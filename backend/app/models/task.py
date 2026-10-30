from sqlalchemy import Column, String, Boolean, Integer, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .enums import TaskType


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(UUID(as_uuid=False), ForeignKey("games.id"), nullable=True)
    description = Column(Text, nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    is_alcoholic = Column(Boolean, nullable=False, default=False)

    game = relationship("Game", back_populates="tasks")
