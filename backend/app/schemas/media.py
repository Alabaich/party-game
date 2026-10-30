from pydantic import BaseModel
from ..models.enums import MediaType


class MediaOut(BaseModel):
    id: int
    file_url: str
    media_type: MediaType

    class Config:
        from_attributes = True


class PresignIn(BaseModel):
    filename: str
    content_type: str


class PresignOut(BaseModel):
    upload_url: str
    public_url: str
    media_type: MediaType | None = None


class UploadedFile(BaseModel):
    public_url: str
    media_type: MediaType


class CompleteTaskIn(BaseModel):
    files: list[UploadedFile]
    substitute_task_id: int | None = None   # wildcard done instead of this task
