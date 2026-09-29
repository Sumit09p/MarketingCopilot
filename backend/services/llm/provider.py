from google import genai

from config import get_settings
from services.llm.base import LLMProvider
from services.llm.schemas import LLMRequest, LLMResponse


class LLMConfigurationError(Exception):
    """Raised when LLM configuration is missing or invalid."""


class LLMProviderError(Exception):
    """Raised when an LLM provider request fails."""


class MockLLMProvider(LLMProvider):
    """
    Local provider used for development and automated tests.

    This provider never calls an external API.
    """

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        return f"Mock LLM response for: {prompt}"


class GeminiProvider(LLMProvider):
    """
    Gemini implementation of the LLM provider interface.
    """

    def __init__(self) -> None:
        settings = get_settings()

        if settings.LLM_PROVIDER != "gemini":
            raise LLMConfigurationError(
                "LLM_PROVIDER must be set to 'gemini'."
            )

        if settings.LLM_API_KEY is None:
            raise LLMConfigurationError(
                "LLM_API_KEY is not configured."
            )

        if settings.LLM_MODEL is None:
            raise LLMConfigurationError(
                "LLM_MODEL is not configured."
            )

        self.model = settings.LLM_MODEL

        try:
            self.client = genai.Client(
                api_key=settings.LLM_API_KEY.get_secret_value()
            )
        except Exception as exc:
            raise LLMConfigurationError(
                "Unable to initialize Gemini provider."
            ) from exc

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        contents = prompt

        if system_prompt:
            contents = (
                f"System instruction:\n{system_prompt}\n\n"
                f"User request:\n{prompt}"
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
        except Exception as exc:
            raise LLMProviderError(
                "Gemini request failed."
            ) from exc

        if not response.text:
            raise LLMProviderError(
                "Gemini returned an empty response."
            )

        return response.text


class LLMService:
    """
    Central application service for LLM operations.

    Higher-level application code should depend on this service
    instead of directly importing an LLM provider SDK.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or MockLLMProvider()

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        content = self.provider.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
        )

        return LLMResponse(
            content=content,
            provider=self.provider.__class__.__name__,
        )