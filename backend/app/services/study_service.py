"""
Study Session and Card Review Service.
Retrieves queued cards, renders templates, and applies SRS scheduling algorithms.
Implements Anki-compliant Day Rollover (4:00 AM) and Daily Limits (new_per_day, review_per_day).
"""

import os
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_, func

from ..core.config import settings
from ..models.user import User
from ..models.deck import Deck, DeckConfig
from ..models.card import Card, Note, Revlog
from ..models.notetype import Notetype, NotetypeTemplate, NotetypeField
from ..schemas.study import (
    CardDetailResponse,
    CardRenderedView,
    CleanCardView,
    StudyQueueResponse,
    CardAnswerResponse,
)
from ..anki_core import (
    CardState,
    DeckConfigParams,
    Rating,
    get_scheduler,
    TemplateRenderer,
)
from .deck_service import DeckService


# In-memory store for today's custom daily limit bonuses: key = "{user_id}:{day_num}:{deck_id}"
_DAILY_BONUS: Dict[str, int] = {}


class StudyService:

    @staticmethod
    def get_day_timing(now_ts: Optional[int] = None) -> tuple[int, int, datetime]:
        """
        Calculates Anki 4:00 AM Day Rollover.
        Uses UTC+7 offset for local timezone.
        Returns (current_timestamp, day_num, day_start_datetime_utc).
        """
        if now_ts is None:
            now_ts = int(datetime.now(timezone.utc).timestamp())
        tz_offset = 7 * 3600  # UTC+7
        local_now_ts = now_ts + tz_offset
        rollover_offset = 4 * 3600  # 4:00 AM
        day_num = (local_now_ts - rollover_offset) // 86400
        today_start_local_ts = day_num * 86400 + rollover_offset
        today_start_utc_ts = today_start_local_ts - tz_offset
        day_start_dt = datetime.utcfromtimestamp(today_start_utc_ts)
        return now_ts, day_num, day_start_dt

    @staticmethod
    def extract_clean_card_data(
        card: Card,
        note: Note,
        user_id: str,
        media_dir: str,
    ) -> CleanCardView:
        """
        Extracts clean, structured text data from note fields, decoupling presentation
        from arbitrary third-party raw HTML/CSS. Validates media existence on disk.
        """
        fields = note.fields or []
        notetype = note.notetype
        field_names = (
            [f.name for f in sorted(notetype.fields, key=lambda x: x.ord)]
            if notetype and notetype.fields
            else []
        )
        field_map: Dict[str, str] = {}
        for idx, name in enumerate(field_names):
            field_map[name.lower()] = fields[idx] if idx < len(fields) else ""

        def clean_html(text: str) -> str:
            if not text:
                return ""
            # Strip script and style blocks
            text = re.sub(r"<(script|style).*?>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
            # Replace line-breaking HTML with newlines
            text = re.sub(r"<(br|p|div|li)[^>]*>", "\n", text, flags=re.IGNORECASE)
            # Remove remaining tags
            text = re.sub(r"<[^>]+>", "", text)
            # Decode HTML entities
            text = (
                text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
            )
            # Clean excessive blank lines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)

        # 1. Term (Word / Expression / Front)
        term = ""
        for key in ["expression", "kanji", "front", "word", "vocabulary", "term", "từ"]:
            if key in field_map and field_map[key]:
                term = clean_html(field_map[key])
                break
        if not term and fields:
            term = clean_html(fields[0])

        # 2. Phonetic (Reading / Furigana)
        phonetic = ""
        for key in ["reading", "furigana", "phonetic", "hiragana", "katakana", "cách đọc", "phát âm"]:
            if key in field_map and field_map[key]:
                phonetic = clean_html(field_map[key])
                break
        if not phonetic and len(fields) > 1 and len(fields[1]) < 60:
            cand = clean_html(fields[1])
            if cand != term and not any(c in cand for c in [";", "\n"]):
                phonetic = cand

        # 3. Meaning (Vietnamese Definition / Back)
        meaning = ""
        for key in ["meaning", "back", "definition", "vietnamese", "nghĩa", "nghia"]:
            if key in field_map and field_map[key]:
                meaning = clean_html(field_map[key])
                break
        if not meaning and len(fields) > 2:
            meaning = clean_html(fields[2])
        elif not meaning and len(fields) > 1 and fields[1] != phonetic:
            meaning = clean_html(fields[1])

        # 4. Examples
        examples: List[str] = []
        example_raw = ""
        for key in ["example", "examples", "sentence", "sentences", "ví dụ", "vidu"]:
            if key in field_map and field_map[key]:
                example_raw = field_map[key]
                break
        if not example_raw and len(fields) > 4:
            for f in fields[3:]:
                if "•" in f or "<b>" in f or "→" in f or "➜" in f or len(f) > 80:
                    example_raw = f
                    break

        if example_raw:
            parts = re.split(r"(?:•|\n\n|<br\s*/?>\s*<br\s*/?>)", example_raw)
            for part in parts:
                clean_p = clean_html(part)
                if clean_p and len(clean_p) > 2:
                    examples.append(clean_p)

        # 5. Audio URL (Strict physical file existence check on disk)
        audio_url: Optional[str] = None
        all_fields_str = " ".join(fields)
        sound_matches = re.findall(r"\[sound:(.*?)\]", all_fields_str)
        if sound_matches:
            audio_filename = sound_matches[0].strip()
            user_audio = os.path.join(media_dir, user_id, audio_filename)
            global_audio = os.path.join(media_dir, audio_filename)
            if os.path.isfile(user_audio):
                audio_url = f"/media/{user_id}/{audio_filename}"
            elif os.path.isfile(global_audio):
                audio_url = f"/media/{audio_filename}"

        # 6. Image URL (Strict physical file existence check on disk)
        image_url: Optional[str] = None
        img_matches = re.findall(r'<img[^>]+src=["\'](.*?)["\']', all_fields_str)
        if img_matches:
            img_filename = img_matches[0].strip()
            img_basename = os.path.basename(img_filename)
            user_img = os.path.join(media_dir, user_id, img_basename)
            global_img = os.path.join(media_dir, img_basename)
            if os.path.isfile(user_img):
                image_url = f"/media/{user_id}/{img_basename}"
            elif os.path.isfile(global_img):
                image_url = f"/media/{img_basename}"

        # 7. Level Tag
        level_tag = ""
        for key in ["level", "tag", "n", "jlpt"]:
            if key in field_map and field_map[key]:
                level_tag = clean_html(field_map[key])
                break
        if not level_tag and note.tags:
            for t in note.tags:
                if re.match(r"^N[1-5]$", str(t), re.I):
                    level_tag = str(t).upper()
                    break

        return CleanCardView(
            term=term,
            phonetic=phonetic,
            meaning=meaning,
            examples=examples,
            audio_url=audio_url,
            image_url=image_url,
            level_tag=level_tag,
            notes="",
        )

    @staticmethod
    def increase_daily_limit(user_id: str, deck_id: Optional[int], amount: int = 10) -> int:
        """
        Increases today's new card quota by amount (Custom Study bonus).
        """
        _, day_num, _ = StudyService.get_day_timing()
        key = f"{user_id}:{day_num}:{deck_id or 0}"
        curr = _DAILY_BONUS.get(key, 0)
        _DAILY_BONUS[key] = curr + amount
        return _DAILY_BONUS[key]

    @staticmethod
    async def get_next_queued_card(
        db: AsyncSession,
        user_id: str,
        deck_id: Optional[int] = None,
        filter_mode: str = "all",
    ) -> StudyQueueResponse:
        now_ts, today_days, day_start_dt = StudyService.get_day_timing()

        # Build filter conditions
        conditions = [Card.user_id == user_id]
        if deck_id:
            deck_ids = await DeckService.get_deck_and_child_ids(db, user_id, deck_id)
            conditions.append(Card.deck_id.in_(deck_ids))

        # Query Revlog count for cards studied today since 4:00 AM
        revlog_conditions = [
            Revlog.user_id == user_id,
            Revlog.created_at >= day_start_dt,
        ]
        new_done_stmt = select(func.count(Revlog.id)).where(
            and_(*revlog_conditions, Revlog.last_ivl == 0)
        )
        new_done_res = await db.execute(new_done_stmt)
        new_done_today = new_done_res.scalar() or 0

        review_done_stmt = select(func.count(Revlog.id)).where(
            and_(*revlog_conditions, Revlog.last_ivl > 0)
        )
        review_done_res = await db.execute(review_done_stmt)
        review_done_today = review_done_res.scalar() or 0

        # Anki Daily Limits: new_per_day default 20, review_per_day default 200
        new_per_day = 20
        review_per_day = 200

        # Include custom bonus for today
        bonus_key = f"{user_id}:{today_days}:{deck_id or 0}"
        bonus_new = _DAILY_BONUS.get(bonus_key, 0)
        effective_new_limit = new_per_day + bonus_new

        remaining_new_quota = max(0, effective_new_limit - new_done_today)
        remaining_review_quota = max(0, review_per_day - review_done_today)

        # Count available cards in DB
        db_count_stmt = (
            select(
                Card.queue,
                func.count(Card.id).label("cnt"),
            )
            .where(and_(*conditions, Card.queue.in_([0, 1, 2, 3])))
            .group_by(Card.queue)
        )
        db_res = await db.execute(db_count_stmt)
        db_rows = db_res.all()

        db_counts = {"new": 0, "learning": 0, "due": 0}
        for q, cnt in db_rows:
            if q == 0:
                db_counts["new"] = cnt
            elif q in (1, 3):
                db_counts["learning"] += cnt
            elif q == 2:
                db_counts["due"] += cnt

        # Review cards actually due today (queue=2, due <= today_days)
        due_review_stmt = select(func.count(Card.id)).where(
            and_(*conditions, Card.queue == 2, Card.due <= today_days)
        )
        due_review_res = await db.execute(due_review_stmt)
        actual_due_today = due_review_res.scalar() or 0

        # Calculate user-facing remaining counters
        user_counts = {
            "new": min(db_counts["new"], remaining_new_quota),
            "learning": db_counts["learning"],
            "due": min(actual_due_today, remaining_review_quota),
        }

        # Gather card with Anki priority:
        # 1. Intraday Learning cards (queue in (1, 3), due <= now_ts)
        # 2. Review cards due today (queue == 2, due <= today_days) up to remaining_review_quota
        # 3. New cards (queue == 0) up to remaining_new_quota
        card = None

        if filter_mode == "lapsed_only":
            lapsed_stmt = (
                select(Card)
                .options(
                    selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.templates),
                    selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
                    selectinload(Card.deck),
                )
                .where(and_(*conditions, Card.lapses > 0))
                .order_by(Card.lapses.desc(), Card.due)
                .limit(1)
            )
            res = await db.execute(lapsed_stmt)
            card = res.scalars().first()
        else:
            # Step 1: Learning cards due right now
            learn_stmt = (
                select(Card)
                .options(
                    selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.templates),
                    selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
                    selectinload(Card.deck),
                )
                .where(and_(*conditions, Card.queue.in_([1, 3]), Card.due <= now_ts))
                .order_by(Card.due)
                .limit(1)
            )
            res = await db.execute(learn_stmt)
            card = res.scalars().first()

            # Step 2: Review cards due today (if review quota remains)
            if not card and filter_mode in ("all", "due_only") and remaining_review_quota > 0:
                review_stmt = (
                    select(Card)
                    .options(
                        selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.templates),
                        selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
                        selectinload(Card.deck),
                    )
                    .where(and_(*conditions, Card.queue == 2, Card.due <= today_days))
                    .order_by(Card.due)
                    .limit(1)
                )
                res = await db.execute(review_stmt)
                card = res.scalars().first()

            # Step 3: New cards (if new quota remains)
            if not card and filter_mode in ("all", "new_only") and remaining_new_quota > 0:
                new_stmt = (
                    select(Card)
                    .options(
                        selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.templates),
                        selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
                        selectinload(Card.deck),
                    )
                    .where(and_(*conditions, Card.queue == 0))
                    .order_by(Card.id)
                    .limit(1)
                )
                res = await db.execute(new_stmt)
                card = res.scalars().first()

        if not card:
            return StudyQueueResponse(card=None, remaining_counts=user_counts)

        # Render card using TemplateRenderer
        note = card.note
        notetype = note.notetype
        template = None
        for tmpl in notetype.templates:
            if tmpl.ord == card.ord:
                template = tmpl
                break
        if not template and notetype.templates:
            template = notetype.templates[0]

        # Field names mapping
        fields_dict: Dict[str, str] = {}
        ordered_fields = sorted(notetype.fields, key=lambda f: f.ord)
        for idx, fld in enumerate(ordered_fields):
            val = note.fields[idx] if idx < len(note.fields) else ""
            fields_dict[fld.name] = val

        renderer = TemplateRenderer(media_base_url=f"/media/{user_id}")
        rendered_dict = renderer.render_card(
            qfmt=template.qfmt if template else "{{Front}}",
            afmt=template.afmt if template else "{{Back}}",
            fields=fields_dict,
            css=notetype.css or "",
            card_ord=card.ord,
        )

        # Extract clean structured card data
        clean_data = StudyService.extract_clean_card_data(
            card=card,
            note=note,
            user_id=user_id,
            media_dir=settings.MEDIA_DIR,
        )

        # Scheduler preview intervals
        cfg_params = DeckConfigParams()
        sched = get_scheduler(cfg_params)
        card_state = CardState(
            card_id=card.id,
            card_type=card.type,
            queue=card.queue,
            due=card.due,
            interval=card.ivl,
            factor=card.factor,
            reps=card.reps,
            lapses=card.lapses,
            fsrs_stability=card.fsrs_stability,
            fsrs_difficulty=card.fsrs_difficulty,
        )
        intervals = sched.describe_next_intervals(card_state, now_ts, today_days)

        card_detail = CardDetailResponse(
            id=card.id,
            deck_id=card.deck_id,
            deck_name=card.deck.name if card.deck else "Default",
            note_id=card.note_id,
            ord=card.ord,
            type=card.type,
            queue=card.queue,
            due=card.due,
            ivl=card.ivl,
            factor=card.factor,
            reps=card.reps,
            lapses=card.lapses,
            fields=fields_dict,
            tags=note.tags if note.tags else [],
            rendered=CardRenderedView(
                front_html=rendered_dict["front_html"],
                back_html=rendered_dict["back_html"],
                css=rendered_dict["css"],
            ),
            clean_data=clean_data,
            next_intervals=intervals,
        )

        return StudyQueueResponse(
            card=card_detail,
            remaining_counts=user_counts,
        )

    @staticmethod
    async def submit_card_answer(
        db: AsyncSession,
        user: User,
        card_id: int,
        rating_val: int,
        time_taken_ms: int = 0,
    ) -> CardAnswerResponse:
        stmt = select(Card).where(Card.id == card_id, Card.user_id == user.id)
        res = await db.execute(stmt)
        card = res.scalars().first()
        if not card:
            raise ValueError(f"Card {card_id} not found.")

        now_ts, today_days, _ = StudyService.get_day_timing()

        # Load deck config params
        cfg_params = DeckConfigParams()
        sched = get_scheduler(cfg_params)

        card_state = CardState(
            card_id=card.id,
            card_type=card.type,
            queue=card.queue,
            due=card.due,
            interval=card.ivl,
            factor=card.factor,
            reps=card.reps,
            lapses=card.lapses,
            left=card.left,
            fsrs_stability=card.fsrs_stability,
            fsrs_difficulty=card.fsrs_difficulty,
        )

        schedule_res = sched.schedule(
            card=card_state,
            rating=Rating(rating_val),
            now_ts=now_ts,
            today_day=today_days,
            time_taken_ms=time_taken_ms,
        )

        # Update card in database
        card.type = schedule_res.card_type
        card.queue = schedule_res.queue
        card.due = schedule_res.due
        card.ivl = schedule_res.interval
        card.factor = schedule_res.factor
        card.reps = schedule_res.reps
        card.lapses = schedule_res.lapses
        card.left = schedule_res.left
        card.fsrs_stability = schedule_res.fsrs_stability
        card.fsrs_difficulty = schedule_res.fsrs_difficulty

        # Insert Revlog
        revlog = Revlog(
            user_id=user.id,
            card_id=card.id,
            rating=rating_val,
            new_ivl=schedule_res.interval,
            last_ivl=card_state.interval,
            factor=schedule_res.factor,
            time_taken_ms=time_taken_ms,
            review_type=schedule_res.review_type,
            created_at=datetime.utcnow(),
        )
        db.add(revlog)

        # Update User XP and Streak
        xp_gain = 15 if rating_val > 1 else 5
        user.xp += xp_gain
        today_date = date.today()
        if user.last_study_date != today_date:
            if user.last_study_date == today_date - timedelta(days=1):
                user.streak_days += 1
            else:
                user.streak_days = 1
            user.last_study_date = today_date

        await db.commit()

        return CardAnswerResponse(
            card_id=card.id,
            rating=rating_val,
            new_interval=card.ivl,
            due=card.due,
            xp_awarded=xp_gain,
            streak_days=user.streak_days,
        )
