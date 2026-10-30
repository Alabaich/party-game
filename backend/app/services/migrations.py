"""Startup schema upgrades for databases created by earlier versions.

`create_all` only creates missing tables, it never adds columns, so every
column added after the first release is listed here. All statements are
idempotent (Postgres IF NOT EXISTS), so this runs on every start.
"""
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import Base, engine
from ..models import Game, GameState, User, Task
from .codes import new_game_code


UPGRADES = [
    "ALTER TABLE game_state ADD COLUMN IF NOT EXISTS places_revealed BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS game_id UUID REFERENCES games(id)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS answers JSON",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS game_id UUID REFERENCES games(id)",
    "ALTER TABLE games ADD COLUMN IF NOT EXISTS code VARCHAR(8)",
    "ALTER TABLE games ADD COLUMN IF NOT EXISTS settings JSON",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_games_code ON games (code)",
    "ALTER TABLE media ADD COLUMN IF NOT EXISTS hidden BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE free_media ADD COLUMN IF NOT EXISTS hidden BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_accepted_at TIMESTAMP",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_document_id INTEGER REFERENCES consent_documents(id)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_ip VARCHAR",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_user_agent VARCHAR",
    "CREATE INDEX IF NOT EXISTS ix_users_game_id ON users (game_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_game_id ON tasks (game_id)",
    "CREATE INDEX IF NOT EXISTS ix_assignments_user_id ON assignments (user_id)",
]

LEGACY_GAME_NAME = "Birthday Party (original)"


def upgrade_schema() -> None:
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        for stmt in UPGRADES:
            conn.execute(text(stmt))


def adopt_legacy_data(db: Session) -> None:
    """Wrap pre-multi-game rows (no game_id) into one Game, once."""
    orphans = db.query(User.id).filter(User.game_id.is_(None)).first() or \
        db.query(Task.id).filter(Task.game_id.is_(None)).first()
    if orphans:
        game = db.query(Game).filter(Game.name == LEGACY_GAME_NAME).first()
        if not game:
            gs = db.get(GameState, 1)
            game = Game(
                name=LEGACY_GAME_NAME, tasks_per_user=7,
                first_user_joined_at=gs.first_user_joined_at if gs else datetime.utcnow(),
                started_at=gs.started_at if gs else None,
                tasks_assigned=bool(gs and gs.tasks_assigned),
                places_revealed=bool(gs and gs.places_revealed),
                settings={"theme": "party", "alcohol_tasks": True,
                          "questions": [{"id": "drinking", "kind": "alcohol",
                                         "text": "Will you be drinking alcohol tonight?"}]},
            )
            db.add(game)
            db.flush()
        db.query(User).filter(User.game_id.is_(None)).update(
            {User.game_id: game.id}, synchronize_session=False)
        db.query(Task).filter(Task.game_id.is_(None)).update(
            {Task.game_id: game.id}, synchronize_session=False)
    for g in db.query(Game).filter(Game.code.is_(None)).all():
        g.code = new_game_code(db)
        db.flush()
    db.commit()
