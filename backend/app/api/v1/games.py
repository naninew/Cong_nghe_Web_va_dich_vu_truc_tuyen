"""
Quiz Game Endpoints: Start quiz session, submit answer, finish session.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.user import User
from ...schemas.study import (
    StartGameRequest,
    StartGameResponse,
    SubmitGameAnswerRequest,
    SubmitGameAnswerResponse,
    FinishGameRequest,
    FinishGameResponse,
)
from ...services.game_service import GameService
from ...core.deps import get_current_user

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/fields", response_model=List[str])
async def get_deck_fields(
    deck_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return distinct available note field names for a deck (or all user decks)."""
    return await GameService.get_available_fields(db=db, user_id=user.id, deck_id=deck_id)


@router.post("/start", response_model=StartGameResponse)
async def start_quiz_session(
    req: StartGameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate interactive 4-option quiz from deck cards.
    Dynamically picks plausible distractors from the same deck & category.
    """
    try:
        return await GameService.start_quiz_session(
            db=db,
            user_id=user.id,
            deck_id=req.deck_id,
            total_questions=req.total_questions,
            srs_sync=req.srs_sync,
            mode=req.mode,
            direction=req.direction,
            question_field=req.question_field,
            answer_field=req.answer_field,
            hint_field=req.hint_field,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/answer", response_model=SubmitGameAnswerResponse)
async def submit_quiz_answer(
    req: SubmitGameAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit answer for a quiz question.
    Calculates score, combo multiplier, and syncs SRS rating automatically:
    - Correct -> Card marked remembered (Good rating).
    - Incorrect -> Card marked forgotten (Again rating, lapse incremented).
    """
    try:
        return await GameService.submit_answer(
            db=db,
            user=user,
            session_id=req.session_id,
            card_id=req.card_id,
            selected_key=req.selected_key,
            response_time_ms=req.response_time_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/finish", response_model=FinishGameResponse)
async def finish_quiz_session(
    req: FinishGameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize quiz game session and compute accuracy score and XP."""
    try:
        return await GameService.finish_session(db, req.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
