"""Host endpoints. Every game route checks that the game belongs to the caller."""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from .deps import get_db, current_account, owned_game
from .. import schemas
from ..models import Account, Game, Task, User, Assignment, Media, FreeMedia, ConsentDocument
from ..schemas.settings import default_settings, Prize, load_settings
from ..scripts.packs import PACKS
from ..services import views
from ..services.codes import new_game_code
from ..services.scheduler import start_game
from ..services.tasks import load_pack_into_game
from ..services.consent import ensure_consent_document
from ..services.storage import check_storage
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/storage-check")
async def storage_check(_: Account = Depends(current_account)):
    ok, message = await run_in_threadpool(check_storage)
    return {"ok": ok, "message": message}


# ---------- games ----------

@router.get("/games", response_model=list[schemas.GameAdminOut])
def list_games(acc: Account = Depends(current_account), db: Session = Depends(get_db)):
    games = (db.query(Game).filter(Game.account_id == acc.id)
             .order_by(Game.created_at.desc()).all())
    return [views.game_admin(db, g) for g in games]


@router.post("/games", response_model=schemas.GameAdminOut)
def create_game(payload: schemas.GameCreateIn, acc: Account = Depends(current_account),
                db: Session = Depends(get_db)):
    theme = payload.theme if payload.theme in ("party", "halloween", "diwali") else "party"
    pack = payload.pack or theme
    if pack not in PACKS:
        raise HTTPException(400, "Unknown task pack")
    s = default_settings(theme)
    s.prizes = [Prize(place="1", title=""), Prize(place="2", title=""),
                Prize(place="3", title="")]
    game = Game(account_id=acc.id, name=payload.name, code=new_game_code(db),
                settings=s.model_dump(), is_draft=True)
    db.add(game)
    db.flush()
    load_pack_into_game(db, game, pack)
    ensure_consent_document(db, game)
    db.commit()
    db.refresh(game)
    return views.game_admin(db, game)


