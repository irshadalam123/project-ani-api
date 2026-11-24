"""Password hashing and JWT access tokens.

Refresh tokens are intentionally not persisted. There is no database yet.
"""

from datetime import timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.exceptions import AuthenticationException
from app.utils.datetime import utcnow

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(subject: str, settings: Settings) -> str:
    issued_at = utcnow()
    expires_at = issued_at + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.resolved_jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.resolved_jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationException("Access token has expired", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationException("Invalid access token", code="INVALID_TOKEN") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationException("Invalid access token", code="INVALID_TOKEN")
    return subject
