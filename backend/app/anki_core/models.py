"""
Anki Core Data Models and Constants.
Defines card states, rating buttons, queues, and scheduling parameters
compatible with official Anki conventions.
"""

from enum import IntEnum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time


class CardType(IntEnum):
    """Anki Card Types."""
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


class CardQueue(IntEnum):
    """Anki Card Queues."""
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    DAY_LEARNING = 3
    SUSPENDED = -1
    USER_BURIED = -2
    SCHED_BURIED = -3


class Rating(IntEnum):
    """Answer button choices."""
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class ReviewType(IntEnum):
    """Review log types."""
    LEARN = 0
    REVIEW = 1
    RELEARN = 2
    FILTERED = 3
    GAME_QUIZ = 4


class DeckConfigParams(BaseModel):
    """Deck configuration options governing scheduling."""
    new_per_day: int = 20
    reviews_per_day: int = 200
    learning_steps: List[float] = [1.0, 10.0]     # Minutes
    relearning_steps: List[float] = [10.0]        # Minutes
    graduating_interval: int = 1                  # Days
    easy_interval: int = 4                        # Days
    starting_ease: int = 2500                     # 250% (factor is ease * 10)
    minimum_ease: int = 1300                      # 130%
    hard_factor: float = 1.2
    easy_bonus: float = 1.3
    interval_modifier: float = 1.0
    maximum_interval: int = 36500                 # 100 years
    leech_threshold: int = 8
    leech_action: str = "tag"                     # "tag" or "suspend"
    fsrs_enabled: bool = False
    desired_retention: float = 0.90
    fsrs_params: Optional[List[float]] = None     # 19 weights for FSRS v4.5


class CardState(BaseModel):
    """Current state of a flashcard."""
    card_id: int
    card_type: CardType = CardType.NEW
    queue: CardQueue = CardQueue.NEW
    due: int = 0                                  # Day index or epoch timestamp
    interval: int = 0                             # In days (or minutes if in learning)
    factor: int = 2500                            # Ease factor * 10
    reps: int = 0
    lapses: int = 0
    left: int = 0                                 # Step remaining counter
    fsrs_stability: Optional[float] = None
    fsrs_difficulty: Optional[float] = None


class ScheduleResult(BaseModel):
    """Outcome of rating an Anki card."""
    card_id: int
    rating: Rating
    card_type: CardType
    queue: CardQueue
    due: int
    interval: int
    factor: int
    reps: int
    lapses: int
    left: int
    fsrs_stability: Optional[float] = None
    fsrs_difficulty: Optional[float] = None
    time_taken_ms: int = 0
    review_type: ReviewType = ReviewType.REVIEW
    is_leech: bool = False
