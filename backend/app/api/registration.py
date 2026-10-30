from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, GameState
from ..services.assignment import assign_tasks_for_latecomer

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    now = datetime.utcnow()

    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "Enter your name")
    existing = db.query(User).filter(func.lower(User.name) == name.lower()).first()
    if existing:
        raise HTTPException(400, "This name is already taken")

    gs = db.get(GameState, 1)
    is_latecomer = False
    if gs is None:
        gs = GameState(id=1, first_user_joined_at=now,
                       started_at=None, tasks_assigned=False, places_revealed=False)
        db.add(gs)
        db.flush()
    else:
        if gs.tasks_assigned:
            is_latecomer = True

    user = User(
        name=name,
        is_drinking=payload.is_drinking,
        joined_at=now,
        is_latecomer=is_latecomer,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_latecomer:
        assign_tasks_for_latecomer(db, user)

    return user


@router.get("/players", response_model=list[schemas.PlayerListItem])
def list_players(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name).all()
