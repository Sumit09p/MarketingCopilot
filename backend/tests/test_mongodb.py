"""Tests for MongoDB database layer."""

import os
import unittest
from unittest.mock import MagicMock, patch

from pymongo.errors import ConnectionFailure

from config.settings import reset_settings_cache
from database.mongodb import (
    DatabaseConnectionError,
    DatabaseNotConfiguredError,
    MONGODB_CLIENT_OPTIONS,
    get_database,
    get_mongo_client,
    ping_database,
    reset_mongo_client,
)


class TestMongoDB(unittest.TestCase):
    def setUp(self) -> None:
        reset_settings_cache()
        reset_mongo_client()

    def tearDown(self) -> None:
        reset_mongo_client()
        reset_settings_cache()

    def test_missing_mongodb_uri_raises_controlled_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            reset_settings_cache()

            with self.assertRaises(DatabaseNotConfiguredError) as ctx:
                get_mongo_client()

        self.assertIn("MongoDB is not configured", str(ctx.exception))
        self.assertNotIn("mongodb://", str(ctx.exception))

    def test_database_name_comes_from_settings(self) -> None:
        env = {
            "MONGODB_URI": "mongodb://user:secret-pass@localhost:27017",
            "DATABASE_NAME": "test_marketingos",
        }
        mock_client = MagicMock()
        mock_database = MagicMock()
        mock_client.__getitem__.return_value = mock_database

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()
            with patch("database.mongodb.MongoClient", return_value=mock_client) as mock_ctor:
                database = get_database()

        mock_ctor.assert_called_once_with(
            "mongodb://user:secret-pass@localhost:27017",
            **MONGODB_CLIENT_OPTIONS,
        )
        mock_client.__getitem__.assert_called_once_with("test_marketingos")
        self.assertIs(database, mock_database)

    def test_get_mongo_client_reuses_shared_instance(self) -> None:
        env = {"MONGODB_URI": "mongodb://localhost:27017"}
        mock_client = MagicMock()

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()
            with patch("database.mongodb.MongoClient", return_value=mock_client) as mock_ctor:
                first = get_mongo_client()
                second = get_mongo_client()

        self.assertIs(first, second)
        mock_ctor.assert_called_once()

    def test_ping_database_returns_safe_success_result(self) -> None:
        env = {
            "MONGODB_URI": "mongodb://localhost:27017",
            "DATABASE_NAME": "marketingos",
        }
        mock_client = MagicMock()
        mock_admin = MagicMock()
        mock_client.admin = mock_admin

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()
            with patch("database.mongodb.MongoClient", return_value=mock_client):
                result = ping_database()

        mock_admin.command.assert_called_once_with("ping")
        self.assertEqual(result, {"status": "ok", "database": "marketingos"})
        self.assertNotIn("mongodb://", str(result))

    def test_ping_database_raises_controlled_error_without_leaking_credentials(
        self,
    ) -> None:
        env = {"MONGODB_URI": "mongodb://user:secret-pass@localhost:27017"}
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = ConnectionFailure("network down")

        with patch.dict(os.environ, env, clear=True):
            reset_settings_cache()
            with patch("database.mongodb.MongoClient", return_value=mock_client):
                with self.assertRaises(DatabaseConnectionError) as ctx:
                    ping_database()

        message = str(ctx.exception)
        self.assertIn("Unable to connect to MongoDB", message)
        self.assertNotIn("secret-pass", message)
        self.assertNotIn("mongodb://", message)

    def test_application_imports_without_mongodb_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            reset_settings_cache()
            reset_mongo_client()

            from main import app

            self.assertEqual(app.title, "MarketingOS AI")


if __name__ == "__main__":
    unittest.main()
