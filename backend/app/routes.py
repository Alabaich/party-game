from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
from . import models, schemas
from .models import (
    User, GameState, Task, Assignment, Media,
    AssignmentStatus, TaskType,
)
from .r2 import make_presigned_put, upload_file_to_r2
from .scheduler import start_game
from .assignment import assign_tasks_for_latecomer

router = APIRouter()


# ---------- Registration ----------

@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    gs = db.get(GameState, 1)

    is_latecomer = False
    if gs is None:
        # найперший юзер — створюємо GameState (гра ще НЕ стартувала)
        gs = GameState(id=1, first_user_joined_at=now,
                       started_at=None, tasks_assigned=False)
        db.add(gs)
        db.flush()
    else:
        # якщо гра вже стартувала — цей юзер латекомер
        if gs.tasks_assigned:
            is_latecomer = True

    user = User(
        name=payload.name.strip(),
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
    """Для кнопки 'увійти як наявний гравець'."""
    return db.query(User).order_by(User.name).all()


# ---------- Game control ----------

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
    )


# ---------- Dashboard ----------

@router.get("/u/{user_id}", response_model=schemas.DashboardOut)
def dashboard(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")

    gs = db.get(GameState, 1)
    started = bool(gs and gs.tasks_assigned)
    # латекомеру таски вже призначені — для нього гра завжди "почалась"
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
                if "{target}" in desc and target_name:
                    desc = desc.replace("{target}", target_name)
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
    )


# ---------- Media: presign + complete ----------

@router.post("/u/{user_id}/assignments/{assignment_id}/presign",
             response_model=schemas.PresignOut)
def presign(user_id: str, assignment_id: int,
            payload: schemas.PresignIn, db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Assignment not found")
    upload_url, public_url = make_presigned_put(payload.filename, payload.content_type)
    return schemas.PresignOut(upload_url=upload_url, public_url=public_url)


@router.post("/u/{user_id}/assignments/{assignment_id}/upload",
             response_model=schemas.PresignOut)
async def upload_proxy(user_id: str, assignment_id: int,
                       file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    """Proxy file upload: browser → backend → R2. Avoids CORS issues."""
    a = db.get(Assignment, assignment_id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Assignment not found")
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    public_url = upload_file_to_r2(file.filename or "upload", content_type, data)
    return schemas.PresignOut(upload_url="", public_url=public_url)


@router.post("/u/{user_id}/assignments/{assignment_id}/complete",
             response_model=schemas.AssignmentOut)
def complete_task(user_id: str, assignment_id: int,
                  payload: schemas.CompleteTaskIn, db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a or a.user_id != user_id:
        raise HTTPException(404, "Assignment not found")

    # replace semantics: clear old media for this assignment
    db.query(Media).filter(Media.assignment_id == assignment_id).delete()
    for f in payload.files:
        db.add(Media(assignment_id=assignment_id, file_url=f.public_url,
                     media_type=f.media_type))

    now = datetime.utcnow()
    a.status = AssignmentStatus.completed
    a.completed_at = now
    db.flush()

    _recalc_user_completion(db, user_id, now)
    db.commit()
    db.refresh(a)

    t = db.get(Task, a.task_id)
    desc = t.description
    target_name = None
    if a.target_user_id:
        tgt = db.get(User, a.target_user_id)
        target_name = tgt.name if tgt else None
        if "{target}" in desc and target_name:
            desc = desc.replace("{target}", target_name)
    return schemas.AssignmentOut(
        id=a.id, task_id=a.task_id, description=desc, type=t.type,
        is_alcoholic=t.is_alcoholic, target_user_name=target_name,
        pair_id=a.pair_id, status=a.status, completed_at=a.completed_at,
        media=[schemas.MediaOut.model_validate(m) for m in a.media],
    )


def _recalc_user_completion(db: Session, user_id: str, now: datetime):
    """Якщо всі 5 тасок юзера completed — ставимо User.completed_at
    (момент останньої заливки). Інакше скидаємо."""
    user = db.get(User, user_id)
    rows = db.query(Assignment).filter(Assignment.user_id == user_id).all()
    if rows and all(r.status == AssignmentStatus.completed for r in rows):
        # час фінішу = найпізніший completed_at серед тасок
        user.completed_at = max(r.completed_at for r in rows)
    else:
        user.completed_at = None


# ---------- Leaderboard ----------

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

    finished = [i for i in items if i["finished"]]
    in_progress = [i for i in items if not i["finished"]]

    finished.sort(key=lambda x: x["completed_at"])      # раніше фініш = вище
    in_progress.sort(key=lambda x: x["completed_count"], reverse=True)

    for item in finished[:3]:
        item["is_winner"] = True

    return [schemas.LeaderboardItem(**i) for i in finished + in_progress]


# ---------- Slideshow ----------

@router.get("/slideshow", response_model=list[schemas.SlideItem])
def slideshow(db: Session = Depends(get_db)):
    rows = (
        db.query(Assignment)
        .filter(Assignment.status == AssignmentStatus.completed)
        .order_by(Assignment.completed_at)
        .all()
    )
    out = []
    for a in rows:
        if not a.media:
            continue
        u = db.get(User, a.user_id)
        t = db.get(Task, a.task_id)
        desc = t.description
        if a.target_user_id and "{target}" in desc:
            tgt = db.get(User, a.target_user_id)
            if tgt:
                desc = desc.replace("{target}", tgt.name)
        out.append(schemas.SlideItem(
            assignment_id=a.id, user_name=u.name if u else "?",
            task_description=desc,
            media=[schemas.MediaOut.model_validate(m) for m in a.media],
            completed_at=a.completed_at,
        ))
    return out
