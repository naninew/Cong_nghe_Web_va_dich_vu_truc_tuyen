"""
Analytics and Statistics Endpoints.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_

from ...db.session import get_db
from ...models.user import User
from ...models.deck import Deck
from ...models.card import Card, Note, Revlog
from ...core.deps import get_current_user
from ...services.deck_service import DeckService

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
    retention_rate = round((success_reviews / total_reviews * 100.0), 1) if total_reviews > 0 else 92.4

    # 3. Due today
    due_stmt = (
        select(func.count(Card.id))
        .where(Card.user_id == user.id, Card.queue == 2, Card.due <= today_days)
    )
    due_res = await db.execute(due_stmt)
    due_today = due_res.scalar() or 0

    return {
        "user": {
            "name": user.display_name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "streak_days": user.streak_days,
            "xp": user.xp,
        },
        "daily_goal": {
            "completed": min(total_reviews, 50),
            "target": 50,
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

    # 2. Query all cards in deck + subdecks
    cards_stmt = (
        select(Card)
        .options(
            selectinload(Card.note),
        )
        .where(Card.user_id == user.id, Card.deck_id.in_(child_ids))
    )
    cards_res = await db.execute(cards_stmt)
    cards = cards_res.scalars().all()
    total_cards = len(cards)

    # 3. Status breakdown & progress
    new_count = 0
    learning_count = 0
    review_count = 0
    relearning_count = 0
    leech_count = 0
    starred_count = 0
    studied_count = 0

    tier_counts = {
        "tier1": 0,  # Mới nhớ (< 1d)
        "tier2": 0,  # Đang nhớ (1 - 7d)
        "tier3": 0,  # Khá vững (7 - 21d)
        "tier4": 0,  # Vững (21 - 60d)
        "tier5": 0,  # Nhớ lâu (> 60d)
    }
    learned_matrix = []

    for c in cards:
        c_flags = getattr(c, "flags", 0) or 0
        if c_flags > 0:
            starred_count += 1
        elif c.note and c.note.tags and any("marked" in str(t).lower() or "star" in str(t).lower() for t in c.note.tags):
            starred_count += 1
        if c.lapses >= 4:
            leech_count += 1

        if c.queue == 0:
            new_count += 1
        elif c.queue in (1, 3):
            learning_count += 1
            if c.lapses > 0:
                relearning_count += 1
        elif c.queue == 2:
            review_count += 1

        if c.reps > 0 or c.queue in (1, 2, 3):
            studied_count += 1
            # Determine memory stability tier
            ivl = c.ivl or 0
            if ivl < 1:
                tier = 1
                tier_counts["tier1"] += 1
            elif ivl <= 7:
                tier = 2
                tier_counts["tier2"] += 1
            elif ivl <= 21:
                tier = 3
                tier_counts["tier3"] += 1
            elif ivl <= 60:
                tier = 4
                tier_counts["tier4"] += 1
            else:
                tier = 5
                tier_counts["tier5"] += 1

            if len(learned_matrix) < 400:
                note_field0 = c.note.fields[0] if (c.note and c.note.fields and len(c.note.fields) > 0) else f"Card {c.id}"
                learned_matrix.append({
                    "card_id": c.id,
                    "front_text": _clean_plain_text(note_field0),
                    "ivl": c.ivl,
                    "reps": c.reps,
                    "lapses": c.lapses,
                    "tier": tier,
                })

    progress_percent = round((studied_count / max(1, total_cards)) * 100, 1)

    # 4. Review telemetry from Revlog for this deck's cards
    card_id_list = [c.id for c in cards]
    total_reviews = 0
    success_reviews = 0
    if card_id_list:
        rev_stmt = (
            select(Revlog.rating, func.count(Revlog.id))
            .where(Revlog.user_id == user.id, Revlog.card_id.in_(card_id_list))
            .group_by(Revlog.rating)
        )
        rev_res = await db.execute(rev_stmt)
        rev_rows = rev_res.all()
        total_reviews = sum(cnt for _, cnt in rev_rows)
        success_reviews = sum(cnt for rating, cnt in rev_rows if rating > 1)

    fail_reviews = total_reviews - success_reviews
    retention_rate = round((success_reviews / max(1, total_reviews)) * 100, 1) if total_reviews > 0 else 92.4
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
