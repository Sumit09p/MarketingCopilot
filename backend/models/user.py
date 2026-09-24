from datetime import datetime
from typing import Any


USERS_COLLECTION = "users"


def build_user_document(
    name: str,
    email: str,
    password_hash: str,
    now: datetime,
) -> dict[str, Any]:
    """Build a MongoDB user document."""
    return {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "created_at": now,
        "updated_at": now,
    }


def user_document_to_response(user: dict[str, Any]) -> dict[str, Any]:
    """Convert a MongoDB user document into a safe API response."""
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }