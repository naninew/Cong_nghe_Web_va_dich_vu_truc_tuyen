"""
Free Spaced Repetition Scheduler (FSRS-5) Implementation.

Memory model: Stability (S, days until R drops to 90%), Difficulty (D, 1..10),
Retrievability (R). 19 parameters, same layout as Anki 24.11+ / py-fsrs 4.x.

Like Anki, FSRS only decides *review* intervals; short-term learning and relearning
still go through the deck's (re)learning steps (minutes), during which S/D are updated
with the FSRS-5 short-term stability formula.
"""

import math
from typing import Dict, Optional, Tuple
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

# FSRS-5 default parameters (py-fsrs 4.x / Anki 24.11)
DEFAULT_FSRS_WEIGHTS = [
    0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575, 0.1192,
    1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621,
]
DECAY = -0.5
FACTOR = 19.0 / 81.0  # chosen so that R(t=S) = 0.9


class FSRSScheduler(BaseScheduler):
    """Free Spaced Repetition Scheduler (FSRS-5)."""

    def __init__(self, config: DeckConfigParams):
        super().__init__(config)
        params = config.fsrs_params
        self.w = list(params) if params and len(params) == 19 else list(DEFAULT_FSRS_WEIGHTS)
        dr = config.desired_retention or 0.90
        self.desired_retention = min(0.99, max(0.70, dr))

    # ------------------------------------------------------------------
    # FSRS-5 formulas
    # ------------------------------------------------------------------
    def retrievability(self, elapsed_days: float, stability: float) -> float:
        """R(t, S) = (1 + FACTOR * t / S) ^ DECAY"""
        if stability <= 0.0:
            return 0.0
        return math.pow(1.0 + FACTOR * max(0.0, elapsed_days) / stability, DECAY)

    def _interval_per_stability(self) -> float:
        """Days of interval per day of stability at the desired retention (=1.0 at 90%)."""
        return (math.pow(self.desired_retention, 1.0 / DECAY) - 1.0) / FACTOR

    def next_interval(self, stability: float) -> int:
        """Interval in days so that R falls to the desired retention."""
        ivl = stability * self._interval_per_stability()
        return int(max(1, min(self.config.maximum_interval, round(ivl))))

    def init_stability(self, rating: Rating) -> float:
        return max(0.1, self.w[rating.value - 1])

    def _init_difficulty_raw(self, rating: Rating) -> float:
        return self.w[4] - math.exp(self.w[5] * (rating.value - 1)) + 1.0

    def init_difficulty(self, rating: Rating) -> float:
        return _clamp_d(self._init_difficulty_raw(rating))

    def next_difficulty(self, curr_d: float, rating: Rating) -> float:
        """Linear damping toward 10, then mean reversion toward D0(Easy)."""
        delta = -self.w[6] * (rating.value - 3)
        damped = curr_d + delta * (10.0 - curr_d) / 9.0
        reverted = self.w[7] * self._init_difficulty_raw(Rating.EASY) + (1.0 - self.w[7]) * damped
        return _clamp_d(reverted)

    def next_recall_stability(self, d: float, s: float, r: float, rating: Rating) -> float:
        hard_penalty = self.w[15] if rating == Rating.HARD else 1.0
        easy_bonus = self.w[16] if rating == Rating.EASY else 1.0
        inc = (
            math.exp(self.w[8])
            * (11.0 - d)
            * math.pow(s, -self.w[9])
            * (math.exp(self.w[10] * (1.0 - r)) - 1.0)
            * hard_penalty
            * easy_bonus
        )
        return max(0.1, s * (1.0 + inc))

    def next_forget_stability(self, d: float, s: float, r: float) -> float:
        s_forget = (
            self.w[11]
            * math.pow(d, -self.w[12])
            * (math.pow(s + 1.0, self.w[13]) - 1.0)
            * math.exp(self.w[14] * (1.0 - r))
        )
        s_min = s / math.exp(self.w[17] * self.w[18])
        return max(0.1, min(s_forget, s_min))

    def short_term_stability(self, s: float, rating: Rating) -> float:
        """Same-day review (learning/relearning steps)."""
        inc = math.exp(self.w[17] * (rating.value - 3 + self.w[18]))
        if rating >= Rating.GOOD:
            inc = max(inc, 1.0)
        return max(0.1, s * inc)

    # ------------------------------------------------------------------
    # Memory state helpers
    # ------------------------------------------------------------------
    def memory_from_sm2(self, card: CardState) -> Tuple[float, float]:
        """
        Derive (S, D) for a card that was scheduled by SM-2 and has no FSRS state yet,
        so switching algorithms keeps the card's progress instead of resetting it.
          * S: stability that would produce the card's current interval at desired retention.
          * D: mapped from ease (250% -> 5, 130% -> 10, >=350% -> 1).
        """
        ivl = max(1, card.interval)
        s = max(0.1, ivl / self._interval_per_stability())
        ease = (card.factor or 2500) / 1000.0
        d = _clamp_d(5.0 + (2.5 - ease) * (5.0 / 1.2))
        return s, d

    @staticmethod
    def elapsed_days(card: CardState, today_day: int) -> int:
        """Days since last review. For review cards: last review day = due - interval."""
        if card.card_type == CardType.REVIEW and card.interval > 0:
            return max(0, today_day - (card.due - card.interval))
        return 0

    def _memory_after(
        self, s: Optional[float], d: Optional[float], rating: Rating, elapsed: int, short_term: bool
    ) -> Tuple[float, float]:
        if s is None or d is None:
            return self.init_stability(rating), self.init_difficulty(rating)
        new_d = self.next_difficulty(d, rating)
        if short_term:
            return self.short_term_stability(s, rating), new_d
        r = self.retrievability(elapsed, s)
        if rating == Rating.AGAIN:
            return self.next_forget_stability(d, s, r), new_d
        return self.next_recall_stability(d, s, r, rating), new_d

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------
    def schedule(
        self,
        card: CardState,
        rating: Rating,
        now_ts: int,
        today_day: int,
        time_taken_ms: int = 0,
    ) -> ScheduleResult:
        cfg = self.config
        ct = card.card_type
        lapses = card.lapses
        is_leech = False
        factor = card.factor or cfg.starting_ease

        s, d = card.fsrs_stability, card.fsrs_difficulty
        if (s is None or d is None) and ct in (CardType.REVIEW, CardType.RELEARNING) and card.interval > 0:
            s, d = self.memory_from_sm2(card)  # switched from SM-2: keep progress
        if ct == CardType.NEW:
            s, d = None, None

        elapsed = self.elapsed_days(card, today_day)
        short_term = ct in (CardType.LEARNING, CardType.RELEARNING) or (ct == CardType.REVIEW and elapsed == 0)
        new_s, new_d = self._memory_after(s, d, rating, elapsed, short_term)

        def learning(delay_min: float, left: int, new_type: CardType, ivl: int) -> dict:
            return dict(card_type=new_type, queue=CardQueue.LEARNING,
                        due=now_ts + int(round(delay_min * 60)), left=left, interval=ivl)

        def review(ivl: int) -> dict:
            return dict(card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                        due=today_day + ivl, interval=ivl, left=0)

        if ct in (CardType.NEW, CardType.LEARNING, CardType.RELEARNING):
            relearn = ct == CardType.RELEARNING
            review_type = ReviewType.RELEARN if relearn else ReviewType.LEARN
            steps = self.relearning_steps if relearn else self.learning_steps
            left = len(steps) if ct == CardType.NEW else card.left
            tr = None if (rating == Rating.EASY or not steps) else self.step_transition(steps, left, rating)
            if tr is None:
                state = review(self.apply_fuzz(self.next_interval(new_s), card))
            else:
                state = learning(tr[0], tr[1], ct if relearn else CardType.LEARNING, 0 if not relearn else card.interval)
        else:
            review_type = ReviewType.REVIEW
            if rating == Rating.AGAIN:
                lapses += 1
                is_leech = self.is_leech(lapses)
                lapse_ivl = self.next_interval(new_s)
                steps = self.relearning_steps
                state = (learning(steps[0], len(steps), CardType.RELEARNING, lapse_ivl)
                         if steps else review(lapse_ivl))
            else:
                state = review(self._ordered_review_intervals(card, s, d, elapsed, short_term)[rating])

        if is_leech and cfg.leech_action == "suspend":
            state["queue"] = CardQueue.SUSPENDED

        return ScheduleResult(
            card_id=card.card_id,
            rating=rating,
            factor=factor,
            reps=card.reps + 1,
            lapses=lapses,
            fsrs_stability=round(new_s, 4),
            fsrs_difficulty=round(new_d, 4),
            time_taken_ms=time_taken_ms,
            review_type=review_type,
            is_leech=is_leech,
            **state,
        )

    def _ordered_review_intervals(
        self, card: CardState, s: Optional[float], d: Optional[float], elapsed: int, short_term: bool
    ) -> Dict[Rating, int]:
        """Hard/Good/Easy intervals (fuzzed) with Anki's guarantee hard < good < easy."""
        ivls = {
            g: self.next_interval(self._memory_after(s, d, g, elapsed, short_term)[0])
            for g in (Rating.HARD, Rating.GOOD, Rating.EASY)
        }
        hard = self.apply_fuzz(min(ivls[Rating.HARD], ivls[Rating.GOOD]), card)
        good = self.apply_fuzz(max(ivls[Rating.GOOD], hard + 1), card, minimum=hard + 1)
        easy = self.apply_fuzz(max(ivls[Rating.EASY], good + 1), card, minimum=good + 1)
        return {Rating.HARD: hard, Rating.GOOD: good, Rating.EASY: easy}


def _clamp_d(d: float) -> float:
    return max(1.0, min(10.0, d))
