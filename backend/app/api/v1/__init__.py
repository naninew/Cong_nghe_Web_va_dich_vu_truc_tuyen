"""
API v1 Router Registration.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .decks import router as decks_router
from .study import router as study_router
from .games import router as games_router
from .stats import router as stats_router
from .cards import router as cards_router
from .import_export import router as import_export_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(decks_router)
api_router.include_router(cards_router)
api_router.include_router(study_router)
api_router.include_router(games_router)
api_router.include_router(stats_router)
api_router.include_router(import_export_router)
