"""Shared API dependencies."""
import hmac
from fastapi import Header, HTTPException
from ..config import settings
from ..database import get_db


def require_admin(x_admin_pin: str = Header(default="")):
    """Host-only actions. If ADMIN_PIN is not configured, everything is allowed."""
    if settings.ADMIN_PIN and not hmac.compare_digest(x_admin_pin, settings.ADMIN_PIN):
        raise HTTPException(403, "Wrong admin PIN")


__all__ = ["get_db", "require_admin"]
