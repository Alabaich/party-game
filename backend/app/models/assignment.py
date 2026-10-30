from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .enums import AssignmentStatus


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    target_user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    pair_id = Column(UUID(as_uuid=False), nullable=True)
    status = Column(
        Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.pending
    )
    completed_at = Column(DateTime, nullable=True)

    user = relationship(
        "User", back_populates="assignments", foreign_keys=[user_id]
    )
    target_user = relationship("User", foreign_keys=[target_user_id])
    task = relationship("Task")
    media = relationship(
        "Media", back_populates="assignment", cascade="all, delete-orphan"
    )
