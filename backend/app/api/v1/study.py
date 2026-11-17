"""
Study Endpoints: Queued card retrieval and SRS rating submission.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.user import User
from ...schemas.study import (
    StudyQueueResponse,
    CardAnswerRequest,
    CardAnswerResponse,
    CustomIncreaseRequest,
    CustomIncreaseResponse,
)
from ...services.study_service import StudyService
from ...core.deps import get_current_user

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/queue", response_model=StudyQueueResponse)
async def get_study_card(
    deck_id: Optional[int] = None,
    filter_mode: str = "all",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch next scheduled card in the study queue (Learning -> Due -> New), optionally filtered."""
    return await StudyService.get_next_queued_card(db, user.id, deck_id, filter_mode)


@router.post("/answer", response_model=CardAnswerResponse)
async def answer_card(
    req: CardAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit card review rating (1=Again, 2=Hard, 3=Good, 4=Easy).
    Calculates intervals, updates SRS states, logs revlog, and awards XP.
    """
    try:
        return await StudyService.submit_card_answer(
            db=db,
            user=user,
            card_id=req.card_id,
            rating_val=req.rating,
            time_taken_ms=req.time_taken_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/custom-increase", response_model=CustomIncreaseResponse)
async def custom_increase_limit(
    req: CustomIncreaseRequest,
    user: User = Depends(get_current_user),
):
    """
    Increases today's new card quota by requested amount (default +10).
    Allows user to continue studying when daily limit is reached.
    """
    new_bonus = StudyService.increase_daily_limit(
        user_id=user.id,
        deck_id=req.deck_id,
        amount=req.amount,
    )
    return CustomIncreaseResponse(
        success=True,
        added_cards=req.amount,
        remaining_new=new_bonus,
    )
