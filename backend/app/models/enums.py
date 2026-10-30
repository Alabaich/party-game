import enum


class TaskType(enum.IntEnum):
    SOLO = 1
    TARGETED = 2
    PAIRED = 3


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"
