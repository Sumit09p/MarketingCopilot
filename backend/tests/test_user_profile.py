import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
# from fastapi import HTTPException

from routes.users import get_my_profile, update_my_profile
from schemas.user import UpdateUserProfileRequest
from services.user_profile_service import (
    UserNotFoundError,
    UserProfileService,
)


class TestUserProfileService(unittest.TestCase):

    def test_get_user_by_id(self) -> None:
        user_id = ObjectId(
            "507f1f77bcf86cd799439011"
        )

        user = {
            "_id": user_id,
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": "secret-hash",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = user

        with patch(
            "services.user_profile_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = UserProfileService()

            result = service.get_user_by_id(
                str(user_id)
            )

        self.assertEqual(
            result["_id"],
            user_id,
        )

    def test_get_user_by_id_not_found(self) -> None:
        user_id = ObjectId(
            "507f1f77bcf86cd799439011"
        )

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None

        with patch(
            "services.user_profile_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = UserProfileService()

            with self.assertRaises(
                UserNotFoundError
            ):
                service.get_user_by_id(
                    str(user_id)
                )

    def test_update_user_name(self) -> None:
        user_id = ObjectId(
            "507f1f77bcf86cd799439011"
        )

        updated_user = {
            "_id": user_id,
            "name": "Jane Doe",
            "email": "john@example.com",
            "password_hash": "secret-hash",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_collection = MagicMock()
        mock_collection.find_one_and_update.return_value = (
            updated_user
        )

        with patch(
            "services.user_profile_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = UserProfileService()

            result = service.update_user_name(
                user_id=str(user_id),
                name="  Jane Doe  ",
            )

        self.assertEqual(
            result["name"],
            "Jane Doe",
        )

        update_call = (
            mock_collection.find_one_and_update.call_args
        )

        update_document = update_call.args[1]

        self.assertEqual(
            update_document["$set"]["name"],
            "Jane Doe",
        )

    def test_update_user_not_found(self) -> None:
        user_id = ObjectId(
            "507f1f77bcf86cd799439011"
        )

        mock_collection = MagicMock()
        mock_collection.find_one_and_update.return_value = (
            None
        )

        with patch(
            "services.user_profile_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = UserProfileService()

            with self.assertRaises(
                UserNotFoundError
            ):
                service.update_user_name(
                    str(user_id),
                    "Jane Doe",
                )


class TestUserProfileRoutes(unittest.TestCase):

    def test_get_my_profile_does_not_expose_password(
        self,
    ) -> None:
        user = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": "secret-hash",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        response = get_my_profile(
            current_user=user
        )

        self.assertEqual(
            response.email,
            "john@example.com",
        )

        self.assertFalse(
            hasattr(response, "password_hash")
        )

    def test_update_my_profile(self) -> None:
        user = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": "secret-hash",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        updated_user = {
            **user,
            "name": "Jane Doe",
        }

        mock_service = MagicMock()

        mock_service.update_user_name.return_value = (
            updated_user
        )

        response = update_my_profile(
            request=UpdateUserProfileRequest(
                name="Jane Doe"
            ),
            current_user=user,
            user_service=mock_service,
        )

        self.assertEqual(
            response.name,
            "Jane Doe",
        )

        mock_service.update_user_name.assert_called_once()

    # def test_invalid_empty_name(self) -> None:
    #     with self.assertRaises(Exception):
    #         UpdateUserProfileRequest(
    #             name=""
    #         )


if __name__ == "__main__":
    unittest.main()