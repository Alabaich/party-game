from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean
from ..database import Base


class GameState(Base):
    """LEGACY singleton (id=1). Still the source of truth for the current
    single-game flow. Being superseded by Game — kept this step so existing
    routes/scheduler keep working unchanged.
    """
    __tablename__ = "game_state"

    id = Column(Integer, primary_key=True, default=1)
    first_user_joined_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    tasks_assigned = Column(Boolean, nullable=False, default=False)
    places_revealed = Column(Boolean, nullable=False, default=False)
