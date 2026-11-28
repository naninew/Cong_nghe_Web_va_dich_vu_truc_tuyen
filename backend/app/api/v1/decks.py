"""
Decks API Endpoints.
"""

import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...db.session import get_db
from ...models.user import User
from ...models.deck import Deck, DeckConfig
from ...schemas.deck import (
    DeckTreeResponse,
    DeckCreateRequest,
    DeckUpdateRequest,
    DeckConfigSchema,
    DeckConfigUpdateRequest,
)
from ...services.deck_service import DeckService
from ...core.deps import get_current_user

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=List[DeckTreeResponse])
async def list_user_decks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get hierarchical deck tree with real-time card counts."""
    return await DeckService.get_user_decks_tree(db, user.id)


@router.post("", response_model=DeckTreeResponse)
async def create_deck(
    req: DeckCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new flashcard deck."""
    new_deck = Deck(
        id=int(uuid_int := int(str(uuid.uuid4().int)[:13])),
        user_id=user.id,
        name=req.name,
        description=req.description,
        config_id=req.config_id,
    )
    db.add(new_deck)
    await db.commit()
    await db.refresh(new_deck)

    return DeckTreeResponse(
        id=new_deck.id,
        name=new_deck.name,
        description=new_deck.description or "",
    )


@router.get("/{deck_id}")
async def get_deck_detail(
    deck_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a single deck."""
    stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id)
    res = await db.execute(stmt)
    deck = res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return {
        "id": deck.id,
        "name": deck.name,
        "description": deck.description or "",
        "config_id": deck.config_id,
    }


@router.patch("/{deck_id}")
async def update_deck(
    deck_id: int,
    req: DeckUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update deck name or description."""
    stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id)
    res = await db.execute(stmt)
    deck = res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    if req.name is not None and req.name.strip():
        deck.name = req.name.strip()
    if req.description is not None:
        deck.description = req.description
    if req.config_id is not None:
        deck.config_id = req.config_id

    await db.commit()
    await db.refresh(deck)

    return {
        "id": deck.id,
        "name": deck.name,
        "description": deck.description or "",
        "config_id": deck.config_id,
    }


async def _get_owned_deck(db: AsyncSession, user: User, deck_id: int) -> Deck:
    res = await db.execute(select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id))
    deck = res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


async def _get_deck_config(db: AsyncSession, user: User, deck: Deck):
    if not deck.config_id:
        return None
    cfg = await db.get(DeckConfig, deck.config_id)
    return cfg if cfg and cfg.user_id == user.id else None


@router.get("/{deck_id}/config", response_model=DeckConfigSchema)
async def get_deck_config(
    deck_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scheduling options of a deck (defaults if the deck has no options preset yet)."""
    deck = await _get_owned_deck(db, user, deck_id)
    cfg = await _get_deck_config(db, user, deck)
    if not cfg:
        return DeckConfigSchema()
    return DeckConfigSchema.model_validate(cfg, from_attributes=True)


@router.put("/{deck_id}/config", response_model=DeckConfigSchema)
async def update_deck_config(
    deck_id: int,
    req: DeckConfigUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a deck's scheduling options, e.g. {"fsrs_enabled": true} to switch SM-2 -> FSRS.
    Creates an options preset for the deck on first use.
    """
    deck = await _get_owned_deck(db, user, deck_id)
    cfg = await _get_deck_config(db, user, deck)
    if not cfg:
        defaults = DeckConfigSchema()
        cfg = DeckConfig(
            user_id=user.id,
            **defaults.model_dump(exclude={"id", "name"}),
            name=f"{deck.name} options",
        )
        db.add(cfg)
        await db.flush()
        deck.config_id = cfg.id

    for key, value in req.model_dump(exclude_unset=True).items():
        if value is None and key != "fsrs_params":
            continue
        setattr(cfg, key, value)

    await db.commit()
    await db.refresh(cfg)
    return DeckConfigSchema.model_validate(cfg, from_attributes=True)


@router.delete("/{deck_id}")
async def delete_deck(
    deck_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a deck and all cards inside it."""
    stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id)
    res = await db.execute(stmt)
    deck = res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    await db.delete(deck)
    await db.commit()
    return {"success": True, "message": "Deck deleted successfully"}
