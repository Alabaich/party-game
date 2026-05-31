import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


class TaskType(enum.IntEnum):
    SOLO = 1       # Type 1
    TARGETED = 2   # Type 2
    PAIRED = 3     # Type 3


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    is_drinking = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Момент заливки доказу на 5-ту (останню) таску. NULL поки не завершив усе.
    completed_at = Column(DateTime, nullable=True)
    is_latecomer = Column(Boolean, nullable=False, default=False)

    assignments = relationship(
        "Assignment",
        back_populates="user",
        foreign_keys="Assignment.user_id",
        cascade="all, delete-orphan",
    )


class GameState(Base):
    """Singleton-рядок (id=1) — єдине джерело правди про старт гри.
    Гра стартує ВРУЧНУ натисканням кнопки СТАРТ на лідерборді.
    started_at фіксується в той момент і є точкою відліку тривалості."""
    __tablename__ = "game_state"

    id = Column(Integer, primary_key=True, default=1)
    first_user_joined_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)        # NULL поки не натиснули СТАРТ
    tasks_assigned = Column(Boolean, nullable=False, default=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    is_alcoholic = Column(Boolean, nullable=False, default=False)


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    # Type 2: ціль дії. Type 3: партнер по парі.
    target_user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    # Спільний ідентифікатор Type 3 пари (однаковий у двох рядків пари).
    pair_id = Column(UUID(as_uuid=False), nullable=True)
    status = Column(Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.pending)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="assignments", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    task = relationship("Task")
    media = relationship("Media", back_populates="assignment", cascade="all, delete-orphan")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    file_url = Column(String, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="media")
