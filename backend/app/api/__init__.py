"""API package — combines all sub-routers into one APIRouter."""
from fastapi import APIRouter
from . import public, dashboard, media, auth, admin

router = APIRouter()
router.include_router(public.router)      # /g/{code}/...   players + TV screen
router.include_router(dashboard.router)   # /u/{user_id}    player's own page
router.include_router(media.router)       # uploads, proof, download
router.include_router(auth.router)        # /auth/...       host accounts
router.include_router(admin.router)       # /admin/...      host tools

__all__ = ["router"]
