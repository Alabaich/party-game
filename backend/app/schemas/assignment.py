from datetime import datetime
from pydantic import BaseModel
from ..models.enums import TaskType, AssignmentStatus
from .user import UserOut, PlayerListItem
from .media import MediaOut


class AssignmentOut(BaseModel):
    id: int
    task_id: int
    description: str
    type: TaskType
    is_alcoholic: bool
    target_user_name: str | None
    pair_id: str | None
    status: AssignmentStatus
    completed_at: datetime | None
    media: list[MediaOut]


class DashboardOut(BaseModel):
    user: UserOut
    game_started: bool
    started_at: datetime | None
    server_time: datetime
    players: list[PlayerListItem]
    assignments: list[AssignmentOut]
    places_revealed: bool
