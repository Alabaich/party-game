from sqlalchemy.orm import Session
from ..models import Game, Task, TaskType
from ..scripts.packs import PACKS


def load_pack_into_game(db: Session, game: Game, pack: str) -> int:
    _, tasks, wildcards = PACKS[pack]
    for desc, ttype, alco in tasks:
        db.add(Task(game_id=game.id, description=desc, type=ttype, is_alcoholic=alco))
    for desc in wildcards:
        db.add(Task(game_id=game.id, description=desc, type=TaskType.SOLO, is_universal=True))
    db.flush()
    return len(tasks) + len(wildcards)
