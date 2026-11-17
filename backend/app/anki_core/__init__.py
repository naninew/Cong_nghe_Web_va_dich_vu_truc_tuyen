"""
Anki Core Packaged Module.
Independent, pure-Python logic engine for Spaced Repetition, Template Rendering,
APKG Import/Export, and Search.
"""

from .models import (
    CardType,
    CardQueue,
    Rating,
    ReviewType,
    CardState,
    DeckConfigParams,
    ScheduleResult,
)
from .scheduler import BaseScheduler, SM2Scheduler, FSRSScheduler, get_scheduler
from .template import TemplateRenderer
from .importer import ApkgImporter, ApkgPackageData
from .exporter import ApkgExporter
from .search import SearchQueryParser, ParsedSearchQuery

__version__ = "1.0.0"

__all__ = [
    "CardType",
    "CardQueue",
    "Rating",
    "ReviewType",
    "CardState",
    "DeckConfigParams",
    "ScheduleResult",
    "BaseScheduler",
    "SM2Scheduler",
    "FSRSScheduler",
    "get_scheduler",
    "TemplateRenderer",
    "ApkgImporter",
    "ApkgPackageData",
    "ApkgExporter",
    "SearchQueryParser",
    "ParsedSearchQuery",
]
