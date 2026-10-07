from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.brand_profile import (
    BrandProfileCreate,
    BrandProfileResponse,
    BrandProfileUpdate,
)
from backend.services.brand_profile_service import (
    BrandProfileNotFoundError,
    BrandProfileService,
)
from backend.utils.auth import get_current_user


router = APIRouter(
    prefix="/api/brand-profile",
    tags=["Brand Profile"],
)


def get_brand_profile_service() -> BrandProfileService:
    return BrandProfileService()


@router.post(
    "",
    response_model=BrandProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_brand_profile(
    payload: BrandProfileCreate,
    current_user: dict = Depends(get_current_user),
    brand_service: BrandProfileService = Depends(
        get_brand_profile_service
    ),
):
    try:
        return brand_service.create_brand_profile(
            user_id=str(current_user["_id"]),
            company_name=payload.company_name,
            industry=payload.industry,
            description=payload.description,
            target_audience=payload.target_audience,
            products_services=payload.products_services,
            brand_tone=payload.brand_tone,
            website=payload.website,
            location=payload.location,
            competitors=payload.competitors,
            social_links=payload.social_links,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc


@router.get(
    "",
    response_model=BrandProfileResponse,
)
def get_brand_profile(
    current_user: dict = Depends(get_current_user),
    brand_service: BrandProfileService = Depends(
        get_brand_profile_service
    ),
):
    profile = brand_service.get_brand_profile(
        str(current_user["_id"])
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "data": None,
                "message": "Brand profile not found.",
            },
        )

    return profile


@router.put(
    "",
    response_model=BrandProfileResponse,
)
def update_brand_profile(
    payload: BrandProfileUpdate,
    current_user: dict = Depends(get_current_user),
    brand_service: BrandProfileService = Depends(
        get_brand_profile_service
    ),
):
    updates = payload.model_dump(exclude_unset=True)

    try:
        return brand_service.update_brand_profile(
            user_id=str(current_user["_id"]),
            updates=updates,
        )

    except BrandProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_brand_profile(
    current_user: dict = Depends(get_current_user),
    brand_service: BrandProfileService = Depends(
        get_brand_profile_service
    ),
):
    try:
        brand_service.delete_brand_profile(
            str(current_user["_id"])
        )

    except BrandProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    return None
