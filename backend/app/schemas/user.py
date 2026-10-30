from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    name: str = Field(max_length=40)
    answers: dict[str, Any] = {}
    consent_sha256: str | None = None


class UserOut(BaseModel):
    id: str
    name: str
    is_drinking: bool
    is_latecomer: bool

    class Config:
        from_attributes = True


class PlayerListItem(BaseModel):
    key: str     # public player key, never the real id
    name: str


class PlayerAdminOut(BaseModel):
    id: str
    name: str
    answers: dict[str, Any] | None
    is_latecomer: bool
    consent_accepted_at: datetime | None
    completed_count: int
    total: int
