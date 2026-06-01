from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .models import (
    User, GameState, Task, Assignment, Media, FreeMedia,
    AssignmentStatus, TaskType, MediaType,
)
from .r2 import make_presigned_put, upload_file_to_r2
from .scheduler import start_game
from .assignment import assign_tasks_for_latecomer

router = APIRouter()


# ---------- Registration ----------

@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    now = datetime.utcnow()

    existing = db.query(User).filter(User.name == payload.name.strip()).first()
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


# ---------- Dashboard ----------

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
        places_revealed=bool(gs and gs.places_revealed),
    )


# ---------- Media: task upload + complete ----------

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

    db.query(Media).filter(Media.assignment_id == assignment_id).delete()
    for f in payload.files:
        db.add(Media(assignment_id=assignment_id, file_url=f.public_url,
                     media_type=f.media_type))

    now = datetime.utcnow()
    a.status = AssignmentStatus.completed
    a.completed_at = now
    db.flush()

    _recalc_user_completion(db, user_id, now)

    if a.pair_id:
        partner = (
            db.query(Assignment)
            .filter(Assignment.pair_id == a.pair_id, Assignment.id != a.id)
            .first()
        )
        if partner and partner.status != AssignmentStatus.completed:
            partner.status = AssignmentStatus.completed
            partner.completed_at = now
            db.flush()
            _recalc_user_completion(db, partner.user_id, now)

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
    user = db.get(User, user_id)
    rows = db.query(Assignment).filter(Assignment.user_id == user_id).all()
    if rows and all(r.status == AssignmentStatus.completed for r in rows):
        user.completed_at = max(r.completed_at for r in rows)
    else:
        user.completed_at = None


# ---------- Download proxy ----------

@router.get("/download")
async def download_proxy(url: str):
    """Proxy download to force Content-Disposition: attachment for cross-origin files."""
    import httpx
    from fastapi.responses import StreamingResponse
    import urllib.parse
    # extract filename from url
    path = urllib.parse.urlparse(url).path
    filename = path.split("/")[-1] or "download"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        content_type = r.headers.get("content-type", "application/octet-stream")
        return StreamingResponse(
            iter([r.content]),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


# ---------- Free upload ----------

@router.post("/u/{user_id}/free-upload", response_model=schemas.PresignOut)
async def free_upload(user_id: str,
                      file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    """Upload media without a task — appears in slideshow with just player name."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Player not found")
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    public_url = upload_file_to_r2(file.filename or "upload", content_type, data)
    media_type = MediaType.video if (content_type or "").startswith("video") else MediaType.image
    db.add(FreeMedia(
        user_id=user_id,
        file_url=public_url,
        media_type=media_type,
    ))
    db.commit()
    return schemas.PresignOut(upload_url="", public_url=public_url)


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

    finished_list = [i for i in items if i["finished"]]
    in_progress = [i for i in items if not i["finished"]]

    finished_list.sort(key=lambda x: x["completed_at"])
    in_progress.sort(key=lambda x: x["completed_count"], reverse=True)

    for item in finished_list[:3]:
        item["is_winner"] = True

    return [schemas.LeaderboardItem(**i) for i in finished_list + in_progress]


# ---------- Slideshow ----------

@router.get("/slideshow", response_model=list[schemas.SlideItem])
def slideshow(db: Session = Depends(get_db)):
    out = []

    # task completions
    rows = (
        db.query(Assignment)
        .filter(Assignment.status == AssignmentStatus.completed)
        .order_by(Assignment.completed_at)
        .all()
    )
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

    # free uploads
    free_rows = db.query(FreeMedia).order_by(FreeMedia.uploaded_at).all()
    for fm in free_rows:
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

    # sort all by time
    out.sort(key=lambda x: x.completed_at)
    return out