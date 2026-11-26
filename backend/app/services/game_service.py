"""
Quiz Game Engine Service.
Generates 4-option quiz questions, distractor selection, scoring, combo streaks,
and bi-directional SRS synchronization with multiple game modes and question directions.
"""

import re
import uuid
import random
import html as html_lib
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func

from ..models.user import User
from ..models.card import Card, Note
from ..models.notetype import Notetype, NotetypeField
from ..models.game import GameSession, GameSessionAnswer
from ..schemas.study import (
    QuizOption,
    QuizQuestion,
    StartGameRequest,
    StartGameResponse,
    SubmitGameAnswerResponse,
    FinishGameResponse,
)
from .study_service import StudyService
from .deck_service import DeckService
from ..anki_core.models import Rating

# In-memory store for active quiz sessions (session_id -> dict with correct answers & state)
active_quiz_cache: Dict[str, Dict[str, Any]] = {}


def _clean_text(text: Optional[str]) -> str:
    """Strip HTML tags and clean whitespace for clean button labels and prompts."""
    if not text:
        return ""
    # Strip sound tags
    s = re.sub(r"\[sound:.*?\]", "", text)
    # Convert <br>, <p>, <div> to space
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"</?(?:p|div|li)[^>]*>", " ", s, flags=re.IGNORECASE)
    # Strip all remaining html tags
    s = re.sub(r"<[^>]+>", "", s)
    # Unescape HTML entities
    s = html_lib.unescape(s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_card_info(
    card: Card,
    question_field: Optional[str] = None,
    answer_field: Optional[str] = None,
    hint_field: Optional[str] = None,
) -> Dict[str, Any]:
    """Dynamically resolve Question, Answer, Hint and Audio from card note fields."""
    note = card.note
    fields = note.fields if note else []
    fields_by_name: Dict[str, str] = {}
    if note and note.notetype and note.notetype.fields:
        ordered_f = sorted(note.notetype.fields, key=lambda f: f.ord)
        for idx, fld in enumerate(ordered_f):
            val = fields[idx] if idx < len(fields) else ""
            fields_by_name[fld.name] = val
            fields_by_name[fld.name.lower()] = val

    # Search for audio
    audio_file = None
    for fld_val in fields:
        match = re.search(r"\[sound:(.*?)\]", fld_val)
        if match:
            audio_file = match.group(1)
            break

    # Determine Question (Prompt)
    q_val = None
    if question_field and question_field in fields_by_name:
        q_val = fields_by_name[question_field]
    elif question_field and question_field.lower() in fields_by_name:
        q_val = fields_by_name[question_field.lower()]

    if not q_val:
        for alias in ["front", "question", "kanji", "expression", "từ vựng", "word", "vocabulary", "item"]:
            if alias in fields_by_name and fields_by_name[alias]:
                q_val = fields_by_name[alias]
                break
    if not q_val and len(fields) > 0:
        q_val = fields[0]

    # Determine Answer
    a_val = None
    if answer_field and answer_field in fields_by_name:
        a_val = fields_by_name[answer_field]
    elif answer_field and answer_field.lower() in fields_by_name:
        a_val = fields_by_name[answer_field.lower()]

    if not a_val:
        for alias in ["back", "meaning", "answer", "definition", "nghĩa", "ý nghĩa", "translation", "explanation"]:
            if alias in fields_by_name and fields_by_name[alias]:
                a_val = fields_by_name[alias]
                break
    if not a_val and len(fields) > 2 and fields[2]:
        a_val = fields[2]
    elif not a_val and len(fields) > 1 and fields[1]:
        a_val = fields[1]

    # Determine Hint (Example / Reading)
    h_val = None
    if hint_field and hint_field in fields_by_name:
        h_val = fields_by_name[hint_field]
    elif hint_field and hint_field.lower() in fields_by_name:
        h_val = fields_by_name[hint_field.lower()]

    if not h_val:
        for alias in ["hint", "example", "examples", "reading", "furigana", "sentence", "câu ví dụ", "ví dụ", "notes", "gợi ý"]:
            if alias in fields_by_name and fields_by_name[alias]:
                h_val = fields_by_name[alias]
                break
    if not h_val and len(fields) > 1 and fields[1] != a_val and fields[1] != q_val:
        h_val = fields[1]

    return {
        "question": _clean_text(q_val or f"Card {card.id}"),
        "answer": _clean_text(a_val or "Correct"),
        "hint": _clean_text(h_val or ""),
        "audio_file": audio_file,
    }


class GameService:

    @staticmethod
    async def get_available_fields(
        db: AsyncSession,
        user_id: str,
        deck_id: Optional[int] = None,
    ) -> List[str]:
        """Return distinct available note field names for a deck (or all user decks)."""
        if deck_id:
            child_ids = await DeckService.get_deck_and_child_ids(db, user_id, deck_id)
            nt_stmt = (
                select(Note.notetype_id)
                .join(Card, Card.note_id == Note.id)
                .where(Card.user_id == user_id, Card.deck_id.in_(child_ids))
                .distinct()
            )
        else:
            nt_stmt = select(Notetype.id).where(Notetype.user_id == user_id)

        nt_res = await db.execute(nt_stmt)
        notetype_ids = [row[0] for row in nt_res.all()]
        if not notetype_ids:
            return []

        fld_stmt = (
            select(NotetypeField.name)
            .where(NotetypeField.notetype_id.in_(notetype_ids))
            .order_by(NotetypeField.ord.asc(), NotetypeField.id.asc())
        )
        fld_res = await db.execute(fld_stmt)
        seen = set()
        fields: List[str] = []
        for (name,) in fld_res.all():
            if name and name not in seen:
                seen.add(name)
                fields.append(name)
        return fields

    @staticmethod
    async def start_quiz_session(
        db: AsyncSession,
        user_id: str,
        deck_id: Optional[int] = None,
        total_questions: int = 10,
        srs_sync: bool = True,
        mode: str = "classic",
        direction: str = "front_to_back",
        question_field: Optional[str] = None,
        answer_field: Optional[str] = None,
        hint_field: Optional[str] = None,
    ) -> StartGameResponse:
        if direction == "custom":
            selected_custom = [f.strip().lower() for f in [question_field, answer_field, hint_field] if f and f.strip()]
            if not question_field or not answer_field:
                raise ValueError("Vui lòng chọn cả Trường Câu Hỏi và Trường Đáp Án.")
            if len(selected_custom) != len(set(selected_custom)):
                raise ValueError("Các trường Câu Hỏi, Đáp Án và Gợi Ý không được trùng nhau.")

        conditions = [Card.user_id == user_id]

        if deck_id:
            child_ids = await DeckService.get_deck_and_child_ids(db, user_id, deck_id)
            conditions.append(Card.deck_id.in_(child_ids))

        if mode == "lapsed_only":
            conditions.append(Card.lapses > 0)

        # Fetch random candidate cards across the entire deck/scope
        sample_limit = max(200, total_questions * 4)
        stmt = (
            select(Card)
            .options(
                selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
            )
            .where(and_(*conditions))
            .order_by(func.random())
            .limit(sample_limit)
        )
        res = await db.execute(stmt)
        cards = res.scalars().all()

        if len(cards) < 4:
            # Fallback across all user cards if deck or filter is too small
            all_stmt = (
                select(Card)
                .options(
                    selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
                )
                .where(Card.user_id == user_id)
                .order_by(func.random())
                .limit(sample_limit)
            )
            all_res = await db.execute(all_stmt)
            cards = all_res.scalars().all()

        if len(cards) < 4:
            raise ValueError("Need at least 4 cards in your library to generate an interactive 4-option quiz.")

        # Create GameSession record
        session = GameSession(
            user_id=user_id,
            deck_id=deck_id or (cards[0].deck_id if cards else 1),
            game_type=f"quiz-{mode}-{direction}",
            total_questions=min(total_questions, len(cards)),
            created_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()

        # Select random sample of target cards
        chosen_cards = random.sample(cards, min(total_questions, len(cards)))
        questions: List[QuizQuestion] = []
        session_cache: Dict[int, Dict[str, Any]] = {}

        # Pre-extract all card info for distractors
        all_card_info: Dict[int, Dict[str, Any]] = {}
        for c in cards:
            all_card_info[c.id] = _extract_card_info(c, question_field, answer_field, hint_field)

        for card in chosen_cards:
            info = all_card_info[card.id]
            q_text = info["question"]
            a_text = info["answer"]
            h_text = info["hint"]
            audio_f = info["audio_file"]

            if direction == "back_to_front":
                prompt_text = a_text
                correct_answer = q_text
                context_hint = h_text
                # Collect distractors from other questions
                other_candidates = [
                    ci["question"] for cid, ci in all_card_info.items()
                    if cid != card.id and ci["question"] and ci["question"] != correct_answer
                ]
            elif direction == "audio_listening":
                prompt_text = "Listen carefully to the audio"
                correct_answer = a_text
                context_hint = h_text or q_text
                other_candidates = [
                    ci["answer"] for cid, ci in all_card_info.items()
                    if cid != card.id and ci["answer"] and ci["answer"] != correct_answer
                ]
            else:  # front_to_back
                prompt_text = q_text
                correct_answer = a_text
                context_hint = h_text
                other_candidates = [
                    ci["answer"] for cid, ci in all_card_info.items()
                    if cid != card.id and ci["answer"] and ci["answer"] != correct_answer
                ]

            # Deduplicate candidate distractors
            unique_candidates = list(dict.fromkeys(other_candidates))
            while len(unique_candidates) < 3:
                unique_candidates.append(f"Option {len(unique_candidates) + 1}")

            distractors = random.sample(unique_candidates, 3)
            all_opts = [correct_answer] + distractors
            random.shuffle(all_opts)

            keys = ["A", "B", "C", "D"]
            correct_key = "A"
            quiz_options: List[QuizOption] = []
            for idx, opt_text in enumerate(all_opts):
                k = keys[idx]
                if opt_text == correct_answer:
                    correct_key = k
                quiz_options.append(QuizOption(key=k, label=opt_text))

            q_id = str(uuid.uuid4())
            questions.append(
                QuizQuestion(
                    question_id=q_id,
                    card_id=card.id,
                    prompt=prompt_text,
                    context_hint=context_hint,
                    audio_file=audio_f,
                    direction=direction,
                    options=quiz_options,
                )
            )

            session_cache[card.id] = {
                "correct_key": correct_key,
                "prompt": prompt_text,
                "correct_answer": correct_answer,
                "context_hint": context_hint,
                "direction": direction,
                "card_id": card.id,
                "srs_sync": srs_sync,
            }

        # Cache session details for evaluation
        active_quiz_cache[session.id] = {
            "user_id": user_id,
            "srs_sync": srs_sync,
            "mode": mode,
            "cards": session_cache,
            "score": 0,
            "combo": 0,
            "correct_count": 0,
            "total_xp": 0,
            "start_time": datetime.utcnow(),
        }

        return StartGameResponse(
            session_id=session.id,
            deck_id=session.deck_id,
            total_questions=len(questions),
            questions=questions,
        )

    @staticmethod
    async def submit_answer(
        db: AsyncSession,
        user: User,
        session_id: str,
        card_id: int,
        selected_key: str,
        response_time_ms: int = 0,
    ) -> SubmitGameAnswerResponse:
        session_data = active_quiz_cache.get(session_id)
        if not session_data:
            raise ValueError("Quiz session not found or has expired.")

        card_info = session_data["cards"].get(card_id)
        if not card_info:
            raise ValueError(f"Card {card_id} not part of this quiz session.")

        correct_key = card_info["correct_key"]
        is_correct = (selected_key.upper() == correct_key)

        points = 0
        combo_xp = 0
        srs_updated = False
        srs_grade = "None"

        if is_correct:
            session_data["combo"] += 1
            session_data["correct_count"] += 1
            combo = session_data["combo"]

            # Score: base 100 + speed bonus up to 50
            speed_bonus = max(0, int((15000 - response_time_ms) / 300))
            points = 100 + speed_bonus
            combo_xp = min(50, combo * 5)
            session_data["score"] += points
            session_data["total_xp"] += (15 + combo_xp)

            # SRS sync: mark as GOOD
            if session_data["srs_sync"]:
                await StudyService.submit_card_answer(
                    db=db,
                    user=user,
                    card_id=card_id,
                    rating_val=Rating.GOOD.value,
                    time_taken_ms=response_time_ms,
                )
                srs_updated = True
                srs_grade = "Good"

            explanation = f"Correct! {card_info['prompt']} ➔ {card_info['correct_answer']}."
        else:
            session_data["combo"] = 0
            # SRS sync: mark as AGAIN (lapse)
            if session_data["srs_sync"]:
                await StudyService.submit_card_answer(
                    db=db,
                    user=user,
                    card_id=card_id,
                    rating_val=Rating.AGAIN.value,
                    time_taken_ms=response_time_ms,
                )
                srs_updated = True
                srs_grade = "Again"

            explanation = f"Incorrect! The correct answer for '{card_info['prompt']}' is option {correct_key}: {card_info['correct_answer']}."

        # Record answer in DB
        ans_record = GameSessionAnswer(
            session_id=session_id,
            card_id=card_id,
            user_answer=selected_key,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
        )
        db.add(ans_record)
        await db.commit()

        return SubmitGameAnswerResponse(
            is_correct=is_correct,
            correct_key=correct_key,
            points_earned=points,
            combo_xp=combo_xp,
            current_combo=session_data["combo"],
            explanation=explanation,
            srs_updated=srs_updated,
            srs_grade=srs_grade,
        )

    @staticmethod
    async def finish_session(
        db: AsyncSession,
        session_id: str,
    ) -> FinishGameResponse:
        session_data = active_quiz_cache.pop(session_id, None)
        stmt = select(GameSession).where(GameSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalars().first()
        if not session:
            raise ValueError("Session record not found.")

        if session_data:
            duration = int((datetime.utcnow() - session_data["start_time"]).total_seconds())
            session.score = session_data["score"]
            session.xp_earned = session_data["total_xp"]
            session.correct_count = session_data["correct_count"]
            session.duration_seconds = duration
        else:
            duration = session.duration_seconds

        await db.commit()

        total = session.total_questions if session.total_questions > 0 else 1
        accuracy = round((session.correct_count / total) * 100.0, 1)

        return FinishGameResponse(
            session_id=session.id,
            score=session.score,
            xp_earned=session.xp_earned,
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            accuracy_percent=accuracy,
            duration_seconds=duration,
        )
