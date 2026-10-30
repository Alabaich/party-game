from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class ConsentDocument(Base):
    """Every version of a game's consent text players ever agreed to.
    Kept forever so we can show exactly what someone accepted."""
    __tablename__ = "consent_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(UUID(as_uuid=False), ForeignKey("games.id"), nullable=False, index=True)
    sha256 = Column(String(64), nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
