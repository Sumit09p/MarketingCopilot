"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

_SECRET_FIELDS = frozenset(
    {
        "MONGODB_URI",
        "JWT_SECRET",
        "LLM_API_KEY",
        "SEARCH_API_KEY",
        "IMAGE_API_KEY",
    }
)


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "MarketingOS AI"

    MONGODB_URI: SecretStr | None = None
    DATABASE_NAME: str = "marketingos"

    JWT_SECRET: SecretStr | None = None
    JWT_EXPIRE_MINUTES: int = 60

    LLM_PROVIDER: str | None = None
    LLM_API_KEY: SecretStr | None = None
    LLM_MODEL: str | None = None

    FRONTEND_URL: str = "http://localhost:5173"

    SEARCH_API_KEY: SecretStr | None = None
    IMAGE_API_KEY: SecretStr | None = None

    @field_validator(
        "MONGODB_URI",
        "JWT_SECRET",
        "LLM_API_KEY",
        "SEARCH_API_KEY",
        "IMAGE_API_KEY",
        mode="before",
    )
    @classmethod
    def _empty_secret_to_none(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value

    @field_validator("LLM_PROVIDER", "LLM_MODEL", mode="before")
    @classmethod
    def _empty_optional_str_to_none(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value

    def safe_model_dump(self) -> dict[str, object]:
        """Return settings safe for logs, debug output, or API responses."""
        result: dict[str, object] = {}
        for field_name in Settings.model_fields:
            value = getattr(self, field_name)
            if field_name in _SECRET_FIELDS:
                result[field_name] = "***" if value is not None else None
            else:
                result[field_name] = value
        return result


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings instance. Intended for tests."""
    get_settings.cache_clear()
