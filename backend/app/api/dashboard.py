from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..services.text import render_task
from ..models import User, GameState, Task, Assignment

router = APIRouter()


@router.get("/u/{user_id}", response_model=schemas.DashboardOut)
def dashboard(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")

    gs = db.get(GameState, 1)
    started = bool(gs and gs.tasks_assigned)
    if user.is_latecomer:
        started = True

    players = db.query(User).order_by(User.name).all()

    assignments_out = []
    if started or user.is_latecomer:
        rows = db.query(Assignment).filter(Assignment.user_id == user_id).all()
        for a in rows:
            t = db.get(Task, a.task_id)
            desc = t.description
            target_name = None
            if a.target_user_id:
                tgt = db.get(User, a.target_user_id)
                target_name = tgt.name if tgt else None
            desc = render_task(desc, target_name)
            assignments_out.append(schemas.AssignmentOut(
                id=a.id, task_id=a.task_id, description=desc,
                type=t.type, is_alcoholic=t.is_alcoholic,
                target_user_name=target_name, pair_id=a.pair_id,
                status=a.status, completed_at=a.completed_at,
                media=[schemas.MediaOut.model_validate(m) for m in a.media],
            ))

    return schemas.DashboardOut(
        user=user,
        game_started=bool(started or user.is_latecomer),
        started_at=gs.started_at if gs else None,
        server_time=datetime.utcnow(),
        players=players,
        assignments=assignments_out,
        places_revealed=bool(gs and gs.places_revealed),
    )
