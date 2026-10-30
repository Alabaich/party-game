import secrets
from sqlalchemy.orm import Session
from ..models import Game

# no 0/O, 1/I/L, to survive being read aloud or off a poster
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
CODE_LEN = 5


def new_game_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))
        if not db.query(Game.id).filter(Game.code == code).first():
            return code


def normalize_code(code: str) -> str:
    return code.strip().upper()
