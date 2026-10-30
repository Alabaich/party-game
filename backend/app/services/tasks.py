from sqlalchemy.orm import Session
from ..models import Game, Task
from ..scripts.packs import PACKS


def load_pack_into_game(db: Session, game: Game, pack: str) -> int:
    _, tasks = PACKS[pack]
    for desc, ttype, alco in tasks:
        db.add(Task(game_id=game.id, description=desc, type=ttype, is_alcoholic=alco))
    db.flush()
    return len(tasks)
