"""Host accounts: scrypt password hashes + HMAC-signed session tokens."""
import base64
import hashlib
import hmac
import secrets
import time
from ..config import settings

_SECRET = (settings.SECRET_KEY or secrets.token_hex(32)).encode()
SESSION_TTL = 30 * 24 * 3600
COOKIE_NAME = "host_session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str | None) -> bool:
    try:
        algo, salt_b64, dk_b64 = (stored or "").split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=2**14, r=8, p=1)
    return hmac.compare_digest(dk, base64.b64decode(dk_b64))


def _sign(payload: str) -> str:
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_token(account_id: str) -> str:
    payload = f"{account_id}.{int(time.time()) + SESSION_TTL}"
    return f"{payload}.{_sign(payload)}"


def read_token(token: str | None) -> str | None:
    """Return the account id from a valid, unexpired token."""
    try:
        account_id, exp, sig = (token or "").rsplit(".", 2)
    except ValueError:
        return None
    payload = f"{account_id}.{exp}"
    if not hmac.compare_digest(sig, _sign(payload)) or int(exp) < time.time():
        return None
    return account_id


def player_key(user_id: str) -> str:
    """Public stand-in for a player's id. The real id opens their page, so it
    must never appear in lists other people can see."""
    return hmac.new(_SECRET, b"player:" + user_id.encode(), hashlib.sha256).hexdigest()[:16]
