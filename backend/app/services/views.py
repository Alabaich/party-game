"""Builders shared by player, TV and host endpoints."""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import schemas
from ..models import (
    Game, User, Task, Assignment, Media, FreeMedia, AssignmentStatus,
)
from ..schemas.settings import load_settings
from .text import render_task
from .consent import current_consent_hash
from .auth import player_key


def player_count(db: Session, game: Game) -> int:
    return db.query(func.count(User.id)).filter(User.game_id == game.id).scalar()


def can_join(game: Game) -> bool:
    if game.is_draft:
        return False
    return not game.tasks_assigned or load_settings(game.settings).allow_late_join


def game_public(db: Session, game: Game) -> schemas.GamePublicOut:
    return schemas.GamePublicOut(
        code=game.code, name=game.name, settings=load_settings(game.settings),
        tasks_per_user=game.tasks_per_user, is_draft=game.is_draft,
        started=game.tasks_assigned, started_at=game.started_at,
        places_revealed=game.places_revealed,
        player_count=player_count(db, game), can_join=can_join(game),
        consent_sha256=current_consent_hash(game),
        server_time=datetime.utcnow(),
    )


def game_admin(db: Session, game: Game) -> schemas.GameAdminOut:
    pub = game_public(db, game)
    task_count = db.query(func.count(Task.id)).filter(Task.game_id == game.id).scalar()
    return schemas.GameAdminOut(**pub.model_dump(), id=game.id,
                                task_count=task_count, created_at=game.created_at)


def target_hint(game: Game, user: User | None) -> str | None:
    """Answers to 'choice' questions (e.g. building) help others find this player."""
    if not user or not user.answers:
        return None
    parts = [str(user.answers[q.id]) for q in load_settings(game.settings).questions
             if q.kind == "choice" and not q.private and user.answers.get(q.id)]
    return " · ".join(parts) or None


def assignment_out(db: Session, game: Game, a: Assignment) -> schemas.AssignmentOut:
    t = db.get(Task, a.task_id)
    tgt = db.get(User, a.target_user_id) if a.target_user_id else None
    sub = db.get(Task, a.substitute_task_id) if a.substitute_task_id else None
    return schemas.AssignmentOut(
        substitute_description=sub.description if sub else None,
        id=a.id, task_id=a.task_id,
        description=render_task(t.description, tgt.name if tgt else None),
        type=t.type, is_alcoholic=t.is_alcoholic,
        target_user_name=tgt.name if tgt else None, target_hint=target_hint(game, tgt),
        pair_id=a.pair_id, status=a.status, completed_at=a.completed_at,
        media=[schemas.MediaOut.model_validate(m) for m in a.media],
    )


def leaderboard(db: Session, game: Game, public: bool = True) -> list[schemas.LeaderboardItem]:
    users = db.query(User).filter(User.game_id == game.id).all()
    counts: dict[str, list[int]] = {u.id: [0, 0] for u in users}
    rows = (db.query(Assignment.user_id, Assignment.status, func.count())
            .join(User, User.id == Assignment.user_id)
            .filter(User.game_id == game.id)
            .group_by(Assignment.user_id, Assignment.status).all())
    for uid, status, n in rows:
        counts[uid][1] += n
        if status == AssignmentStatus.completed:
            counts[uid][0] += n

    items = []
    for u in users:
        done, total = counts[u.id]
        finished = total > 0 and done == total
        duration = None
        if finished and u.completed_at and game.started_at:
            duration = int((u.completed_at - game.started_at).total_seconds())
        items.append(schemas.LeaderboardItem(
            user_id=player_key(u.id) if public else u.id,
            name=u.name, completed_count=done, total=total,
            finished=finished, completed_at=u.completed_at if finished else None,
            duration_seconds=duration, is_winner=False,
        ))
    finished_list = sorted((i for i in items if i.finished), key=lambda i: i.completed_at)
    in_progress = sorted((i for i in items if not i.finished),
                         key=lambda i: (-i.completed_count, i.name.lower()))
    for i in finished_list[:3]:
        i.is_winner = True
    return finished_list + in_progress


def slideshow(db: Session, game: Game, include_hidden: bool = False,
              only_user: str | None = None) -> list[schemas.SlideItem]:
    out = []
    names = {u.id: u.name for u in db.query(User).filter(User.game_id == game.id)}
    q = (db.query(Media, Assignment)
         .join(Assignment, Assignment.id == Media.assignment_id)
         .join(User, User.id == Assignment.user_id)
         .filter(User.game_id == game.id))
    if not include_hidden:
        q = q.filter(Media.hidden == False)  # noqa: E712
    if only_user:
        q = q.filter(Assignment.user_id == only_user)
    tasks = {t.id: t for t in db.query(Task).filter(Task.game_id == game.id)}
    for m, a in q.all():
        t = tasks.get(a.substitute_task_id or a.task_id)
        desc = render_task(t.description, names.get(a.target_user_id)) if t else None
        out.append(schemas.SlideItem(
            id=f"assignment-{a.id}-{m.id}", media_id=m.id,
            user_name=names.get(a.user_id, "?"), task_description=desc,
            file_url=m.file_url, media_type=m.media_type,
            completed_at=m.uploaded_at, is_free=False, hidden=m.hidden,
        ))
    fq = (db.query(FreeMedia).join(User, User.id == FreeMedia.user_id)
          .filter(User.game_id == game.id))
    if not include_hidden:
        fq = fq.filter(FreeMedia.hidden == False)  # noqa: E712
    if only_user:
        fq = fq.filter(FreeMedia.user_id == only_user)
    for fm in fq.all():
        out.append(schemas.SlideItem(
            id=f"free-{fm.id}", media_id=fm.id,
            user_name=names.get(fm.user_id, "?"), task_description=None,
            file_url=fm.file_url, media_type=fm.media_type,
            completed_at=fm.uploaded_at, is_free=True, hidden=fm.hidden,
        ))
    out.sort(key=lambda x: x.completed_at)
    return out
