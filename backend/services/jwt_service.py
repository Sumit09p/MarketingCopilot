"""JWT access-token creation and validation."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import PyJWTError

from config import get_settings


ALGORITHM = "HS256"


class JWTNotConfiguredError(Exception):
    """Raised when JWT_SECRET is not configured."""


class InvalidTokenError(Exception):
    """Raised when a JWT is invalid or expired."""


def create_access_token(user_id: str) -> str:
    """Create a signed JWT for the given user ID."""
    settings = get_settings()

    if settings.JWT_SECRET is None:
        raise JWTNotConfiguredError("JWT is not configured.")

    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    """Decode a JWT and return the user ID."""
    settings = get_settings()

    if settings.JWT_SECRET is None:
        raise JWTNotConfiguredError("JWT is not configured.")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[ALGORITHM],
        )
    except PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token.") from exc

    user_id = payload.get("sub")

    if not user_id or not isinstance(user_id, str):
        raise InvalidTokenError("Invalid or expired token.")

    return user_id