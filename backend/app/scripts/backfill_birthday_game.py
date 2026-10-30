"""One-off backfill: wrap the existing single-game data into one Game object.

Run ONCE against the live DB that already holds the birthday party's data:
    python -m app.scripts.backfill_birthday_game

What it does:
  - creates a single Game row (carrying over the old GameState lifecycle fields),
  - stamps every existing User and Task with that game_id,
  - leaves all media/assignments untouched (they hang off users, already linked).

Idempotent: re-running detects the existing backfilled game and does nothing.
After this, /gallery still shows the same images, but the party now exists as a
real Game object you can scope future code against.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Game, GameState, User, Task

BIRTHDAY_GAME_NAME = "Birthday Party (original)"


def backfill(db: Session) -> Game:
    # already done?
    existing = db.query(Game).filter(Game.name == BIRTHDAY_GAME_NAME).first()
    if existing:
        print(f"Already backfilled — game {existing.id}")
        return existing

    gs = db.get(GameState, 1)
    game = Game(
        account_id=None,  # no tenant yet; attach later when you have an Account
        name=BIRTHDAY_GAME_NAME,
        tasks_per_user=7,
        first_user_joined_at=gs.first_user_joined_at if gs else datetime.utcnow(),
        started_at=gs.started_at if gs else None,
        tasks_assigned=bool(gs and gs.tasks_assigned),
        places_revealed=bool(gs and gs.places_revealed),
    )
    db.add(game)
    db.flush()  # get game.id

    n_users = db.query(User).filter(User.game_id.is_(None)).update(
        {User.game_id: game.id}, synchronize_session=False
    )
    n_tasks = db.query(Task).filter(Task.game_id.is_(None)).update(
        {Task.game_id: game.id}, synchronize_session=False
    )
    db.commit()
    db.refresh(game)
    print(f"Backfilled game {game.id}: {n_users} users, {n_tasks} tasks stamped.")
    return game


def main() -> None:
    db = SessionLocal()
    try:
        backfill(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
