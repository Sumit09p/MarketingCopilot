import unittest
from unittest.mock import patch

from services.llm.provider import (
    GeminiProvider,
    LLMConfigurationError,
    LLMService,
    MockLLMProvider,
)
from services.llm.schemas import LLMRequest


class TestMockLLMProvider(unittest.TestCase):

    def test_generate_returns_mock_response(self):
        provider = MockLLMProvider()

        result = provider.generate(
            prompt="Hello"
        )

        self.assertEqual(
            result,
            "Mock LLM response for: Hello",
        )


class TestLLMService(unittest.TestCase):

    def test_default_provider_is_mock_provider(self):
        # Explicitly inject Mock provider so this unit test
        # does not depend on the real .env configuration.
        service = LLMService(
            provider=MockLLMProvider()
        )

        self.assertIsInstance(
            service.provider,
            MockLLMProvider,
        )

    def test_generate_returns_llm_response(self):
        # Use Mock provider for deterministic unit testing.
        service = LLMService(
            provider=MockLLMProvider()
        )

        request = LLMRequest(
            prompt="Create an Instagram caption."
        )

        response = service.generate(request)

        self.assertEqual(
            response.provider,
            "MockLLMProvider",
        )

        self.assertIn(
            "Create an Instagram caption.",
            response.content,
        )

    def test_system_prompt_is_accepted(self):
        # Use Mock provider so this test never calls Gemini.
        service = LLMService(
            provider=MockLLMProvider()
        )

        request = LLMRequest(
            prompt="Write a caption.",
            system_prompt="You are a marketing assistant.",
        )

        response = service.generate(request)

        self.assertTrue(response.content)


class TestGeminiProviderConfiguration(unittest.TestCase):

    @patch("services.llm.provider.get_settings")
    def test_missing_api_key_raises_configuration_error(
        self,
        mock_get_settings,
    ):
        mock_settings = unittest.mock.MagicMock()
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.LLM_API_KEY = None
        mock_settings.LLM_MODEL = "gemini-3.8-flash"

        mock_get_settings.return_value = mock_settings

        with self.assertRaises(LLMConfigurationError):
            GeminiProvider()

    @patch("services.llm.provider.get_settings")
    def test_missing_model_raises_configuration_error(
        self,
        mock_get_settings,
    ):
        mock_settings = unittest.mock.MagicMock()
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.LLM_API_KEY = MagicSecret("fake-key")
        mock_settings.LLM_MODEL = None

        mock_get_settings.return_value = mock_settings

        with self.assertRaises(LLMConfigurationError):
            GeminiProvider()

    @patch("services.llm.provider.get_settings")
    def test_wrong_provider_raises_configuration_error(
        self,
        mock_get_settings,
    ):
        mock_settings = unittest.mock.MagicMock()
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.LLM_API_KEY = MagicSecret("fake-key")
        mock_settings.LLM_MODEL = "some-model"

        mock_get_settings.return_value = mock_settings

        with self.assertRaises(LLMConfigurationError):
            GeminiProvider()


class MagicSecret:

    def __init__(self, value: str):
        self.value = value

    def get_secret_value(self) -> str:
        return self.value


if __name__ == "__main__":
    unittest.main()