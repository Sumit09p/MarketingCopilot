"""Tests for authentication foundation."""

import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
from bson import ObjectId
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from config.settings import reset_settings_cache
from database.mongodb import reset_mongo_client
from routes.auth import get_me, login, register
from schemas.auth import LoginRequest, RegisterRequest
from services.auth_service import (
    AuthenticationError,
    EmailAlreadyExistsError,
)
from services.jwt_service import (
    InvalidTokenError,
    JWTNotConfiguredError,
    create_access_token,
    decode_access_token,
)
from services.password_service import hash_password, verify_password
from utils.auth import get_current_user


class TestPasswordService(unittest.TestCase):

    def test_hash_and_verify_password(self) -> None:
        password_hash = hash_password("secure-password")

        self.assertTrue(
            verify_password("secure-password", password_hash)
        )
        self.assertFalse(
            verify_password("wrong-password", password_hash)
        )

    def test_password_is_never_stored_plaintext(self) -> None:
        plain_password = "secure-password"
        password_hash = hash_password(plain_password)

        self.assertNotEqual(password_hash, plain_password)
        self.assertNotIn(plain_password, password_hash)


class TestJWTService(unittest.TestCase):

    def setUp(self) -> None:
        reset_settings_cache()

    def tearDown(self) -> None:
        reset_settings_cache()

    def test_create_and_decode_access_token(self) -> None:
        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            token = create_access_token(
                "507f1f77bcf86cd799439011"
            )
            user_id = decode_access_token(token)

        self.assertEqual(
            user_id,
            "507f1f77bcf86cd799439011",
        )

    def test_expired_token_is_rejected(self) -> None:
        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            expired_token = jwt.encode(
                {
                    "sub": "507f1f77bcf86cd799439011",
                    "exp": datetime.now(UTC)
                    - timedelta(minutes=1),
                },
                "test-jwt-secret",
                algorithm="HS256",
            )

            with self.assertRaises(InvalidTokenError):
                decode_access_token(expired_token)

    def test_invalid_token_is_rejected(self) -> None:
        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            with self.assertRaises(InvalidTokenError):
                decode_access_token("not-a-valid-token")

    def test_jwt_secret_is_not_exposed_in_errors(self) -> None:
        env = {"JWT_SECRET": "super-secret-jwt-key"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            with self.assertRaises(InvalidTokenError) as ctx:
                decode_access_token("invalid.token.value")

        self.assertNotIn(
            "super-secret-jwt-key",
            str(ctx.exception),
        )

    def test_jwt_requires_secret_configuration(self) -> None:
     with patch.dict(
        os.environ,
        {"JWT_SECRET": ""},
        clear=True,
    ):
        reset_settings_cache()

        with self.assertRaises(JWTNotConfiguredError):
            create_access_token(
                "507f1f77bcf86cd799439011"
            )


class TestAuthService(unittest.TestCase):

    def test_email_is_normalized(self) -> None:
        from services.auth_service import AuthService

        self.assertEqual(
            AuthService.normalize_email(
                "  John@Example.COM "
            ),
            "john@example.com",
        )

    def test_register_user(self) -> None:
        mock_collection = MagicMock()

        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(
            inserted_id=ObjectId(
                "507f1f77bcf86cd799439011"
            )
        )

        with patch(
            "services.auth_service.get_database",
            return_value={"users": mock_collection},
        ):
            from services.auth_service import AuthService

            service = AuthService()

            user = service.register_user(
                name="John Doe",
                email="John@Example.COM",
                password="password123",
            )

        stored_document = (
            mock_collection.insert_one.call_args.args[0]
        )

        self.assertEqual(
            stored_document["email"],
            "john@example.com",
        )
        self.assertNotEqual(
            stored_document["password_hash"],
            "password123",
        )
        self.assertEqual(
            user["_id"],
            ObjectId("507f1f77bcf86cd799439011"),
        )

    def test_duplicate_email_registration(self) -> None:
        mock_collection = MagicMock()

        mock_collection.find_one.return_value = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "email": "john@example.com",
        }

        with patch(
            "services.auth_service.get_database",
            return_value={"users": mock_collection},
        ):
            from services.auth_service import AuthService

            service = AuthService()

            with self.assertRaises(
                EmailAlreadyExistsError
            ):
                service.register_user(
                    name="Jane Doe",
                    email="john@example.com",
                    password="password123",
                )

    def test_authenticate_user_successfully(self) -> None:
        from services.auth_service import AuthService

        user = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": hash_password(
                "password123"
            ),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = user

        with patch(
            "services.auth_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = AuthService()

            result = service.authenticate_user(
                email="john@example.com",
                password="password123",
            )

        self.assertEqual(result["_id"], user["_id"])

    def test_authenticate_user_invalid_password(self) -> None:
        from services.auth_service import AuthService

        user = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": hash_password(
                "password123"
            ),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = user

        with patch(
            "services.auth_service.get_database",
            return_value={"users": mock_collection},
        ):
            service = AuthService()

            with self.assertRaises(AuthenticationError):
                service.authenticate_user(
                    email="john@example.com",
                    password="wrong-password",
                )


