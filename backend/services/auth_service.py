from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from database import get_database
from models.user import build_user_document, USERS_COLLECTION
from services.password_service import hash_password, verify_password


class EmailAlreadyExistsError(Exception):
    """Raised when attempting to register a duplicate email."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthService:
    """Authentication and user persistence service."""

    def __init__(self) -> None:
        self.users = get_database()[USERS_COLLECTION]

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        normalized_email = self.normalize_email(email)

        existing_user = self.users.find_one(
            {"email": normalized_email}
        )

        if existing_user:
            raise EmailAlreadyExistsError(
                "Email already registered."
            )

        now = datetime.now(UTC)

        user_document = build_user_document(
            name=name,
            email=normalized_email,
            password_hash=hash_password(password),
            now=now,
        )

        try:
            result = self.users.insert_one(user_document)
        except Exception as exc:
            # Keep database implementation details away from API responses.
            raise RuntimeError(
                "Unable to create user."
            ) from exc

        user_document["_id"] = result.inserted_id

        return user_document

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        normalized_email = self.normalize_email(email)

        user = self.users.find_one(
            {"email": normalized_email}
        )

        if user is None:
            raise AuthenticationError(
                "Invalid email or password."
            )

        if not verify_password(
            password,
            user["password_hash"],
        ):
            raise AuthenticationError(
                "Invalid email or password."
            )

        return user

    def get_user_by_id(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            return None

        return self.users.find_one(
            {"_id": object_id}
        )