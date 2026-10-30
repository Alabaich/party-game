from datetime import datetime
from pydantic import BaseModel


class LeaderboardItem(BaseModel):
    user_id: str
    name: str
    completed_count: int
    finished: bool
    completed_at: datetime | None
    duration_seconds: int | None
    is_winner: bool


class GameStatusOut(BaseModel):
    exists: bool
    started: bool
    started_at: datetime | None
    player_count: int
    server_time: datetime
    places_revealed: bool
