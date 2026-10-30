from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .enums import MediaType


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    file_url = Column(String, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="media")


class FreeMedia(Base):
    """Media uploaded without a task — appears in slideshow with just player name."""
    __tablename__ = "free_media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    file_url = Column(String, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="free_media")
