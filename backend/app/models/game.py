from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from ._helpers import gen_uuid


class Game(Base):
    """One party-game event, owned by an Account.

    Two ids: `id` (UUID) is internal / admin-facing, `code` (5 chars) is the
    short public id used in links and QR codes: /g/{code}.
    `settings` holds everything the host configures (see schemas.GameSettings).
    """
    __tablename__ = "games"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    code = Column(String(8), unique=True, index=True, nullable=True)
    account_id = Column(
        UUID(as_uuid=False), ForeignKey("accounts.id"), nullable=True
    )
    name = Column(String, nullable=False, default="Party Quest")
    tasks_per_user = Column(Integer, nullable=False, default=7)
    settings = Column(JSON, nullable=True)

    # --- lifecycle ---
    # draft = host is still setting it up; nobody can join yet
    is_draft = Column(Boolean, nullable=False, default=False)
    first_user_joined_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    tasks_assigned = Column(Boolean, nullable=False, default=False)
    places_revealed = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    account = relationship("Account", back_populates="games")
    users = relationship("User", back_populates="game")
    tasks = relationship("Task", back_populates="game")
