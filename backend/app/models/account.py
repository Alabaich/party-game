from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from ._helpers import gen_uuid


class Account(Base):
    """A tenant — the person/org that registers on the platform and owns games.

    Auth is intentionally stubbed for now: the email + password_hash columns
    exist so the shape is settled, but no login flow is wired up yet. The
    immediate goal is just: an Account owns many Games.
    """
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # stub: fill when auth lands
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    games = relationship(
        "Game",
        back_populates="account",
        cascade="all, delete-orphan",
    )
