from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from database import get_database
from models.user import USERS_COLLECTION


class UserNotFoundError(Exception):
    pass


class UserProfileService:
    def __init__(self) -> None:
        self.users = get_database()[USERS_COLLECTION]

    def get_user_by_id(self, user_id: str) -> dict[str, Any]:
        try:
            object_id = ObjectId(user_id)
        except Exception as exc:
            raise UserNotFoundError("User not found.") from exc

        user = self.users.find_one({"_id": object_id})

        if user is None:
            raise UserNotFoundError("User not found.")

        return user

    def update_user_name(
        self,
        user_id: str,
        name: str,
    ) -> dict[str, Any]:
        try:
            object_id = ObjectId(user_id)
        except Exception as exc:
            raise UserNotFoundError("User not found.") from exc

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("Name cannot be empty.")

        result = self.users.find_one_and_update(
            {"_id": object_id},
            {
                "$set": {
                    "name": normalized_name,
                    "updated_at": datetime.now(UTC),
                }
            },
            return_document=True,
        )

        if result is None:
            raise UserNotFoundError("User not found.")

        return result