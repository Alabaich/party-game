"""Shared API dependencies."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Account, Game
from ..services.auth import COOKIE_NAME, read_token


def current_account(request: Request, db: Session = Depends(get_db)) -> Account:
    token = request.cookies.get(COOKIE_NAME)
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:]
    account_id = read_token(token)
    acc = db.get(Account, account_id) if account_id else None
    if not acc or not acc.is_active:
        raise HTTPException(401, "Please log in")
    return acc


def optional_account(request: Request, db: Session = Depends(get_db)) -> Account | None:
    try:
        return current_account(request, db)
    except HTTPException:
        return None


def owned_game(game_id: str, acc: Account = Depends(current_account),
               db: Session = Depends(get_db)) -> Game:
    game = db.get(Game, game_id)
    if not game or game.account_id != acc.id:
        raise HTTPException(404, "Game not found")
    return game


__all__ = ["get_db", "current_account", "owned_game"]
