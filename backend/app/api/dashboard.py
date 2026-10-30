from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, Game, Assignment, Task
from ..schemas.settings import load_settings
from ..services.auth import player_key
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

    used = sum(1 for a in assignments if a.substitute_description)
    wildcards = db.query(Task).filter(Task.game_id == game.id,
                                      Task.is_universal == True).order_by(Task.id).all()  # noqa: E712
    users = db.query(User).filter(User.game_id == game.id).order_by(User.name).all()
    return schemas.DashboardOut(
        user=user,
        user_key=player_key(user.id),
        game=views.game_public(db, game),
        players=[schemas.PlayerListItem(key=player_key(u.id), name=u.name) for u in users],
        assignments=assignments,
        wildcards=[schemas.Wildcard(id=t.id, description=t.description) for t in wildcards],
        wildcards_left=max(0, load_settings(game.settings).max_wildcards - used),
    )


@router.get("/u/{user_id}/media", response_model=list[schemas.SlideItem])
def my_media(user_id: str, db: Session = Depends(get_db)):
    """A player's own uploads (works even when the game gallery is private)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")
    return views.slideshow(db, db.get(Game, user.game_id), only_user=user.id)
