from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from backend.database import get_database
from backend.models.brand_profile import (
    BRAND_PROFILES_COLLECTION,
    brand_profile_to_response,
)


class BrandProfileNotFoundError(Exception):
    pass


class BrandProfileService:
    """
    Manage the authenticated user's brand profile.

    Each user has one primary brand profile.
    """

    def __init__(self) -> None:
        self.brand_profiles = get_database()[
            BRAND_PROFILES_COLLECTION
        ]

    def _validate_user_id(
        self,
        user_id: str,
    ) -> str:
        """
        Validate MongoDB ObjectId format.

        The brand_profiles collection stores user_id as a string
        so that it remains easy to use throughout the application.
        """

        try:
            ObjectId(user_id)
        except Exception as exc:
            raise ValueError(
                "Invalid user ID."
            ) from exc

        return user_id

    def get_brand_profile(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Return the user's brand profile.

        Returns None if the user has not created one yet.
        """

        self._validate_user_id(user_id)

        profile = self.brand_profiles.find_one(
            {
                "user_id": user_id,
            }
        )

        if profile is None:
            return None

        return brand_profile_to_response(profile)

    def create_brand_profile(
        self,
        user_id: str,
        company_name: str,
        industry: str,
        description: str = "",
        target_audience: str = "",
        products_services: list[str] | None = None,
        brand_tone: str = "",
        website: str = "",
        location: str = "",
        competitors: list[str] | None = None,
        social_links: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a brand profile for a user.

        A user can have only one primary brand profile.
        """

        self._validate_user_id(user_id)

        company_name = company_name.strip()
        industry = industry.strip()

        if not company_name:
            raise ValueError(
                "Company name cannot be empty."
            )

        if not industry:
            raise ValueError(
                "Industry cannot be empty."
            )

        existing = self.brand_profiles.find_one(
            {
                "user_id": user_id,
            }
        )

        if existing is not None:
            raise ValueError(
                "Brand profile already exists."
            )

        now = datetime.now(UTC)

        document = {
            "user_id": user_id,
            "company_name": company_name,
            "industry": industry,
            "description": description.strip(),
            "target_audience": target_audience.strip(),
            "products_services": products_services or [],
            "brand_tone": brand_tone.strip(),
            "website": website.strip(),
            "location": location.strip(),
            "competitors": competitors or [],
            "social_links": social_links or {},
            "created_at": now,
            "updated_at": now,
        }

        result = self.brand_profiles.insert_one(
            document
        )

        document["_id"] = result.inserted_id

        return brand_profile_to_response(
            document
        )

    def update_brand_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update the user's existing brand profile.
        """

        self._validate_user_id(user_id)

        allowed_fields = {
            "company_name",
            "industry",
            "description",
            "target_audience",
            "products_services",
            "brand_tone",
            "website",
            "location",
            "competitors",
            "social_links",
        }

        clean_updates: dict[str, Any] = {}

        for key, value in updates.items():

            if key not in allowed_fields:
                continue

            if isinstance(value, str):
                value = value.strip()

            clean_updates[key] = value

        if not clean_updates:
            raise ValueError(
                "No valid brand profile fields provided."
            )

        if (
            "company_name" in clean_updates
            and not clean_updates["company_name"]
        ):
            raise ValueError(
                "Company name cannot be empty."
            )

        if (
            "industry" in clean_updates
            and not clean_updates["industry"]
        ):
            raise ValueError(
                "Industry cannot be empty."
            )

        clean_updates["updated_at"] = datetime.now(
            UTC
        )

        result = self.brand_profiles.find_one_and_update(
            {
                "user_id": user_id,
            },
            {
                "$set": clean_updates,
            },
            return_document=True,
        )

        if result is None:
            raise BrandProfileNotFoundError(
                "Brand profile not found."
            )

        return brand_profile_to_response(
            result
        )

    def delete_brand_profile(
        self,
        user_id: str,
    ) -> bool:
        """
        Delete the user's brand profile.
        """

        self._validate_user_id(user_id)

        result = self.brand_profiles.delete_one(
            {
                "user_id": user_id,
            }
        )

        if result.deleted_count == 0:
            raise BrandProfileNotFoundError(
                "Brand profile not found."
            )

        return True

