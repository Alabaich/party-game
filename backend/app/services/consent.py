import hashlib
from sqlalchemy.orm import Session
from ..models import ConsentDocument, Game
from ..schemas.settings import load_settings


def consent_hash(title: str, body: str) -> str:
    return hashlib.sha256(f"{title}\n\n{body}".encode()).hexdigest()


def current_consent_hash(game: Game) -> str | None:
    c = load_settings(game.settings).consent
    return consent_hash(c.title, c.body) if c.enabled else None


def ensure_consent_document(db: Session, game: Game) -> ConsentDocument | None:
    """Snapshot the current consent text (once per distinct version)."""
    c = load_settings(game.settings).consent
    if not c.enabled:
        return None
    sha = consent_hash(c.title, c.body)
    doc = (db.query(ConsentDocument)
           .filter(ConsentDocument.game_id == game.id, ConsentDocument.sha256 == sha).first())
    if not doc:
        doc = ConsentDocument(game_id=game.id, sha256=sha, title=c.title, body=c.body)
        db.add(doc)
        db.flush()
    return doc
