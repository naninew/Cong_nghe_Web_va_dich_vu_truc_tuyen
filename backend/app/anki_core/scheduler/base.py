"""
Abstract Base Scheduler Interface + shared Anki behaviours.

Shared pieces used by both SM-2 and FSRS so the two algorithms stay consistent:
  * learning / relearning step transitions (Anki v3 semantics)
  * leech detection
  * interval previews, computed by *running* ``schedule()`` for each button so the
    label on a button can never disagree with what actually happens.

Due-value convention (same as Anki):
  * card_type LEARNING / RELEARNING  -> ``due`` is a unix timestamp (seconds)
  * card_type REVIEW                 -> ``due`` is a day number (see StudyService.get_day_timing)
  * card_type NEW                    -> ``due`` is the new-card position
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from ..models import CardState, CardType, DeckConfigParams, Rating, ScheduleResult

DEFAULT_LEARNING_STEPS = [1.0, 10.0]


class BaseScheduler(ABC):
    """Abstract interface for spaced repetition schedulers."""

    def __init__(self, config: DeckConfigParams):
        self.config = config

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------
    @property
    def learning_steps(self) -> List[float]:
        return list(self.config.learning_steps) if self.config.learning_steps else list(DEFAULT_LEARNING_STEPS)

    @property
    def relearning_steps(self) -> List[float]:
        # An empty list is meaningful: lapsed cards go straight back to review.
        return list(self.config.relearning_steps or [])

    # ------------------------------------------------------------------
    # Shared Anki behaviours
    # ------------------------------------------------------------------
    @staticmethod
    def step_transition(
        steps: List[float], left: int, rating: Rating
    ) -> Optional[Tuple[float, int]]:
        """
        Anki v3 learning-step transition.

        :param steps: step delays in minutes (non-empty).
        :param left: remaining steps counter of the card (``len(steps)`` = at first step).
        :return: ``(delay_minutes, new_left)`` if the card stays in (re)learning,
                 or ``None`` if the card graduates.
        """
        n = len(steps)
        if n == 0:
            return None  # no steps configured: card leaves (re)learning immediately
        left = left if 0 < left <= n else n
        idx = n - left  # index of the step the card is currently on

        if rating == Rating.AGAIN:
            return steps[0], n
        if rating == Rating.HARD:
            if idx == 0:
                # First step: average of step 1 and 2, or 1.5x a single step (capped at +1 day).
                delay = (steps[0] + steps[1]) / 2.0 if n > 1 else min(steps[0] * 1.5, steps[0] + 1440.0)
            else:
                delay = steps[idx]  # repeat current step
            return delay, left
        if rating == Rating.GOOD:
            nxt = idx + 1
            if nxt < n:
                return steps[nxt], n - nxt
            return None
        return None  # EASY always graduates

    def is_leech(self, lapses: int) -> bool:
        """Anki: leech at the threshold, then again every half-threshold lapses."""
        threshold = self.config.leech_threshold
        if threshold <= 0 or lapses < threshold:
            return False
        return (lapses - threshold) % max(1, threshold // 2) == 0

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    @abstractmethod
    def schedule(
        self,
        card: CardState,
        rating: Rating,
        now_ts: int,
        today_day: int,
        time_taken_ms: int = 0,
    ) -> ScheduleResult:
        """
        Calculate next card state based on rating and deck configuration.

        :param card: Current card state.
        :param rating: User selected answer rating (1..4).
        :param now_ts: Current unix epoch timestamp (seconds).
        :param today_day: Current day number.
        :param time_taken_ms: Response time in milliseconds.
        """

    def describe_next_intervals(
        self, card: CardState, now_ts: int, today_day: int
    ) -> Dict[str, str]:
        """
        Human-readable previews for the 4 buttons, e.g. {'again': '1m', 'hard': '6m', 'good': '10m', 'easy': '4d'}.
        Derived from ``schedule()`` itself so preview == reality.
        """
        out: Dict[str, str] = {}
        for rating in Rating:
            res = self.schedule(card, rating, now_ts, today_day)
            out[rating.name.lower()] = format_due(res, now_ts, today_day)
        return out


def format_due(res: ScheduleResult, now_ts: int, today_day: int) -> str:
    """Format the delay until ``res.due`` like Anki does (<1m, 10m, 1.5h, 3d, 2.1mo, 1.3y)."""
    if res.card_type in (CardType.LEARNING, CardType.RELEARNING):
        secs = max(0, res.due - now_ts)
        if secs < 60:
            return "<1m"
        if secs < 3600:
            return f"{round(secs / 60)}m"
        if secs < 86400:
            return _trim(secs / 3600) + "h"
        days = secs / 86400
    else:
        days = max(0, res.due - today_day)
    if days < 30:
        return f"{round(days)}d"
    if days < 365:
        return _trim(days / 30) + "mo"
    return _trim(days / 365) + "y"


def _trim(x: float) -> str:
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s
