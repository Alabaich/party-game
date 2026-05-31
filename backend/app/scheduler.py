"""Старт гри — ручний (кнопка СТАРТ на лідерборді).
Призначення тасок відбувається атомарно під блокуванням singleton-рядка,
щоб подвійне натискання не призначило таски двічі."""
from datetime import datetime
from sqlalchemy.orm import Session
from .models import GameState
from .assignment import assign_tasks_for_all


def start_game(db: Session) -> GameState:
    """Викликається кнопкою СТАРТ. Ідемпотентно: повторний виклик нічого не псує."""
    is_pg = db.bind.dialect.name == "postgresql"
    q = db.query(GameState).filter(GameState.id == 1)
    if is_pg:
        q = q.with_for_update()
    gs = q.first()
    if not gs:
        return None  # ще ніхто не зареєструвався
    if gs.tasks_assigned:
        return gs  # вже стартували

    gs.started_at = datetime.utcnow()
    assign_tasks_for_all(db)
    gs.tasks_assigned = True
    db.commit()
    db.refresh(gs)
    return gs
