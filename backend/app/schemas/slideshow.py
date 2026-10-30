from datetime import datetime
from pydantic import BaseModel
from ..models.enums import MediaType


class SlideItem(BaseModel):
    id: str                       # "assignment-{id}-{media_id}" or "free-{id}"
    user_name: str
    task_description: str | None  # None for free uploads
    file_url: str
    media_type: MediaType
    completed_at: datetime
    is_free: bool
