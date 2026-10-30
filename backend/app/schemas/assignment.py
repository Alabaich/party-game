from datetime import datetime
from pydantic import BaseModel
from ..models.enums import TaskType, AssignmentStatus
from .user import UserOut, PlayerListItem
from .media import MediaOut
from .game import GamePublicOut


class AssignmentOut(BaseModel):
    id: int
    task_id: int
    description: str
    type: TaskType
    is_alcoholic: bool
    target_user_name: str | None
    target_hint: str | None = None   # e.g. their building, to help find them
    pair_id: str | None
    status: AssignmentStatus
    completed_at: datetime | None
    media: list[MediaOut]


class DashboardOut(BaseModel):
    user: UserOut
    game: GamePublicOut
    players: list[PlayerListItem]
    assignments: list[AssignmentOut]
