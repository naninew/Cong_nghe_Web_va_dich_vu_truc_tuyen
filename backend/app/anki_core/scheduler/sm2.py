"""
SM-2 Spaced Repetition Scheduler (Anki V2/V3 compatible).
Implements learning steps, graduation, review intervals, lapses, and leeches.
"""

import math
from typing import Dict, List
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


class SM2Scheduler(BaseScheduler):
    """Anki SM-2 / V2 / V3 Algorithm Implementation."""

    def schedule(
        self,
        card: CardState,
        rating: Rating,
        now_ts: int,
        today_day: int,
        time_taken_ms: int = 0,
    ) -> ScheduleResult:
        cfg = self.config
        steps = cfg.learning_steps if cfg.learning_steps else [1.0, 10.0]
        relearn_steps = cfg.relearning_steps if cfg.relearning_steps else [10.0]

        card_type = card.card_type
        factor = card.factor
        reps = card.reps + 1
        lapses = card.lapses
        is_leech = False
        review_type = ReviewType.REVIEW

        # -------------------------------------------------------------
        # 1. NEW CARD
        # -------------------------------------------------------------
        if card_type == CardType.NEW:
            review_type = ReviewType.LEARN
            if rating == Rating.AGAIN:
                step_idx = 0
                step_mins = steps[step_idx]
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.LEARNING
                left = len(steps) - step_idx
            elif rating == Rating.HARD:
                step_idx = 0
                # Anki hard on first step takes average of step 0 and step 1 or 1.5x
                step_mins = (
                    (steps[0] + (steps[1] if len(steps) > 1 else steps[0] * 2)) / 2.0
                )
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.LEARNING
                left = len(steps)
            elif rating == Rating.GOOD:
                if len(steps) > 1:
                    step_idx = 1
                    step_mins = steps[step_idx]
                    due = now_ts + int(step_mins * 60)
                    interval = 0
                    queue = CardQueue.LEARNING
                    card_type = CardType.LEARNING
                    left = len(steps) - 1
                else:
                    # Graduates immediately
                    interval = cfg.graduating_interval
                    due = today_day + interval
                    queue = CardQueue.REVIEW
                    card_type = CardType.REVIEW
                    left = 0
            elif rating == Rating.EASY:
                interval = cfg.easy_interval
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

        # -------------------------------------------------------------
        # 2. LEARNING CARD
        # -------------------------------------------------------------
        elif card_type == CardType.LEARNING:
            review_type = ReviewType.LEARN
            if rating == Rating.AGAIN:
                step_mins = steps[0]
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.LEARNING
                left = len(steps)
            elif rating == Rating.HARD:
                current_step_idx = max(0, len(steps) - card.left) if card.left > 0 else 0
                step_mins = steps[min(current_step_idx, len(steps) - 1)] * 1.2
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.LEARNING
                left = card.left
            elif rating == Rating.GOOD:
                current_step_idx = max(0, len(steps) - card.left) if card.left > 0 else 0
                next_step_idx = current_step_idx + 1
                if next_step_idx < len(steps):
                    step_mins = steps[next_step_idx]
                    due = now_ts + int(step_mins * 60)
                    interval = 0
                    queue = CardQueue.LEARNING
                    card_type = CardType.LEARNING
                    left = len(steps) - next_step_idx
                else:
                    # Graduate to review!
                    interval = cfg.graduating_interval
                    due = today_day + interval
                    queue = CardQueue.REVIEW
                    card_type = CardType.REVIEW
                    left = 0
            elif rating == Rating.EASY:
                interval = cfg.easy_interval
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

        # -------------------------------------------------------------
        # 3. RELEARNING CARD (after lapse)
        # -------------------------------------------------------------
        elif card_type == CardType.RELEARNING:
            review_type = ReviewType.RELEARN
            if rating == Rating.AGAIN:
                step_mins = relearn_steps[0]
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.RELEARNING
                left = len(relearn_steps)
            elif rating == Rating.HARD:
                step_mins = relearn_steps[0] * 1.5
                due = now_ts + int(step_mins * 60)
                interval = 0
                queue = CardQueue.LEARNING
                card_type = CardType.RELEARNING
                left = card.left
            elif rating == Rating.GOOD:
                # Graduates back to review
                interval = max(1, card.interval)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0
            elif rating == Rating.EASY:
                interval = max(cfg.easy_interval, card.interval + 1)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

        # -------------------------------------------------------------
        # 4. REVIEW CARD (mature / graduated)
        # -------------------------------------------------------------
        else:
            review_type = ReviewType.REVIEW
            prev_ivl = max(1, card.interval)

            if rating == Rating.AGAIN:
                lapses += 1
                factor = max(cfg.minimum_ease, factor - 200)
                if lapses >= cfg.leech_threshold:
                    is_leech = True

                if relearn_steps:
                    step_mins = relearn_steps[0]
                    due = now_ts + int(step_mins * 60)
                    interval = 1
                    queue = (
                        CardQueue.SUSPENDED
                        if (is_leech and cfg.leech_action == "suspend")
                        else CardQueue.LEARNING
                    )
                    card_type = CardType.RELEARNING
                    left = len(relearn_steps)
                else:
                    interval = 1
                    due = today_day + 1
                    queue = (
                        CardQueue.SUSPENDED
                        if (is_leech and cfg.leech_action == "suspend")
                        else CardQueue.REVIEW
                    )
                    card_type = CardType.REVIEW
                    left = 0

            elif rating == Rating.HARD:
                factor = max(cfg.minimum_ease, factor - 150)
                interval = max(
                    prev_ivl + 1,
                    round(prev_ivl * cfg.hard_factor * cfg.interval_modifier),
                )
                interval = min(interval, cfg.maximum_interval)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

            elif rating == Rating.GOOD:
                interval = max(
                    prev_ivl + 1,
                    round(prev_ivl * (factor / 1000.0) * cfg.interval_modifier),
                )
                interval = min(interval, cfg.maximum_interval)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

            elif rating == Rating.EASY:
                factor = factor + 150
                interval = max(
                    prev_ivl + 1,
                    round(
                        prev_ivl
                        * (factor / 1000.0)
                        * cfg.easy_bonus
                        * cfg.interval_modifier
                    ),
                )
                interval = min(interval, cfg.maximum_interval)
                due = today_day + interval
                queue = CardQueue.REVIEW
                card_type = CardType.REVIEW
                left = 0

        return ScheduleResult(
            card_id=card.card_id,
            rating=rating,
            card_type=card_type,
            queue=queue,
            due=due,
            interval=interval,
            factor=factor,
            reps=reps,
            lapses=lapses,
            left=left,
            time_taken_ms=time_taken_ms,
            review_type=review_type,
            is_leech=is_leech,
        )

    def describe_next_intervals(
        self, card: CardState, now_ts: int, today_day: int
    ) -> Dict[str, str]:
        """Generate human-readable preview intervals for buttons."""
        cfg = self.config
        steps = cfg.learning_steps if cfg.learning_steps else [1.0, 10.0]

        if card.card_type in (CardType.NEW, CardType.LEARNING):
            again_mins = steps[0]
            good_mins = steps[1] if len(steps) > 1 else cfg.graduating_interval * 1440
            return {
                "again": f"< {int(again_mins)}m",
                "hard": f"{int(again_mins * 1.5)}m",
                "good": f"{int(good_mins)}m" if len(steps) > 1 else f"{cfg.graduating_interval}d",
                "easy": f"{cfg.easy_interval}d",
            }
        else:
            prev_ivl = max(1, card.interval)
            hard_ivl = max(
                prev_ivl + 1, round(prev_ivl * cfg.hard_factor * cfg.interval_modifier)
            )
            good_ivl = max(
                prev_ivl + 1,
                round(prev_ivl * (card.factor / 1000.0) * cfg.interval_modifier),
            )
            easy_ivl = max(
                prev_ivl + 1,
                round(
                    prev_ivl
                    * (card.factor / 1000.0)
                    * cfg.easy_bonus
                    * cfg.interval_modifier
                ),
            )
            return {
                "again": "< 10m",
                "hard": f"{hard_ivl}d",
                "good": f"{good_ivl}d",
                "easy": f"{easy_ivl}d",
            }
