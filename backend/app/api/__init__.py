"""API package — combines all sub-routers into one APIRouter.

Existing game routes keep their original paths (no prefix). New platform
endpoints live under /accounts.
"""
from fastapi import APIRouter
from . import (
    registration, game, dashboard, media, leaderboard, slideshow, accounts,
)

router = APIRouter()

# existing single-game routes — paths unchanged
router.include_router(registration.router)
router.include_router(game.router)
router.include_router(dashboard.router)
router.include_router(media.router)
router.include_router(leaderboard.router)
router.include_router(slideshow.router)

# new platform routes
router.include_router(accounts.router)

__all__ = ["router"]
