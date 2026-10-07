from fastapi import APIRouter, Depends, HTTPException

from models.user import user_document_to_response
from schemas.user import (
    UpdateUserProfileRequest,
    UserProfileResponse,
)
from services.user_profile_service import (
    UserNotFoundError,
    UserProfileService,
)
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


def get_user_profile_service() -> UserProfileService:
    return UserProfileService()


@router.get(
    "/me",
    response_model=UserProfileResponse,
)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
):
    return UserProfileResponse(
        **user_document_to_response(current_user)
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse,
)
def update_my_profile(
    request: UpdateUserProfileRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserProfileService = Depends(
        get_user_profile_service
    ),
):
    try:
        updated_user = user_service.update_user_name(
            user_id=str(current_user["_id"]),
            name=request.name,
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    return UserProfileResponse(
        **user_document_to_response(updated_user)
    )