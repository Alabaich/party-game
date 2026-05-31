from datetime import datetime
from pydantic import BaseModel
from .models import TaskType, AssignmentStatus, MediaType


# ---- Registration ----
class RegisterIn(BaseModel):
    name: str
    is_drinking: bool


class UserOut(BaseModel):
    id: str
    name: str
    is_drinking: bool
    is_latecomer: bool

    class Config:
        from_attributes = True


class PlayerListItem(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


# ---- Media inside assignment ----
class MediaOut(BaseModel):
    id: int
    file_url: str
    media_type: MediaType

    class Config:
        from_attributes = True


# ---- Assignment / dashboard ----
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
    players: list[PlayerListItem]      # для екрану очікування
    assignments: list[AssignmentOut]   # порожній поки гра не почалась


# ---- Presigned upload ----
class PresignIn(BaseModel):
    filename: str
    content_type: str


class PresignOut(BaseModel):
    upload_url: str
    public_url: str


class CompleteTaskIn(BaseModel):
    # фронт надсилає сюди публічні URL після успішної заливки в R2
    files: list["UploadedFile"]


class UploadedFile(BaseModel):
    public_url: str
    media_type: MediaType


# ---- Leaderboard ----
class LeaderboardItem(BaseModel):
    user_id: str
    name: str
    completed_count: int
    finished: bool
    completed_at: datetime | None
    duration_seconds: int | None   # completed_at - started_at, лише для finished
    is_winner: bool                # топ-3 серед finished


# ---- Game status (для кнопки СТАРТ) ----
class GameStatusOut(BaseModel):
    exists: bool          # чи зареєстрований хоч хтось
    started: bool
    started_at: datetime | None
    player_count: int
    server_time: datetime


# ---- Slideshow ----
class SlideItem(BaseModel):
    assignment_id: int
    user_name: str
    task_description: str
    media: list[MediaOut]
    completed_at: datetime


CompleteTaskIn.model_rebuild()
