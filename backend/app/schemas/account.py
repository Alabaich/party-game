from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=80)
    invite_code: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AccountOut(BaseModel):
    id: str
    email: str
    display_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True
