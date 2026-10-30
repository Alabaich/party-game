from pydantic import BaseModel, Field
from ..models.enums import TaskType


class TaskIn(BaseModel):
    description: str = Field(min_length=3, max_length=500)
    type: TaskType
    is_alcoholic: bool = False


class TaskOut(TaskIn):
    id: int
    assigned_count: int = 0