@router.get("/games/{game_id}", response_model=schemas.GameAdminOut)
def get_game(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    return views.game_admin(db, game)


@router.patch("/games/{game_id}", response_model=schemas.GameAdminOut)
def update_game(payload: schemas.GameUpdateIn, game: Game = Depends(owned_game),
                db: Session = Depends(get_db)):
    if payload.name is not None:
        game.name = payload.name
    if payload.tasks_per_user is not None:
        if game.tasks_assigned and payload.tasks_per_user != game.tasks_per_user:
            raise HTTPException(409, "Tasks per player can't change after the start")
        game.tasks_per_user = payload.tasks_per_user
    if payload.settings is not None:
        ids = [q.id for q in payload.settings.questions]
        if len(ids) != len(set(ids)):
            raise HTTPException(400, "Question ids must be unique")
        game.settings = payload.settings.model_dump()
        ensure_consent_document(db, game)
    db.commit()
    db.refresh(game)
    return views.game_admin(db, game)


@router.post("/games/{game_id}/publish", response_model=schemas.GameAdminOut)
def publish(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    if not db.query(Task.id).filter(Task.game_id == game.id).first():
        raise HTTPException(400, "Add tasks first")
    game.is_draft = False
    db.commit()
    return views.game_admin(db, game)


@router.post("/games/{game_id}/unpublish", response_model=schemas.GameAdminOut)
def unpublish(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    if game.tasks_assigned:
        raise HTTPException(409, "The game has already started")
    game.is_draft = True
    db.commit()
    return views.game_admin(db, game)


@router.post("/games/{game_id}/start", response_model=schemas.GameAdminOut)
def start(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    if game.is_draft:
        raise HTTPException(400, "Publish the game first")
    if views.player_count(db, game) == 0:
        raise HTTPException(400, "No players yet")
    if not db.query(Task.id).filter(Task.game_id == game.id).first():
        raise HTTPException(400, "Add tasks first")
    game = start_game(db, game.id)
    return views.game_admin(db, game)


@router.post("/games/{game_id}/reveal", response_model=schemas.GameAdminOut)
def reveal(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    if not game.tasks_assigned:
        raise HTTPException(400, "Game hasn't started")
    game.places_revealed = True
    db.commit()
    return views.game_admin(db, game)


# ---------- players ----------

@router.get("/games/{game_id}/players", response_model=list[schemas.PlayerAdminOut])
def players(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    lb = {i.user_id: i for i in views.leaderboard(db, game, public=False)}
    users = db.query(User).filter(User.game_id == game.id).order_by(User.joined_at).all()
    return [schemas.PlayerAdminOut(
        id=u.id, name=u.name, answers=u.answers, is_latecomer=u.is_latecomer,
        consent_accepted_at=u.consent_accepted_at,
        completed_count=lb[u.id].completed_count, total=lb[u.id].total,
    ) for u in users]


@router.get("/games/{game_id}/consents.csv")
def consents_csv(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    """Record of who accepted which version of the release, and when (UTC)."""
    questions = load_settings(game.settings).questions
    docs = {d.id: d for d in db.query(ConsentDocument).filter(ConsentDocument.game_id == game.id)}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", *[q.text for q in questions], "consent_accepted_at_utc",
                "consent_title", "consent_sha256", "ip", "user_agent"])
    for u in db.query(User).filter(User.game_id == game.id).order_by(User.joined_at):
        d = docs.get(u.consent_document_id)
        w.writerow([u.name, *[(u.answers or {}).get(q.id, "") for q in questions],
                    u.consent_accepted_at.isoformat() if u.consent_accepted_at else "",
                    d.title if d else "", d.sha256 if d else "",
                    u.consent_ip or "", u.consent_user_agent or ""])
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="consents-{game.code}.csv"'})


@router.get("/games/{game_id}/consent/{sha256}")
def consent_document(sha256: str, game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    d = (db.query(ConsentDocument)
         .filter(ConsentDocument.game_id == game.id, ConsentDocument.sha256 == sha256).first())
    if not d:
        raise HTTPException(404, "Not found")
    return {"title": d.title, "body": d.body, "created_at": d.created_at, "sha256": d.sha256}


@router.get("/games/{game_id}/leaderboard", response_model=list[schemas.LeaderboardItem])
def admin_leaderboard(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    return views.leaderboard(db, game, public=False)


# ---------- tasks ----------

@router.get("/packs", response_model=list[schemas.PackOut])
def packs(_: Account = Depends(current_account)):
    return [schemas.PackOut(id=k, title=v[0], task_count=len(v[1]) + len(v[2])) for k, v in PACKS.items()]


def _tasks_out(db: Session, game: Game) -> list[schemas.TaskOut]:
    used = dict(db.query(Assignment.task_id, func.count())
                .join(Task, Task.id == Assignment.task_id)
                .filter(Task.game_id == game.id).group_by(Assignment.task_id).all())
    tasks = db.query(Task).filter(Task.game_id == game.id).order_by(Task.type, Task.id).all()
    subs = dict(db.query(Assignment.substitute_task_id, func.count())
                .join(Task, Task.id == Assignment.substitute_task_id)
                .filter(Task.game_id == game.id).group_by(Assignment.substitute_task_id).all())
    return [schemas.TaskOut(id=t.id, description=t.description, type=t.type,
                            is_alcoholic=t.is_alcoholic, is_universal=t.is_universal,
                            assigned_count=used.get(t.id, 0) + subs.get(t.id, 0))
            for t in tasks]


@router.get("/games/{game_id}/tasks", response_model=list[schemas.TaskOut])
def list_tasks(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    return _tasks_out(db, game)


@router.post("/games/{game_id}/tasks", response_model=list[schemas.TaskOut])
def add_task(payload: schemas.TaskIn, game: Game = Depends(owned_game),
             db: Session = Depends(get_db)):
    db.add(Task(game_id=game.id, **payload.model_dump()))
    db.commit()
    return _tasks_out(db, game)


def _own_task(db: Session, game: Game, task_id: int) -> Task:
    t = db.get(Task, task_id)
    if not t or t.game_id != game.id:
        raise HTTPException(404, "Task not found")
    return t


@router.put("/games/{game_id}/tasks/{task_id}", response_model=list[schemas.TaskOut])
def edit_task(task_id: int, payload: schemas.TaskIn, game: Game = Depends(owned_game),
              db: Session = Depends(get_db)):
    t = _own_task(db, game, task_id)
    if game.tasks_assigned and payload.type != t.type:
        raise HTTPException(409, "Task type can't change after the start")
    if game.tasks_assigned and payload.is_universal != t.is_universal and \
            db.query(Assignment.id).filter(Assignment.task_id == t.id).first():
        raise HTTPException(409, "This task is already assigned; it can't become a wildcard")
    t.description, t.type, t.is_alcoholic = payload.description, payload.type, payload.is_alcoholic
    t.is_universal = payload.is_universal
    db.commit()
    return _tasks_out(db, game)


@router.delete("/games/{game_id}/tasks/{task_id}", response_model=list[schemas.TaskOut])
def delete_task(task_id: int, game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    t = _own_task(db, game, task_id)
    if db.query(Assignment.id).filter((Assignment.task_id == t.id) |
                                      (Assignment.substitute_task_id == t.id)).first():
        raise HTTPException(409, "This task is already assigned to players")
    db.delete(t)
    db.commit()
    return _tasks_out(db, game)


@router.post("/games/{game_id}/tasks/load-pack", response_model=list[schemas.TaskOut])
def load_pack(pack: str, replace: bool = False, game: Game = Depends(owned_game),
              db: Session = Depends(get_db)):
    if pack not in PACKS:
        raise HTTPException(400, "Unknown task pack")
    if replace:
        if game.tasks_assigned:
            raise HTTPException(409, "Can't replace tasks after the start")
        db.query(Task).filter(Task.game_id == game.id).delete()
    load_pack_into_game(db, game, pack)
    db.commit()
    return _tasks_out(db, game)


# ---------- media moderation ----------

@router.get("/games/{game_id}/media", response_model=list[schemas.SlideItem])
def media(game: Game = Depends(owned_game), db: Session = Depends(get_db)):
    return views.slideshow(db, game, include_hidden=True)


@router.post("/games/{game_id}/media/{kind}/{media_id}/hidden")
def set_hidden(kind: str, media_id: int, hidden: bool, game: Game = Depends(owned_game),
               db: Session = Depends(get_db)):
    if kind == "task":
        row = (db.query(Media).join(Assignment, Assignment.id == Media.assignment_id)
               .join(User, User.id == Assignment.user_id)
               .filter(Media.id == media_id, User.game_id == game.id).first())
    elif kind == "free":
        row = (db.query(FreeMedia).join(User, User.id == FreeMedia.user_id)
               .filter(FreeMedia.id == media_id, User.game_id == game.id).first())
    else:
        row = None
    if not row:
        raise HTTPException(404, "Media not found")
    row.hidden = hidden
    db.commit()
    return {"ok": True, "hidden": hidden}
