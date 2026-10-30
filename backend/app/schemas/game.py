from datetime import datetime
from pydantic import BaseModel, Field
from .settings import GameSettings


class LeaderboardItem(BaseModel):
    user_id: str
    name: str
    completed_count: int
    total: int
    finished: bool
    completed_at: datetime | None
    duration_seconds: int | None
    is_winner: bool


class GamePublicOut(BaseModel):
    """What players and the TV screen see."""
    code: str
    name: str
    settings: GameSettings
    tasks_per_user: int
    started: bool
    started_at: datetime | None
    places_revealed: bool
    player_count: int
    can_join: bool
    consent_sha256: str | None   # send back on register to prove which text was shown
    server_time: datetime


class GameAdminOut(GamePublicOut):
    id: str
    task_count: int
    created_at: datetime


class GameCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    theme: str = "party"
    pack: str | None = None


class GameUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    tasks_per_user: int | None = Field(default=None, ge=1, le=20)
    settings: GameSettings | None = None


class PackOut(BaseModel):
    id: str
    title: str
    task_count: int
