from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from ._helpers import gen_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    game_id = Column(UUID(as_uuid=False), ForeignKey("games.id"), nullable=True)
    name = Column(String, nullable=False)
    is_drinking = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_latecomer = Column(Boolean, nullable=False, default=False)
    # answers to the game's pre-game questions: {question_id: value}
    answers = Column(JSON, nullable=True)
    # proof of the media release: when (server time), which text, from where
    consent_accepted_at = Column(DateTime, nullable=True)
    consent_document_id = Column(Integer, ForeignKey("consent_documents.id"), nullable=True)
    consent_ip = Column(String, nullable=True)
    consent_user_agent = Column(String, nullable=True)

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
