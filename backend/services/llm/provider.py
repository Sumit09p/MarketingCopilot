from __future__ import annotations

import json

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

    Generic prompts preserve the original mock response contract.
    Agent-specific prompts return deterministic structured JSON.
    """

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        prompt_lower = prompt.lower()

        # ---------------------------------------------------------
        # Content Generation Agent
        # ---------------------------------------------------------
        if (
            "campaign_hook" in prompt_lower
            or "content generation" in prompt_lower
            or "social media" in prompt_lower
        ):
            return json.dumps(
                {
                    "campaign_hook": (
                        "Work smarter with AI and get more done."
                    ),
                    "caption": (
                        "Meet your new AI productivity companion. "
                        "Plan smarter, stay focused, and get more done "
                        "with less effort. 🚀"
                    ),
                    "cta": (
                        "Try it today and boost your productivity."
                    ),
                    "hashtags": [
                        "#AI",
                        "#Productivity",
                        "#AITools",
                        "#WorkSmarter",
                        "#Technology",
                    ],
                    "strategy": [
                        "Use short-form educational content to "
                        "demonstrate productivity benefits.",
                        "Show practical use cases through relatable "
                        "Instagram posts and reels.",
                        "Use clear CTAs to drive product trials "
                        "and conversions.",
                    ],
                }
            )

        # ---------------------------------------------------------
        # Research Agent
        # ---------------------------------------------------------
        if (
            "audience_insights" in prompt_lower
            and "market_trends" in prompt_lower
        ):
            return json.dumps(
                {
                    "topic": "Mock research topic",
                    "summary": (
                        "Mock market research summary for development "
                        "and testing."
                    ),
                    "audience_insights": [
                        "Users value convenient digital solutions.",
                        "Customers respond to clear product benefits.",
                        "Practical use cases influence adoption.",
                    ],
                    "market_trends": [
                        "Increasing adoption of AI-powered tools.",
                        "Growing demand for automation.",
                        "Personalized digital experiences are increasing.",
                    ],
                    "opportunities": [
                        "Educational content can attract new users.",
                        "Automation can improve customer engagement.",
                        "Targeted campaigns can improve conversions.",
                    ],
                }
            )

        # ---------------------------------------------------------
        # Competitor Analysis Agent
        # ---------------------------------------------------------
        if (
            "competitor" in prompt_lower
            and (
                "positioning" in prompt_lower
                or "competitor analysis" in prompt_lower
            )
        ):
            return json.dumps(
                {
                    "competitors": [
                        "Mock Competitor A",
                        "Mock Competitor B",
                        "Mock Competitor C",
                    ],
                    "summary": (
                        "Mock competitor analysis generated for "
                        "development and testing."
                    ),
                    "positioning": [
                        "Competitors emphasize ease of use.",
                        "Competitors highlight automation.",
                        "Competitors use productivity-focused messaging.",
                    ],
                    "content_gaps": [
                        "More educational content",
                        "More detailed product demonstrations",
                        "More customer-focused use cases",
                    ],
                    "recommendations": [
                        "Differentiate through clear AI capabilities.",
                        "Publish practical educational content.",
                        "Highlight measurable customer benefits.",
                    ],
                }
            )

        # ---------------------------------------------------------
        # SEO Agent
        # ---------------------------------------------------------
        if (
            "seo" in prompt_lower
            and (
                "keyword" in prompt_lower
                or "search intent" in prompt_lower
                or "meta" in prompt_lower
            )
        ):
            return json.dumps(
                {
                    "summary": (
                        "Mock SEO analysis generated for development "
                        "and testing."
                    ),
                    "keywords": [
                        "AI productivity tool",
                        "AI productivity app",
                        "productivity automation",
                    ],
                    "search_intent": [
                        "Informational",
                        "Commercial",
                        "Transactional",
                    ],
                    "technical_observations": [
                        "Improve page metadata.",
                        "Improve content structure.",
                        "Ensure important pages are crawlable.",
                    ],
                    "content_gaps": [
                        "AI productivity guides",
                        "Product comparison content",
                        "Use-case landing pages",
                    ],
                    "recommendations": [
                        "Create keyword-focused landing pages.",
                        "Improve title and meta descriptions.",
                        "Publish useful long-form content.",
                    ],
                }
            )

        # ---------------------------------------------------------
        # Analytics Agent
        # ---------------------------------------------------------
        if (
            "analytics" in prompt_lower
            or "ctr" in prompt_lower
            or "conversion rate" in prompt_lower
        ):
            return json.dumps(
                {
                    "summary": (
                        "Mock marketing analytics interpretation "
                        "generated for development and testing."
                    ),
                    "observations": [
                        "Traffic shows room for further growth.",
                        "Engagement should be monitored by channel.",
                        "Conversion performance should be compared "
                        "across campaigns.",
                    ],
                    "trends": [
                        "Traffic trend is being monitored.",
                        "Engagement trend is being monitored.",
                        "Conversion trend is being monitored.",
                    ],
                    "recommendations": [
                        "Identify high-performing channels.",
                        "Improve campaigns with low conversion rates.",
                        "Continue monitoring campaign performance.",
                    ],
                }
            )

        # ---------------------------------------------------------
        # Image Generation Agent
        # ---------------------------------------------------------
        if (
            "image" in prompt_lower
            or "creative" in prompt_lower
            or "visual" in prompt_lower
        ):
            return json.dumps(
                {
                    "status": "IMAGE_PROVIDER_NOT_CONFIGURED",
                    "prompt": prompt,
                    "image_url": None,
                    "provider": None,
                }
            )

        # ---------------------------------------------------------
        # Generic fallback
        # ---------------------------------------------------------
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
    instead of directly importing a provider SDK.
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