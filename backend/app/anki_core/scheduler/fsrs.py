"""
Free Spaced Repetition Scheduler (FSRS v4.5) Implementation.
Uses human memory retention model with Stability (S), Difficulty (D), and Retrievability (R).
"""

import math
from typing import Dict, List, Optional
from .base import BaseScheduler
from ..models import (
    CardState,
    DeckConfigParams,
    Rating,
    CardType,
    CardQueue,
    ReviewType,
    ScheduleResult,
)

# Standard FSRS-4.5 default 19 weights
DEFAULT_FSRS_WEIGHTS = [
    0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14,
    0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61, 0.42, 0.28,
]


class FSRSScheduler(BaseScheduler):
    """Free Spaced Repetition Scheduler (FSRS v4.5)."""

    def __init__(self, config: DeckConfigParams):
        super().__init__(config)
        self.w = config.fsrs_params if config.fsrs_params and len(config.fsrs_params) >= 19 else DEFAULT_FSRS_WEIGHTS
        self.desired_retention = config.desired_retention if config.desired_retention else 0.90

    def retrievability(self, elapsed_days: float, stability: float) -> float:
        """Calculate retrievability probability R(t, S)."""
        if stability <= 0.0:
            return 0.0
        return math.pow(1.0 + (19.0 / 81.0) * (elapsed_days / stability), -0.5)

    def next_interval(self, stability: float) -> int:
        """Calculate interval in days to reach desired retention."""
        if stability <= 0.0:
            return 1
        ivl = stability * (math.log(self.desired_retention) / math.log(0.90))
        return max(1, min(self.config.maximum_interval, round(ivl)))

    def init_stability(self, rating: Rating) -> float:
        """Initial stability for first review."""
        idx = rating.value - 1
        return max(0.1, self.w[idx])

    def init_difficulty(self, rating: Rating) -> float:
        """Initial difficulty on a scale from 1.0 to 10.0."""
        d0 = self.w[4] - math.exp(self.w[5] * (rating.value - 1)) + 1.0
        return max(1.0, min(10.0, d0))

    def next_difficulty(self, curr_d: float, rating: Rating) -> float:
        """Update difficulty with mean reversion."""
        d0_good = self.init_difficulty(Rating.GOOD)
        delta = -self.w[6] * (rating.value - 3)
        next_d = self.w[7] * d0_good + (1.0 - self.w[7]) * (curr_d + delta)
        return max(1.0, min(10.0, next_d))

    def next_recall_stability(
        self, curr_d: float, curr_s: float, r: float, rating: Rating
    ) -> float:
        """Calculate new stability on successful recall (Hard, Good, Easy)."""
        hard_penalty = self.w[15] if rating == Rating.HARD else 1.0
        easy_bonus = self.w[16] if rating == Rating.EASY else 1.0
        
        factor = (
            math.exp(self.w[8])
            * (11.0 - curr_d)
            * math.pow(curr_s, -self.w[9])
            * (math.exp(self.w[10] * (1.0 - r)) - 1.0)
            * hard_penalty
            * easy_bonus
        )
        return max(0.1, curr_s * (1.0 + factor))

    def next_forget_stability(self, curr_d: float, curr_s: float, r: float) -> float:
        """Calculate new stability on lapse (Again)."""
        s_forget = (
            self.w[11]
            * math.pow(curr_d, -self.w[12])
            * (math.pow(curr_s + 1.0, self.w[13]) - 1.0)
            * math.exp(self.w[14] * (1.0 - r))
        )
        return max(0.1, min(curr_s, s_forget))

    def schedule(
        self,
        card: CardState,
        rating: Rating,
        now_ts: int,
        today_day: int,
        time_taken_ms: int = 0,
    ) -> ScheduleResult:
        cfg = self.config
        reps = card.reps + 1
        lapses = card.lapses
        is_leech = False

        if card.card_type == CardType.NEW or card.fsrs_stability is None:
            # First learning event
            new_s = self.init_stability(rating)
            new_d = self.init_difficulty(rating)
            if rating == Rating.AGAIN:
                interval = 1
                due = today_day + 1
                queue = CardQueue.LEARNING
                card_type = CardType.LEARNING
            else:
                interval = self.next_interval(new_s)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
        else:
            curr_s = card.fsrs_stability
            curr_d = card.fsrs_difficulty if card.fsrs_difficulty is not None else 5.0
            
            # Days since card was last scheduled / elapsed
            elapsed = max(0, today_day - (card.due - card.interval)) if card.interval > 0 else 1
            r = self.retrievability(elapsed, curr_s)

            new_d = self.next_difficulty(curr_d, rating)

            if rating == Rating.AGAIN:
                lapses += 1
                if lapses >= cfg.leech_threshold:
                    is_leech = True
                new_s = self.next_forget_stability(curr_d, curr_s, r)
                interval = 1
                due = today_day + 1
                queue = (
                    CardQueue.SUSPENDED
                    if (is_leech and cfg.leech_action == "suspend")
                    else CardQueue.LEARNING
                )
                card_type = CardType.RELEARNING
            else:
                new_s = self.next_recall_stability(curr_d, curr_s, r, rating)
                interval = self.next_interval(new_s)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW

        return ScheduleResult(
            card_id=card.card_id,
            rating=rating,
            card_type=card_type,
            queue=queue,
            due=due,
            interval=interval,
            factor=card.factor,
            reps=reps,
            lapses=lapses,
            left=0,
            fsrs_stability=round(new_s, 2),
            fsrs_difficulty=round(new_d, 2),
            time_taken_ms=time_taken_ms,
            review_type=ReviewType.REVIEW if card.card_type == CardType.REVIEW else ReviewType.LEARN,
            is_leech=is_leech,
        )

    def describe_next_intervals(
        self, card: CardState, now_ts: int, today_day: int
    ) -> Dict[str, str]:
        """Describe next intervals for 4 ratings under FSRS."""
        if card.fsrs_stability is None:
            return {
                "again": "< 10m",
                "hard": f"{self.next_interval(self.init_stability(Rating.HARD))}d",
                "good": f"{self.next_interval(self.init_stability(Rating.GOOD))}d",
                "easy": f"{self.next_interval(self.init_stability(Rating.EASY))}d",
            }
        
        curr_s = card.fsrs_stability
        curr_d = card.fsrs_difficulty or 5.0
        elapsed = max(0, today_day - (card.due - card.interval)) if card.interval > 0 else 1
        r = self.retrievability(elapsed, curr_s)

        s_again = self.next_forget_stability(curr_d, curr_s, r)
        s_hard = self.next_recall_stability(curr_d, curr_s, r, Rating.HARD)
        s_good = self.next_recall_stability(curr_d, curr_s, r, Rating.GOOD)
        s_easy = self.next_recall_stability(curr_d, curr_s, r, Rating.EASY)

        return {
            "again": "< 10m",
            "hard": f"{self.next_interval(s_hard)}d",
            "good": f"{self.next_interval(s_good)}d",
            "easy": f"{self.next_interval(s_easy)}d",
        }
