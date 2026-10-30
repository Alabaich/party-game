from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import User, Task, Assignment, FreeMedia, AssignmentStatus

router = APIRouter()


@router.get("/slideshow", response_model=list[schemas.SlideItem])
def slideshow(
    db: Session = Depends(get_db),
    game_id: str | None = Query(
        None,
        description="If provided, only media from players in this game. "
                    "Omit for the legacy unscoped behavior (all media).",
    ),
):
    out = []

    # Optionally restrict to users belonging to one game.
    user_ids: set[str] | None = None
    if game_id is not None:
        user_ids = {
            uid for (uid,) in
            db.query(User.id).filter(User.game_id == game_id).all()
        }

    assignment_q = db.query(Assignment).filter(
        Assignment.status == AssignmentStatus.completed
    )
    rows = assignment_q.order_by(Assignment.completed_at).all()
    for a in rows:
        if not a.media:
            continue
        if user_ids is not None and a.user_id not in user_ids:
            continue
        u = db.get(User, a.user_id)
        t = db.get(Task, a.task_id)
        desc = t.description
        if a.target_user_id and "{target}" in desc:
            tgt = db.get(User, a.target_user_id)
            if tgt:
                desc = desc.replace("{target}", tgt.name)
        for m in a.media:
            out.append(schemas.SlideItem(
                id=f"assignment-{a.id}-{m.id}",
                user_name=u.name if u else "?",
                task_description=desc,
                file_url=m.file_url,
                media_type=m.media_type,
                completed_at=a.completed_at,
                is_free=False,
            ))

    free_rows = db.query(FreeMedia).order_by(FreeMedia.uploaded_at).all()
    for fm in free_rows:
        if user_ids is not None and fm.user_id not in user_ids:
            continue
        u = db.get(User, fm.user_id)
        out.append(schemas.SlideItem(
            id=f"free-{fm.id}",
            user_name=u.name if u else "?",
            task_description=None,
            file_url=fm.file_url,
            media_type=fm.media_type,
            completed_at=fm.uploaded_at,
            is_free=True,
        ))

    out.sort(key=lambda x: x.completed_at)
    return out
