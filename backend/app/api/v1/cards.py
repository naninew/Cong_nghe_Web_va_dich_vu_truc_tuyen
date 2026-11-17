"""
Cards and Browser API Endpoints.
Provides card browsing, search across note fields, lapsed card tracking, note editing, and SRS reset.
"""

from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, or_, and_

from ...db.session import get_db
from ...models.user import User
from ...models.deck import Deck
from ...models.card import Card, Note, Revlog
from ...models.notetype import Notetype, NotetypeField, NotetypeTemplate
from ...core.deps import get_current_user
from ...services.deck_service import DeckService
from ...anki_core.template.renderer import TemplateRenderer

router = APIRouter(prefix="/cards", tags=["cards"])


class CardBrowseItem(BaseModel):
    id: int
    deck_id: int
    deck_name: str
    note_id: int
    ord: int
    type: int
    queue: int
    state_label: str
    due: int
    ivl: int
    factor: int
    reps: int
    lapses: int
    fields: Dict[str, str]
    tags: List[str]


class CardBrowseResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CardBrowseItem]


class CardUpdateRequest(BaseModel):
    fields: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    is_suspended: Optional[bool] = None


class CardCreateRequest(BaseModel):
    deck_id: int
    notetype_id: int
    fields: Dict[str, str]
    tags: Optional[List[str]] = []


