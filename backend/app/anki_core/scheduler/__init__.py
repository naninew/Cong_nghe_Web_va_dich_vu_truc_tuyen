"""
Scheduler Factory and Exports.
"""

from .base import BaseScheduler
from .sm2 import SM2Scheduler
from .fsrs import FSRSScheduler
from ..models import DeckConfigParams


def get_scheduler(config: DeckConfigParams) -> BaseScheduler:
    """Return appropriate scheduler instance based on configuration."""
    if config.fsrs_enabled:
        return FSRSScheduler(config)
    return SM2Scheduler(config)


__all__ = ["BaseScheduler", "SM2Scheduler", "FSRSScheduler", "get_scheduler"]
