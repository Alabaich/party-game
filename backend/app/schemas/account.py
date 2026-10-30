from datetime import datetime
from pydantic import BaseModel, EmailStr


class AccountCreateIn(BaseModel):
    email: EmailStr
    display_name: str | None = None
    password: str | None = None  # stub until auth lands


class AccountOut(BaseModel):
    id: str
    email: str
    display_name: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GameCreateIn(BaseModel):
    name: str = "Party Quest"
    tasks_per_user: int = 7


class GameOut(BaseModel):
    id: str
    account_id: str | None
    name: str
    tasks_per_user: int
    started_at: datetime | None
    tasks_assigned: bool
    places_revealed: bool
    created_at: datetime

    class Config:
        from_attributes = True