@router.get("/browse", response_model=CardBrowseResponse)
async def browse_cards(
    deck_id: Optional[int] = Query(None),
    state: str = Query("all", pattern="^(all|lapsed|due|learning|new|suspended)$"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search and filter user cards with pagination.
    Supports filtering by deck (including all subdecks), card state (lapsed, due, new, etc.), and keyword search.
    """
    now_ts = int(datetime.now(timezone.utc).timestamp())
    today_days = now_ts // 86400

    conditions = [Card.user_id == user.id]

    if deck_id:
        child_ids = await DeckService.get_deck_and_child_ids(db, user.id, deck_id)
        conditions.append(Card.deck_id.in_(child_ids))

    if state == "lapsed":
        conditions.append(Card.lapses > 0)
    elif state == "due":
        conditions.append(or_(
            and_(Card.queue.in_([1, 3]), Card.due <= now_ts),
            and_(Card.queue == 2, Card.due <= today_days),
        ))
    elif state == "learning":
        conditions.append(Card.queue.in_([1, 3]))
    elif state == "new":
        conditions.append(Card.queue == 0)
    elif state == "suspended":
        conditions.append(Card.queue == -1)

    # Note text search filter
    note_join_needed = False
    if search and search.strip():
        note_join_needed = True
        pattern = f"%{search.strip()}%"
        # Search in note fields or tags
        # Note.fields is a JSON list of strings; in postgres can be cast to text
        conditions.append(Note.fields.cast(db.bind.dialect.name == "postgresql" and func.text or str).ilike(pattern))

    # Total count query
    count_stmt = select(func.count(Card.id)).where(and_(*conditions))
    if note_join_needed:
        count_stmt = count_stmt.join(Card.note)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paged query
    stmt = (
        select(Card)
        .options(
            selectinload(Card.deck),
            selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
        )
        .where(and_(*conditions))
    )
    if note_join_needed:
        stmt = stmt.join(Card.note)

    # Order by lapses descending if lapsed, else id
    if state == "lapsed":
        stmt = stmt.order_by(Card.lapses.desc(), Card.id)
    else:
        stmt = stmt.order_by(Card.id)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    cards_res = await db.execute(stmt)
    cards = cards_res.scalars().all()

    items: List[CardBrowseItem] = []
    for c in cards:
        note = c.note
        notetype = note.notetype if note else None

        fields_dict: Dict[str, str] = {}
        if notetype and notetype.fields:
            ordered_f = sorted(notetype.fields, key=lambda f: f.ord)
            for idx, fld in enumerate(ordered_f):
                val = note.fields[idx] if note and idx < len(note.fields) else ""
                fields_dict[fld.name] = val
        elif note and note.fields:
            for idx, val in enumerate(note.fields):
                fields_dict[f"Field_{idx}"] = val

        # State label
        if c.queue == -1:
            state_lbl = "Suspended"
        elif c.queue == 0:
            state_lbl = "New"
        elif c.queue in (1, 3):
            state_lbl = "Learning"
        elif c.queue == 2:
            state_lbl = "Due" if c.due <= today_days else "Review"
        else:
            state_lbl = "Buried"

        items.append(
            CardBrowseItem(
                id=c.id,
                deck_id=c.deck_id,
                deck_name=c.deck.name if c.deck else "Default",
                note_id=c.note_id,
                ord=c.ord,
                type=c.type,
                queue=c.queue,
                state_label=state_lbl,
                due=c.due,
                ivl=c.ivl,
                factor=c.factor,
                reps=c.reps,
                lapses=c.lapses,
                fields=fields_dict,
                tags=note.tags if note and note.tags else [],
            )
        )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return CardBrowseResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get("/{card_id}")
async def get_card_detail(
    card_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete card details, rendered HTML preview, and review logs."""
    stmt = (
        select(Card)
        .options(
            selectinload(Card.deck),
            selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
            selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.templates),
            selectinload(Card.revlogs),
        )
        .where(Card.id == card_id, Card.user_id == user.id)
    )
    res = await db.execute(stmt)
    card = res.scalars().first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    note = card.note
    notetype = note.notetype

    fields_dict: Dict[str, str] = {}
    ordered_f = sorted(notetype.fields, key=lambda f: f.ord) if notetype else []
    for idx, fld in enumerate(ordered_f):
        val = note.fields[idx] if idx < len(note.fields) else ""
        fields_dict[fld.name] = val

    template = notetype.templates[card.ord] if notetype and card.ord < len(notetype.templates) else (notetype.templates[0] if notetype and notetype.templates else None)
    renderer = TemplateRenderer(media_base_url=f"/media/{user.id}")
    rendered = renderer.render_card(
        qfmt=template.qfmt if template else "{{Front}}",
        afmt=template.afmt if template else "{{Back}}",
        fields=fields_dict,
        css=notetype.css if notetype else "",
        card_ord=card.ord,
    )

    recent_logs = [
        {
            "id": log.id,
            "rating": log.rating,
            "new_ivl": log.new_ivl,
            "last_ivl": log.last_ivl,
            "review_type": log.review_type,
            "time_taken_ms": log.time_taken_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in sorted(card.revlogs, key=lambda l: l.id, reverse=True)[:10]
    ]

    return {
        "id": card.id,
        "deck_id": card.deck_id,
        "deck_name": card.deck.name if card.deck else "Default",
        "note_id": card.note_id,
        "ord": card.ord,
        "type": card.type,
        "queue": card.queue,
        "due": card.due,
        "ivl": card.ivl,
        "factor": card.factor,
        "reps": card.reps,
        "lapses": card.lapses,
        "fields": fields_dict,
        "tags": note.tags if note and note.tags else [],
        "rendered": rendered,
        "revlogs": recent_logs,
    }


@router.patch("/{card_id}")
async def update_card(
    card_id: int,
    req: CardUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit note fields, tags, or suspend/unsuspend card."""
    stmt = (
        select(Card)
        .options(
            selectinload(Card.note).selectinload(Note.notetype).selectinload(Notetype.fields),
        )
        .where(Card.id == card_id, Card.user_id == user.id)
    )
    res = await db.execute(stmt)
    card = res.scalars().first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    note = card.note
    if req.fields and note:
        ordered_f = sorted(note.notetype.fields, key=lambda f: f.ord)
        current_fields = list(note.fields)
        while len(current_fields) < len(ordered_f):
            current_fields.append("")
        for idx, fld in enumerate(ordered_f):
            if fld.name in req.fields:
                current_fields[idx] = req.fields[fld.name]
        note.fields = current_fields

    if req.tags is not None and note:
        note.tags = req.tags

    if req.is_suspended is not None:
        if req.is_suspended:
            card.queue = -1
        else:
            card.queue = 0 if card.type == 0 else (2 if card.type == 2 else 1)

    await db.commit()
    return {"success": True, "message": "Card updated successfully"}


@router.post("/{card_id}/reset")
async def reset_card_progress(
    card_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset card SRS memory state back to a brand new card."""
    stmt = select(Card).where(Card.id == card_id, Card.user_id == user.id)
    res = await db.execute(stmt)
    card = res.scalars().first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.type = 0
    card.queue = 0
    card.due = 0
    card.ivl = 0
    card.factor = 2500
    card.reps = 0
    card.lapses = 0
    card.left = 0
    card.fsrs_stability = None
    card.fsrs_difficulty = None

    await db.commit()
    return {"success": True, "message": "Card progress reset to New successfully"}


@router.get("/notetypes/list")
async def list_notetypes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve available notetypes and their field definitions for the current user."""
    stmt = (
        select(Notetype)
        .options(
            selectinload(Notetype.fields),
            selectinload(Notetype.templates),
        )
        .where(Notetype.user_id == user.id)
    )
    res = await db.execute(stmt)
    notetypes = res.scalars().all()

    return [
        {
            "id": nt.id,
            "name": nt.name,
            "fields": [
                {"id": f.id, "name": f.name, "ord": f.ord}
                for f in sorted(nt.fields, key=lambda f: f.ord)
            ],
            "templates": [
                {"id": t.id, "name": t.name, "ord": t.ord}
                for t in sorted(nt.templates, key=lambda t: t.ord)
            ],
        }
        for nt in notetypes
    ]


@router.post("")
async def create_card_and_note(
    req: CardCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new note with cards across all its templates in the specified deck."""
    # 1. Verify deck belongs to user
    d_stmt = select(Deck).where(Deck.id == req.deck_id, Deck.user_id == user.id)
    d_res = await db.execute(d_stmt)
    deck = d_res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # 2. Verify notetype belongs to user
    nt_stmt = (
        select(Notetype)
        .options(
            selectinload(Notetype.fields),
            selectinload(Notetype.templates),
        )
        .where(Notetype.id == req.notetype_id, Notetype.user_id == user.id)
    )
    nt_res = await db.execute(nt_stmt)
    notetype = nt_res.scalars().first()
    if notetype is None:
        raise HTTPException(status_code=404, detail="Notetype not found")

    # 3. Build ordered fields array
    ordered_f = sorted(notetype.fields, key=lambda f: f.ord)
    note_fields_arr = []
    for f in ordered_f:
        val = req.fields.get(f.name, "")
        note_fields_arr.append(val)

    note_id = int(str(uuid.uuid4().int)[:13])
    note = Note(
        id=note_id,
        user_id=user.id,
        notetype_id=notetype.id,
        guid=str(uuid.uuid4()),
        fields=note_fields_arr,
        tags=req.tags or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(note)

    # 4. Create a Card for each template
    created_cards = []
    for tmpl in notetype.templates:
        card_id = int(str(uuid.uuid4().int)[:13])
        card = Card(
            id=card_id,
            user_id=user.id,
            note_id=note.id,
            deck_id=deck.id,
            ord=tmpl.ord,
            type=0,  # New
            queue=0, # New
            due=0,
            ivl=0,
            factor=2500,
            reps=0,
            lapses=0,
            left=0,
        )
        db.add(card)
        created_cards.append(card_id)

    await db.commit()
    return {
        "success": True,
        "note_id": note_id,
        "created_cards": created_cards,
        "message": f"Successfully created note with {len(created_cards)} cards",
    }


@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a card and delete the parent note if no other cards remain."""
    stmt = (
        select(Card)
        .options(selectinload(Card.note).selectinload(Note.cards))
        .where(Card.id == card_id, Card.user_id == user.id)
    )
    res = await db.execute(stmt)
    card = res.scalars().first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    parent_note = card.note
    await db.delete(card)

    if parent_note and len(parent_note.cards) <= 1:
        await db.delete(parent_note)

    await db.commit()
    return {"success": True, "message": "Card deleted successfully"}
