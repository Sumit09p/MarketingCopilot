"""Centralized MongoDB connection management."""

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError

from config import get_settings

MONGODB_CLIENT_OPTIONS: dict[str, int] = {
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 5000,
    "socketTimeoutMS": 10000,
}

_client: MongoClient | None = None


class DatabaseNotConfiguredError(Exception):
    """Raised when MongoDB URI is not configured."""


class DatabaseConnectionError(Exception):
    """Raised when MongoDB connection or ping fails."""


def _require_mongodb_uri() -> str:
    settings = get_settings()
    if settings.MONGODB_URI is None:
        raise DatabaseNotConfiguredError(
            "MongoDB is not configured. Set MONGODB_URI in the environment."
        )
    return settings.MONGODB_URI.get_secret_value()


def get_mongo_client() -> MongoClient:
    """Return a shared MongoClient instance. Does not connect until first use."""
    global _client
    if _client is None:
        uri = _require_mongodb_uri()
        _client = MongoClient(uri, **MONGODB_CLIENT_OPTIONS)
    return _client


def get_database() -> Database:
    """Return the configured MongoDB database."""
    settings = get_settings()
    return get_mongo_client()[settings.DATABASE_NAME]


def ping_database() -> dict[str, Any]:
    """Verify MongoDB connectivity and return a safe success result."""
    try:
        client = get_mongo_client()
        client.admin.command("ping")
    except DatabaseNotConfiguredError:
        raise
    except (ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError) as exc:
        raise DatabaseConnectionError("Unable to connect to MongoDB.") from exc

    settings = get_settings()
    return {
        "status": "ok",
        "database": settings.DATABASE_NAME,
    }


def close_mongo_client() -> None:
    """Close the shared MongoClient if one exists."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def reset_mongo_client() -> None:
    """Reset the shared client. Intended for tests."""
    close_mongo_client()
