"""Platform endpoints: accounts (tenants) create and own games.

These are the seed of the future platform. They are intentionally minimal and
unauthenticated for now (auth is stubbed on the model); they exist so the new
Account/Game objects are reachable and the shape can be validated.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db, require_admin
from .. import schemas
from ..models import Account, Game

router = APIRouter(prefix="/accounts", tags=["accounts"],
                   dependencies=[Depends(require_admin)])


@router.post("", response_model=schemas.AccountOut)
def create_account(payload: schemas.AccountCreateIn, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.email == payload.email).first()
    if existing:
        raise HTTPException(400, "An account with this email already exists")
    acc = Account(email=payload.email, display_name=payload.display_name)
    # NOTE: password hashing intentionally not implemented yet (auth stubbed)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@router.get("/{account_id}", response_model=schemas.AccountOut)
def get_account(account_id: str, db: Session = Depends(get_db)):
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")
    return acc


@router.get("/{account_id}/games", response_model=list[schemas.GameOut])
def list_games(account_id: str, db: Session = Depends(get_db)):
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")
    return db.query(Game).filter(Game.account_id == account_id).all()


@router.post("/{account_id}/games", response_model=schemas.GameOut)
def create_game(account_id: str, payload: schemas.GameCreateIn,
                db: Session = Depends(get_db)):
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "Account not found")
    game = Game(account_id=account_id, name=payload.name,
                tasks_per_user=payload.tasks_per_user)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game
