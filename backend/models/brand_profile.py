from typing import Any
from datetime import datetime


BRAND_PROFILES_COLLECTION = "brand_profiles"


def build_brand_profile_document(
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
    """Build a MongoDB brand profile document."""

    return {
        "user_id": user_id,
        "company_name": company_name.strip(),
        "industry": industry.strip(),
        "description": description.strip(),
        "target_audience": target_audience.strip(),
        "products_services": products_services or [],
        "brand_tone": brand_tone.strip(),
        "website": website.strip(),
        "location": location.strip(),
        "competitors": competitors or [],
        "social_links": social_links or {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


def brand_profile_to_response(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Convert MongoDB brand profile into a safe API response."""

    return {
        "id": str(profile["_id"]),
        "user_id": profile["user_id"],
        "company_name": profile["company_name"],
        "industry": profile["industry"],
        "description": profile.get(
            "description",
            "",
        ),
        "target_audience": profile.get(
            "target_audience",
            "",
        ),
        "products_services": profile.get(
            "products_services",
            [],
        ),
        "brand_tone": profile.get(
            "brand_tone",
            "",
        ),
        "website": profile.get(
            "website",
            "",
        ),
        "location": profile.get(
            "location",
            "",
        ),
        "competitors": profile.get(
            "competitors",
            [],
        ),
        "social_links": profile.get(
            "social_links",
            {},
        ),
        "created_at": profile["created_at"],
        "updated_at": profile["updated_at"],
    }
