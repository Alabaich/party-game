"""Player and TV-screen endpoints, addressed by the game's short code."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from .deps import get_db
from .. import schemas
from ..models import Game, User
from ..schemas.settings import load_settings
from ..services.assignment import assign_tasks_for_latecomer
from ..services.codes import normalize_code
from ..services.consent import ensure_consent_document
from ..services import views

router = APIRouter(prefix="/g/{code}")


def game_by_code(code: str, db: Session = Depends(get_db)) -> Game:
    game = db.query(Game).filter(Game.code == normalize_code(code)).first()
    if not game:
        raise HTTPException(404, "Game not found")
    return game


@router.get("", response_model=schemas.GamePublicOut)
def game_info(game: Game = Depends(game_by_code), db: Session = Depends(get_db)):
    return views.game_public(db, game)


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterIn, request: Request,
             game: Game = Depends(game_by_code), db: Session = Depends(get_db)):
    name = " ".join(payload.name.split())
    if not name:
        raise HTTPException(400, "Enter your name")
    if game.is_draft:
        raise HTTPException(403, "This game isn't open yet")
    if not views.can_join(game):
        raise HTTPException(403, "This game has already started")

    consent_doc = ensure_consent_document(db, game)
    if consent_doc and payload.consent_sha256 != consent_doc.sha256:
        # missing = not accepted; different = the text changed while they were reading
        raise HTTPException(400, "Please read and accept the Photo & Media Release")

    answers = {}
    is_drinking = True
    for q in load_settings(game.settings).questions:
        value = payload.answers.get(q.id)
        if q.kind in ("alcohol", "yesno"):
            if value is None:
                if q.required:
                    raise HTTPException(400, f"Please answer: {q.text}")
                continue
            value = bool(value)
            if q.kind == "alcohol":
                is_drinking = value
        elif q.kind == "choice":
            if value not in q.options:
                if q.required:
                    raise HTTPException(400, f"Please answer: {q.text}")
                continue
        elif q.kind == "text":
            value = str(value or "").strip()[:200]
            if q.numeric and value and not value.isdigit():
                raise HTTPException(400, f"Numbers only: {q.text}")
            if not value:
                if q.required:
                    raise HTTPException(400, f"Please answer: {q.text}")
                continue
        answers[q.id] = value

    taken = db.query(User.id).filter(
        User.game_id == game.id, func.lower(User.name) == name.lower()).first()
    if taken:
        raise HTTPException(400, "This name is already taken")

    now = datetime.utcnow()
    if game.first_user_joined_at is None:
        game.first_user_joined_at = now
    fwd = request.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() or (request.client.host if request.client else None)
    user = User(game_id=game.id, name=name, is_drinking=is_drinking, answers=answers,
                joined_at=now, is_latecomer=game.tasks_assigned)
    if consent_doc:
        user.consent_accepted_at = now
        user.consent_document_id = consent_doc.id
        user.consent_ip = ip
        user.consent_user_agent = request.headers.get("user-agent", "")[:500]
    db.add(user)
    db.commit()
    db.refresh(user)
    if user.is_latecomer:
        assign_tasks_for_latecomer(db, game, user)
    return user


@router.get("/players", response_model=list[schemas.PlayerListItem])
def players(game: Game = Depends(game_by_code), db: Session = Depends(get_db)):
    return db.query(User).filter(User.game_id == game.id).order_by(User.name).all()


@router.get("/leaderboard", response_model=list[schemas.LeaderboardItem])
def leaderboard(game: Game = Depends(game_by_code), db: Session = Depends(get_db)):
    return views.leaderboard(db, game)


@router.get("/slideshow", response_model=list[schemas.SlideItem])
def slideshow(game: Game = Depends(game_by_code), db: Session = Depends(get_db)):
    return views.slideshow(db, game)
