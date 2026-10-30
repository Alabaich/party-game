"""Schemas package — re-exports all schemas so existing access patterns like
`schemas.UserOut`, `schemas.AssignmentOut` keep working after the split.
"""
from .user import RegisterIn, UserOut, PlayerListItem
from .media import (
    MediaOut, PresignIn, PresignOut, UploadedFile, CompleteTaskIn,
)
from .assignment import AssignmentOut, DashboardOut
from .game import LeaderboardItem, GameStatusOut
from .slideshow import SlideItem
from .account import AccountCreateIn, AccountOut, GameCreateIn, GameOut

__all__ = [
    "RegisterIn", "UserOut", "PlayerListItem",
    "MediaOut", "PresignIn", "PresignOut", "UploadedFile", "CompleteTaskIn",
    "AssignmentOut", "DashboardOut",
    "LeaderboardItem", "GameStatusOut",
    "SlideItem",
    "AccountCreateIn", "AccountOut", "GameCreateIn", "GameOut",
]
