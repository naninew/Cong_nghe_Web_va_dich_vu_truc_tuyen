"""
Analytics and Statistics Endpoints.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timezone, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_, case

from ...db.session import get_db
from ...models.user import User
from ...models.deck import Deck
from ...models.card import Card, Note, Revlog
from ...core.deps import get_current_user
from ...services.deck_service import DeckService
from ...services.study_service import StudyService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def get_overview_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve bento dashboard statistics: streak, XP, cards mastered, retention rate."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    today_days = now_ts // 86400

    # 1. Card counts
    stmt = (
        select(Card.queue, func.count(Card.id))
        .where(Card.user_id == user.id)
        .group_by(Card.queue)
    )
    res = await db.execute(stmt)
    rows = res.all()

    new_count = 0
    learn_count = 0
    mature_count = 0
    total_cards = 0

    for queue, cnt in rows:
        total_cards += cnt
        if queue == 0:
            new_count += cnt
        elif queue in (1, 3):
            learn_count += cnt
        elif queue == 2:
            mature_count += cnt

    # 2. Retention rate from revlogs (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    rev_stmt = (
        select(Revlog.rating, func.count(Revlog.id))
        .where(Revlog.user_id == user.id, Revlog.created_at >= thirty_days_ago)
        .group_by(Revlog.rating)
    )
    rev_res = await db.execute(rev_stmt)
    rev_rows = rev_res.all()

    total_reviews = sum(cnt for _, cnt in rev_rows)
    success_reviews = sum(cnt for rating, cnt in rev_rows if rating > 1)
    retention_rate = round((success_reviews / total_reviews * 100.0), 1) if total_reviews > 0 else None

    # 2b. Reviews completed today (aligned with Anki 4:00 AM rollover)
    _, _, day_start_dt = StudyService.get_day_timing()
    today_rev_stmt = (
        select(func.count(Revlog.id))
        .where(Revlog.user_id == user.id, Revlog.created_at >= day_start_dt)
    )
    today_rev_res = await db.execute(today_rev_stmt)
    reviews_today = today_rev_res.scalar() or 0

    # 2c. Effective streak (reset to 0 if user missed yesterday and today)
    today_date = date.today()
    effective_streak = user.streak_days
    if not user.last_study_date or user.last_study_date < today_date - timedelta(days=1):
        effective_streak = 0
        if user.streak_days != 0:
            user.streak_days = 0
            await db.commit()

    # 3. Due today
    due_stmt = (
        select(func.count(Card.id))
        .where(Card.user_id == user.id, Card.queue == 2, Card.due <= today_days)
    )
    due_res = await db.execute(due_stmt)
    due_today = due_res.scalar() or 0

    daily_target = user.daily_goal or 50

    return {
        "user": {
            "name": user.display_name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "streak_days": effective_streak,
            "xp": user.xp,
        },
        "daily_goal": {
            "completed": reviews_today,
            "target": daily_target,
        },
        "due_count": due_today + learn_count,
        "total_cards": total_cards,
        "mature_cards": mature_count,
        "learning_cards": learn_count,
        "new_cards": new_count,
        "retention_rate": retention_rate,
    }


def _clean_plain_text(html: Optional[str]) -> str:
    if not html:
        return ""
    s = re.sub(r"\[sound:.*?\]", "", html)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


@router.get("/deck/{deck_id}")
async def get_deck_stats(
    deck_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Comprehensive Deck Statistics (Hizashi Dashboard equivalent):
    - 4 Metric cards: Total cards, study progress %, retention %, review count & avg.
    - Status distribution: New, Learning, Review, Relearning (lapses), Leeches, Starred.
    - Learned cards matrix: 5 memory tiers (Mới nhớ, Đang nhớ, Khá vững, Vững, Nhớ lâu).
    """
    # 1. Fetch deck
    deck_stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id)
    deck_res = await db.execute(deck_stmt)
    deck = deck_res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    child_ids = await DeckService.get_deck_and_child_ids(db, user.id, deck_id)

    # 2. Aggregate card counts & stability tiers directly in SQL (fast even for 50,000+ cards)
    base_filter = and_(Card.user_id == user.id, Card.deck_id.in_(child_ids))
    is_studied = or_(Card.reps > 0, Card.queue.in_([1, 2, 3]))
    ivl_col = func.coalesce(Card.ivl, 0)

    agg_stmt = select(
        func.count(Card.id).label("total_cards"),
        func.sum(case((Card.queue == 0, 1), else_=0)).label("new_count"),
        func.sum(case((Card.queue.in_([1, 3]), 1), else_=0)).label("learning_count"),
        func.sum(case((Card.queue == 2, 1), else_=0)).label("review_count"),
        func.sum(case((and_(Card.queue.in_([1, 3]), Card.lapses > 0), 1), else_=0)).label("relearning_count"),
        func.sum(case((Card.lapses >= 4, 1), else_=0)).label("leech_count"),
        func.sum(case((func.coalesce(Card.flags, 0) > 0, 1), else_=0)).label("starred_count"),
        func.sum(case((is_studied, 1), else_=0)).label("studied_count"),
        func.sum(case((and_(is_studied, ivl_col < 1), 1), else_=0)).label("tier1"),
        func.sum(case((and_(is_studied, ivl_col >= 1, ivl_col <= 7), 1), else_=0)).label("tier2"),
        func.sum(case((and_(is_studied, ivl_col > 7, ivl_col <= 21), 1), else_=0)).label("tier3"),
        func.sum(case((and_(is_studied, ivl_col > 21, ivl_col <= 60), 1), else_=0)).label("tier4"),
        func.sum(case((and_(is_studied, ivl_col > 60), 1), else_=0)).label("tier5"),
    ).where(base_filter)

    agg_row = (await db.execute(agg_stmt)).one()

    total_cards = int(agg_row.total_cards or 0)
    new_count = int(agg_row.new_count or 0)
    learning_count = int(agg_row.learning_count or 0)
    review_count = int(agg_row.review_count or 0)
    relearning_count = int(agg_row.relearning_count or 0)
    leech_count = int(agg_row.leech_count or 0)
    starred_count = int(agg_row.starred_count or 0)
    studied_count = int(agg_row.studied_count or 0)

    tier_counts = {
        "tier1": int(agg_row.tier1 or 0),  # Mới nhớ (< 1d)
        "tier2": int(agg_row.tier2 or 0),  # Đang nhớ (1 - 7d)
        "tier3": int(agg_row.tier3 or 0),  # Khá vững (7 - 21d)
        "tier4": int(agg_row.tier4 or 0),  # Vững (21 - 60d)
        "tier5": int(agg_row.tier5 or 0),  # Nhớ lâu (> 60d)
    }

    # 3. Fetch only up to 400 studied cards (with notes) for the learned matrix grid
    learned_matrix = []
    if studied_count > 0:
        learned_stmt = (
            select(Card)
            .options(selectinload(Card.note))
            .where(and_(base_filter, is_studied))
            .limit(400)
        )
        learned_cards = (await db.execute(learned_stmt)).scalars().all()
        for c in learned_cards:
            ivl = c.ivl or 0
            if ivl < 1:
                tier = 1
            elif ivl <= 7:
                tier = 2
            elif ivl <= 21:
                tier = 3
            elif ivl <= 60:
                tier = 4
            else:
                tier = 5

            note_field0 = (
                c.note.fields[0]
                if (c.note and c.note.fields and len(c.note.fields) > 0)
                else f"Card {c.id}"
            )
            learned_matrix.append({
                "card_id": c.id,
                "front_text": _clean_plain_text(note_field0),
                "ivl": c.ivl,
                "reps": c.reps,
                "lapses": c.lapses,
                "tier": tier,
            })

    progress_percent = round((studied_count / max(1, total_cards)) * 100, 1)

    # 4. Review telemetry from Revlog via JOIN (avoids SQL IN(...) variable limit)
    total_reviews = 0
    success_reviews = 0
    if child_ids:
        rev_stmt = (
            select(Revlog.rating, func.count(Revlog.id))
            .join(Card, Revlog.card_id == Card.id)
            .where(
                Revlog.user_id == user.id,
                Card.user_id == user.id,
                Card.deck_id.in_(child_ids),
            )
            .group_by(Revlog.rating)
        )
        rev_res = await db.execute(rev_stmt)
        rev_rows = rev_res.all()
        total_reviews = sum(cnt for _, cnt in rev_rows)
        success_reviews = sum(cnt for rating, cnt in rev_rows if rating > 1)

    fail_reviews = total_reviews - success_reviews
    retention_rate = round((success_reviews / max(1, total_reviews)) * 100, 1) if total_reviews > 0 else 0.0
    avg_reviews = round(total_reviews / max(1, total_cards), 1)

    return {
        "deck": {
            "id": deck.id,
            "name": deck.name,
            "description": deck.description or "",
        },
        "overview": {
            "total_cards": total_cards,
            "studied_cards": studied_count,
            "progress_percent": progress_percent,
            "retention_rate": retention_rate,
            "success_reviews": success_reviews,
            "fail_reviews": fail_reviews,
            "total_reviews": total_reviews,
            "avg_reviews_per_card": avg_reviews,
        },
        "distribution": {
            "new": new_count,
            "learning": learning_count,
            "review": review_count,
            "relearning": relearning_count,
            "leeches": leech_count,
            "starred": starred_count,
        },
        "learned": {
            "total_learned": studied_count,
            "total_cards": total_cards,
            "tier_counts": tier_counts,
            "cards": learned_matrix,
        },
    }
