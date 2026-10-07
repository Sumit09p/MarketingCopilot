"""Authentication dependencies for protected routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.user import user_document_to_response
from services.auth_service import AuthService, AuthenticationError
from services.jwt_service import (
    InvalidTokenError,
    JWTNotConfiguredError,
    decode_access_token,
)


security = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> dict:
    """Return the authenticated user."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "data": None,
                "message": "Authentication required.",
            },
        )

    try:
        user_id = decode_access_token(
            credentials.credentials
        )
    except JWTNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "data": None,
                "message": "Authentication service is unavailable.",
            },
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "data": None,
                "message": "Invalid or expired token.",
            },
        ) from exc

    user = auth_service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "data": None,
                "message": "Invalid or expired token.",
            },
        )

    return user


def current_user_response(user: dict) -> dict:
    """Build a safe current-user response."""
    return {
        "success": True,
        "data": user_document_to_response(user),
        "message": None,
    }