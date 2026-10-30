"""Game start — manual (host presses START).
Tasks are assigned under a row lock on the game, so a double click can't
assign twice."""
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Game
from .assignment import assign_tasks_for_all


def start_game(db: Session, game_id: str) -> Game:
    """Idempotent: starting an already started game changes nothing."""
    q = db.query(Game).filter(Game.id == game_id)
    if db.bind.dialect.name == "postgresql":
        q = q.with_for_update()
    game = q.first()
    if game.tasks_assigned:
        return game
    game.started_at = datetime.utcnow()
    assign_tasks_for_all(db, game)
    game.tasks_assigned = True
    db.commit()
    db.refresh(game)
    return game
