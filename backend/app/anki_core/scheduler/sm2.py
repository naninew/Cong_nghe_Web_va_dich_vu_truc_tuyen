"""
SM-2 Spaced Repetition Scheduler (Anki V2/V3 compatible).
Implements learning steps, graduation, review intervals, lapses, relearning steps and leeches.
"""

from typing import Dict
from .base import BaseScheduler
from ..models import (
    CardState,
    Rating,
    CardType,
    CardQueue,
    ReviewType,
    ScheduleResult,
)


class SM2Scheduler(BaseScheduler):
    """Anki SM-2 / V2 / V3 Algorithm Implementation."""

    def review_intervals(self, card: CardState) -> Dict[Rating, int]:
        """
        Intervals (days) for Hard / Good / Easy on a review card.
        Anki guarantees hard < good < easy, and each is at least previous interval + 1.
        """
        cfg = self.config
        prev = max(1, card.interval)
        ease = (card.factor or cfg.starting_ease) / 1000.0
        im = cfg.interval_modifier

        hard = max(prev + 1, round(prev * cfg.hard_factor * im))
        good = max(hard + 1, round(prev * ease * im))
        easy = max(good + 1, round(prev * ease * cfg.easy_bonus * im))
        cap = cfg.maximum_interval
        return {Rating.HARD: min(hard, cap), Rating.GOOD: min(good, cap), Rating.EASY: min(easy, cap)}

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
        factor = card.factor or cfg.starting_ease
        lapses = card.lapses
        is_leech = False

        def learning(delay_min: float, left: int, new_type: CardType) -> dict:
            return dict(card_type=new_type, queue=CardQueue.LEARNING,
                        due=now_ts + int(round(delay_min * 60)), left=left)

        def review(ivl: int) -> dict:
            return dict(card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                        due=today_day + ivl, interval=ivl, left=0)

        # 1. NEW / LEARNING ------------------------------------------------
        if ct in (CardType.NEW, CardType.LEARNING):
            review_type = ReviewType.LEARN
            if ct == CardType.NEW:
                factor = cfg.starting_ease
            steps = self.learning_steps
            left = card.left if ct == CardType.LEARNING else len(steps)
            tr = None if rating == Rating.EASY else self.step_transition(steps, left, rating)
            if tr is None:
                ivl = cfg.easy_interval if rating == Rating.EASY else cfg.graduating_interval
                state = review(max(1, ivl))
            else:
                state = learning(tr[0], tr[1], CardType.LEARNING)
                state["interval"] = 0

        # 2. RELEARNING (after a lapse) -------------------------------------
        elif ct == CardType.RELEARNING:
            review_type = ReviewType.RELEARN
            lapse_ivl = max(1, card.interval)
            steps = self.relearning_steps
            tr = None if (rating == Rating.EASY or not steps) else self.step_transition(steps, card.left, rating)
            if tr is None:
                state = review(min(cfg.maximum_interval, lapse_ivl + 1 if rating == Rating.EASY else lapse_ivl))
            else:
                state = learning(tr[0], tr[1], CardType.RELEARNING)
                state["interval"] = lapse_ivl

        # 3. REVIEW ---------------------------------------------------------
        else:
            review_type = ReviewType.REVIEW
            if rating == Rating.AGAIN:
                lapses += 1
                factor = max(cfg.minimum_ease, factor - 200)
                is_leech = self.is_leech(lapses)
                lapse_ivl = 1  # Anki default "new interval" = 0% -> minimum 1 day
                steps = self.relearning_steps
                if steps:
                    state = learning(steps[0], len(steps), CardType.RELEARNING)
                    state["interval"] = lapse_ivl
                else:
                    state = review(lapse_ivl)
            else:
                ivl = self.review_intervals(card)[rating]
                if rating == Rating.HARD:
                    factor = max(cfg.minimum_ease, factor - 150)
                elif rating == Rating.EASY:
                    factor = factor + 150
                state = review(ivl)

        if is_leech and cfg.leech_action == "suspend":
            state["queue"] = CardQueue.SUSPENDED

        return ScheduleResult(
            card_id=card.card_id,
            rating=rating,
            factor=factor,
            reps=card.reps + 1,
            lapses=lapses,
            time_taken_ms=time_taken_ms,
            review_type=review_type,
            is_leech=is_leech,
            **state,
        )
