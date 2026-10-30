from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from ._helpers import gen_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    # nullable for now: existing single-game users have no game_id yet
    game_id = Column(UUID(as_uuid=False), ForeignKey("games.id"), nullable=True)
    name = Column(String, nullable=False)
    is_drinking = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_latecomer = Column(Boolean, nullable=False, default=False)

    game = relationship("Game", back_populates="users")
    assignments = relationship(
        "Assignment",
        back_populates="user",
        foreign_keys="Assignment.user_id",
        cascade="all, delete-orphan",
    )
    free_media = relationship(
        "FreeMedia",
        back_populates="user",
        cascade="all, delete-orphan",
    )
