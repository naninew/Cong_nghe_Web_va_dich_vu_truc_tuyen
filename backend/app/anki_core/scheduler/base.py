"""
Abstract Base Scheduler Interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from ..models import CardState, DeckConfigParams, Rating, ScheduleResult


class BaseScheduler(ABC):
    """Abstract interface for spaced repetition schedulers."""

    def __init__(self, config: DeckConfigParams):
        self.config = config

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
        :param today_day: Current day index (days since collection creation epoch).
        :param time_taken_ms: Response time in milliseconds.
        :return: ScheduleResult object with updated parameters.
        """
        pass

    @abstractmethod
    def describe_next_intervals(
        self, card: CardState, now_ts: int, today_day: int
    ) -> Dict[str, str]:
        """
        Return human-readable interval previews for the 4 rating buttons (Again, Hard, Good, Easy).
        Example: {'again': '< 1m', 'hard': '12h', 'good': '1d', 'easy': '4d'}
        """
        pass
