"""Tests for backend configuration loading."""

import os
import unittest
from unittest.mock import patch

from config.settings import Settings, get_settings, reset_settings_cache


class TestSettings(unittest.TestCase):
    def setUp(self) -> None:
        reset_settings_cache()

    def tearDown(self) -> None:
        reset_settings_cache()

    def test_default_values_without_env_file(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.APP_ENV, "development")
        self.assertEqual(settings.APP_NAME, "MarketingOS AI")
        self.assertEqual(settings.DATABASE_NAME, "marketingos")
        self.assertEqual(settings.FRONTEND_URL, "http://localhost:5173")
        self.assertIsNone(settings.MONGODB_URI)
        self.assertIsNone(settings.JWT_SECRET)
        self.assertIsNone(settings.LLM_PROVIDER)
        self.assertIsNone(settings.LLM_API_KEY)
        self.assertIsNone(settings.LLM_MODEL)
        self.assertIsNone(settings.SEARCH_API_KEY)
        self.assertIsNone(settings.IMAGE_API_KEY)

    def test_environment_variable_overrides(self) -> None:
        env = {
            "APP_ENV": "production",
            "APP_NAME": "Test MarketingOS",
            "DATABASE_NAME": "test_marketingos",
            "FRONTEND_URL": "http://localhost:3000",
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "gpt-4o-mini",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.APP_ENV, "production")
        self.assertEqual(settings.APP_NAME, "Test MarketingOS")
        self.assertEqual(settings.DATABASE_NAME, "test_marketingos")
        self.assertEqual(settings.FRONTEND_URL, "http://localhost:3000")
        self.assertEqual(settings.LLM_PROVIDER, "openai")
        self.assertEqual(settings.LLM_MODEL, "gpt-4o-mini")

    def test_empty_secret_values_are_normalized_to_none(self) -> None:
        env = {
            "MONGODB_URI": "",
            "JWT_SECRET": "",
            "LLM_API_KEY": "",
            "SEARCH_API_KEY": "",
            "IMAGE_API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

        self.assertIsNone(settings.MONGODB_URI)
        self.assertIsNone(settings.JWT_SECRET)
        self.assertIsNone(settings.LLM_API_KEY)
        self.assertIsNone(settings.SEARCH_API_KEY)
        self.assertIsNone(settings.IMAGE_API_KEY)

    def test_secret_values_are_masked_in_safe_dump(self) -> None:
        env = {
            "MONGODB_URI": "mongodb://user:pass@localhost:27017",
            "JWT_SECRET": "jwt-secret-value",
            "LLM_API_KEY": "llm-key-value",
            "SEARCH_API_KEY": "search-key-value",
            "IMAGE_API_KEY": "image-key-value",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

        safe = settings.safe_model_dump()

        self.assertEqual(safe["MONGODB_URI"], "***")
        self.assertEqual(safe["JWT_SECRET"], "***")
        self.assertEqual(safe["LLM_API_KEY"], "***")
        self.assertEqual(safe["SEARCH_API_KEY"], "***")
        self.assertEqual(safe["IMAGE_API_KEY"], "***")
        self.assertNotIn("jwt-secret-value", str(safe))
        self.assertNotIn("llm-key-value", str(safe))

    def test_secret_values_remain_accessible_internally(self) -> None:
        env = {"JWT_SECRET": "internal-secret", "LLM_API_KEY": "internal-llm-key"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None)

        assert settings.JWT_SECRET is not None
        assert settings.LLM_API_KEY is not None
        self.assertEqual(settings.JWT_SECRET.get_secret_value(), "internal-secret")
        self.assertEqual(settings.LLM_API_KEY.get_secret_value(), "internal-llm-key")

    def test_get_settings_returns_cached_instance(self) -> None:
        with patch.dict(os.environ, {"APP_NAME": "Cached Settings"}, clear=True):
            first = get_settings()
            second = get_settings()

        self.assertIs(first, second)
        self.assertEqual(first.APP_NAME, "Cached Settings")


if __name__ == "__main__":
    unittest.main()
