from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, GameState, Assignment, AssignmentStatus

router = APIRouter()


@router.get("/leaderboard", response_model=list[schemas.LeaderboardItem])
def leaderboard(db: Session = Depends(get_db)):
    gs = db.get(GameState, 1)
    started_at = gs.started_at if gs else None

    users = db.query(User).all()
    items = []
    for u in users:
        rows = db.query(Assignment).filter(Assignment.user_id == u.id).all()
        done = sum(1 for r in rows if r.status == AssignmentStatus.completed)
        finished = bool(rows) and done == len(rows)
        duration = None
        if finished and u.completed_at and started_at:
            duration = int((u.completed_at - started_at).total_seconds())
        items.append({
            "user_id": u.id, "name": u.name,
            "completed_count": done, "finished": finished,
            "completed_at": u.completed_at, "duration_seconds": duration,
            "is_winner": False,
        })

    finished_list = [i for i in items if i["finished"]]
    in_progress = [i for i in items if not i["finished"]]

    finished_list.sort(key=lambda x: x["completed_at"])
    in_progress.sort(key=lambda x: x["completed_count"], reverse=True)

    for item in finished_list[:3]:
        item["is_winner"] = True

    return [schemas.LeaderboardItem(**i) for i in finished_list + in_progress]
