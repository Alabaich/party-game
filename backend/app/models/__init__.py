"""Models package.

Re-exports every model and enum so that existing imports like
`from app.models import User, Task, GameState` keep working unchanged after
the split into per-file modules.
"""
from .enums import TaskType, AssignmentStatus, MediaType
from .account import Account
from .game import Game
from .game_state import GameState  # legacy singleton, being superseded by Game
from .user import User
from .task import Task
from .assignment import Assignment
from .media import Media, FreeMedia
from .consent import ConsentDocument

__all__ = [
    "TaskType",
    "AssignmentStatus",
    "MediaType",
    "Account",
    "Game",
    "GameState",
    "User",
    "Task",
    "Assignment",
    "Media",
    "FreeMedia",
    "ConsentDocument",
]
