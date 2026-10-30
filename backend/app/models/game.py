from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from ._helpers import gen_uuid


class Game(Base):
    """One party-game event.

    This is the object the *entire current project* collapses into: what used
    to be the singleton GameState row is now one Game row. The lifecycle fields
    (started_at, tasks_assigned, places_revealed, first_user_joined_at) are
    folded in here rather than kept in a separate 1:1 table.

    Owned by an Account. Game-scoped rows (users, tasks, assignments, free
    media) carry a nullable game_id for now so existing single-game data and
    code keep working; tightening to NOT NULL is the next migration step.
    """
    __tablename__ = "games"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(
        UUID(as_uuid=False), ForeignKey("accounts.id"), nullable=True
    )
    name = Column(String, nullable=False, default="Party Quest")
    tasks_per_user = Column(Integer, nullable=False, default=7)

    # --- lifecycle (was GameState) ---
    first_user_joined_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    tasks_assigned = Column(Boolean, nullable=False, default=False)
    places_revealed = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    account = relationship("Account", back_populates="games")
    users = relationship("User", back_populates="game")
    tasks = relationship("Task", back_populates="game")
