"""Schemas package — re-exports all schemas (`schemas.UserOut`, ...)."""
from .user import RegisterIn, UserOut, PlayerListItem, PlayerAdminOut
from .media import (
    MediaOut, PresignIn, PresignOut, UploadedFile, CompleteTaskIn,
)
from .game import (
    LeaderboardItem, GamePublicOut, GameAdminOut, GameCreateIn, GameUpdateIn, PackOut,
)
from .assignment import AssignmentOut, DashboardOut, Wildcard
from .slideshow import SlideItem
from .account import SignupIn, LoginIn, AccountOut
from .settings import GameSettings, Question, Prize
from .task import TaskIn, TaskOut
