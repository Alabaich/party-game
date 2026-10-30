from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, Game, Assignment
from ..services import views

router = APIRouter()


@router.get("/u/{user_id}", response_model=schemas.DashboardOut)
def dashboard(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")
    game = db.get(Game, user.game_id)

    assignments = []
    if game.tasks_assigned or user.is_latecomer:
        rows = (db.query(Assignment).filter(Assignment.user_id == user_id)
                .order_by(Assignment.id).all())
        assignments = [views.assignment_out(db, game, a) for a in rows]

    return schemas.DashboardOut(
        user=user,
        game=views.game_public(db, game),
        players=db.query(User).filter(User.game_id == game.id).order_by(User.name).all(),
        assignments=assignments,
    )
