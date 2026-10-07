from fastapi import APIRouter, Depends, HTTPException, status

from models.user import user_document_to_response
from schemas.auth import (
    AuthData,
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from services.auth_service import (
    AuthService,
    AuthenticationError,
    EmailAlreadyExistsError,
)
from services.jwt_service import (
    JWTNotConfiguredError,
    create_access_token,
)
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(),
):
    try:
        user = auth_service.register_user(
            name=request.name,
            email=request.email,
            password=request.password,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    try:
        token = create_access_token(
            str(user["_id"])
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

    return AuthResponse(
        success=True,
        data=AuthData(
            access_token=token,
            user=UserResponse(
                **user_document_to_response(user)
            ),
        ),
        message="Registration successful",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(),
):
    try:
        user = auth_service.authenticate_user(
            email=request.email,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "data": None,
                "message": "Invalid email or password.",
            },
        ) from exc

    try:
        token = create_access_token(
            str(user["_id"])
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

    return AuthResponse(
        success=True,
        data=AuthData(
            access_token=token,
            user=UserResponse(
                **user_document_to_response(user)
            ),
        ),
        message="Login successful",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: dict = Depends(get_current_user),
):
    return UserResponse(
        **user_document_to_response(current_user)
    )