class TestAuthRoutes(unittest.TestCase):

    def setUp(self) -> None:
        reset_settings_cache()
        reset_mongo_client()

    def tearDown(self) -> None:
        reset_settings_cache()
        reset_mongo_client()

    def _sample_user(self) -> dict:
        return {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": hash_password(
                "password123"
            ),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    def test_successful_registration(self) -> None:
        user = self._sample_user()

        mock_service = MagicMock()
        mock_service.register_user.return_value = user

        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            response = register(
                RegisterRequest(
                    name="John Doe",
                    email="john@example.com",
                    password="password123",
                ),
                auth_service=mock_service,
            )

        self.assertTrue(response.success)
        self.assertEqual(
            response.message,
            "Registration successful",
        )
        self.assertEqual(
            response.data.user.email,
            "john@example.com",
        )
        self.assertTrue(
            response.data.access_token
        )

        mock_service.register_user.assert_called_once()

    def test_duplicate_email_registration(self) -> None:
        mock_service = MagicMock()

        mock_service.register_user.side_effect = (
            EmailAlreadyExistsError(
                "Email already registered."
            )
        )

        with self.assertRaises(Exception) as ctx:
            register(
                RegisterRequest(
                    name="Jane Doe",
                    email="john@example.com",
                    password="password123",
                ),
                auth_service=mock_service,
            )

        self.assertEqual(
            ctx.exception.status_code,
            409,
        )

    def test_successful_login(self) -> None:
        user = self._sample_user()

        mock_service = MagicMock()
        mock_service.authenticate_user.return_value = user

        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            response = login(
                LoginRequest(
                    email="john@example.com",
                    password="password123",
                ),
                auth_service=mock_service,
            )

        self.assertTrue(response.success)
        self.assertEqual(
            response.message,
            "Login successful",
        )
        self.assertEqual(
            response.data.token_type,
            "bearer",
        )
        self.assertTrue(
            response.data.access_token
        )
        self.assertEqual(
            response.data.user.email,
            "john@example.com",
        )

    def test_invalid_password_login(self) -> None:
        mock_service = MagicMock()

        mock_service.authenticate_user.side_effect = (
            AuthenticationError(
                "Invalid email or password."
            )
        )

        with self.assertRaises(Exception) as ctx:
            login(
                LoginRequest(
                    email="john@example.com",
                    password="wrong-password",
                ),
                auth_service=mock_service,
            )

        self.assertEqual(
            ctx.exception.status_code,
            401,
        )

    def test_malformed_login_input_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            LoginRequest(
                email="not-an-email",
                password="",
            )


class TestAuthDependency(unittest.TestCase):

    def setUp(self) -> None:
        reset_settings_cache()
        reset_mongo_client()

    def tearDown(self) -> None:
        reset_settings_cache()
        reset_mongo_client()

    def test_get_current_user_with_valid_token(self) -> None:
        user = {
            "_id": ObjectId(
                "507f1f77bcf86cd799439011"
            ),
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": "hashed",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_service = MagicMock()
        mock_service.get_user_by_id.return_value = user

        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            token = create_access_token(
                "507f1f77bcf86cd799439011"
            )

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token,
            )

            current_user = get_current_user(
                credentials=credentials,
                auth_service=mock_service,
            )

        self.assertEqual(
            current_user["email"],
            "john@example.com",
        )

    def test_get_current_user_without_token(self) -> None:
        mock_service = MagicMock()

        with self.assertRaises(Exception) as ctx:
            get_current_user(
                credentials=None,
                auth_service=mock_service,
            )

        self.assertEqual(
            ctx.exception.status_code,
            401,
        )

    def test_get_current_user_with_invalid_token(self) -> None:
        mock_service = MagicMock()

        env = {"JWT_SECRET": "test-jwt-secret"}

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="invalid.token.value",
            )

            with self.assertRaises(Exception) as ctx:
                get_current_user(
                    credentials=credentials,
                    auth_service=mock_service,
                )

        self.assertEqual(
            ctx.exception.status_code,
            401,
        )
        self.assertNotIn(
            "test-jwt-secret",
            str(ctx.exception.detail),
        )


if __name__ == "__main__":
    unittest.main()