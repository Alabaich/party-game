from pydantic import BaseModel


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
