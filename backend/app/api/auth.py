"""Host accounts. Signup is open only for the first account, or with the invite code."""
import hmac
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from .deps import get_db, current_account
from .. import schemas
from ..config import settings
from ..models import Account, Game
from ..services.auth import (
    COOKIE_NAME, SESSION_TTL, hash_password, verify_password, make_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _signup_open(db: Session) -> bool:
    return db.query(func.count(Account.id)).scalar() == 0


def _set_session(response: Response, acc: Account) -> None:
    response.set_cookie(COOKIE_NAME, make_token(acc.id), max_age=SESSION_TTL,
                        httponly=True, samesite="lax", secure=settings.COOKIE_SECURE)


@router.get("/status")
def status(db: Session = Depends(get_db)):
    return {"signup_open": _signup_open(db) or bool(settings.ADMIN_INVITE_CODE)}


@router.post("/signup", response_model=schemas.AccountOut)
def signup(payload: schemas.SignupIn, response: Response, db: Session = Depends(get_db)):
    first = _signup_open(db)
    invited = bool(settings.ADMIN_INVITE_CODE) and hmac.compare_digest(
        payload.invite_code, settings.ADMIN_INVITE_CODE)
    if not (first or invited):
        raise HTTPException(403, "Sign-up is closed")
    email = payload.email.lower()
    if db.query(Account.id).filter(func.lower(Account.email) == email).first():
        raise HTTPException(400, "An account with this email already exists")
    acc = Account(email=email, display_name=payload.display_name,
                  password_hash=hash_password(payload.password))
    db.add(acc)
    db.flush()
    if first:
        # the first host inherits games created before accounts existed
        db.query(Game).filter(Game.account_id.is_(None)).update(
            {Game.account_id: acc.id}, synchronize_session=False)
    db.commit()
    db.refresh(acc)
    _set_session(response, acc)
    return acc


@router.post("/login", response_model=schemas.AccountOut)
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    acc = db.query(Account).filter(func.lower(Account.email) == payload.email.lower()).first()
    if not acc or not acc.is_active or not verify_password(payload.password, acc.password_hash):
        raise HTTPException(401, "Wrong email or password")
    _set_session(response, acc)
    return acc


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=schemas.AccountOut)
def me(acc: Account = Depends(current_account)):
    return acc
