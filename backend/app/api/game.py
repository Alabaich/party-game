from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, GameState
from ..services.scheduler import start_game

router = APIRouter()


@router.get("/game", response_model=schemas.GameStatusOut)
def game_status(db: Session = Depends(get_db)):
    gs = db.get(GameState, 1)
    count = db.query(User).count()
    return schemas.GameStatusOut(
        exists=gs is not None,
        started=bool(gs and gs.tasks_assigned),
        started_at=gs.started_at if gs else None,
        player_count=count,
        server_time=datetime.utcnow(),
        places_revealed=bool(gs and gs.places_revealed),
    )


@router.post("/game/start", response_model=schemas.GameStatusOut)
def game_start(db: Session = Depends(get_db)):
    gs = start_game(db)
    if gs is None:
        raise HTTPException(400, "No players registered yet")
    count = db.query(User).count()
    return schemas.GameStatusOut(
        exists=True, started=gs.tasks_assigned, started_at=gs.started_at,
        player_count=count, server_time=datetime.utcnow(),
        places_revealed=bool(gs.places_revealed),
    )


@router.post("/game/reveal", response_model=schemas.GameStatusOut)
def game_reveal(db: Session = Depends(get_db)):
    gs = db.get(GameState, 1)
    if not gs:
        raise HTTPException(400, "Game not started")
    gs.places_revealed = True
    db.commit()
    count = db.query(User).count()
    return schemas.GameStatusOut(
        exists=True, started=gs.tasks_assigned, started_at=gs.started_at,
        player_count=count, server_time=datetime.utcnow(),
        places_revealed=True,
    )
