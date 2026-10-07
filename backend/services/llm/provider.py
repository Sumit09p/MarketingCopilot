from __future__ import annotations

import json
import time

from google import genai

from backend.config import get_settings
from backend.services.llm.base import LLMProvider
from backend.services.llm.schemas import LLMRequest, LLMResponse


class LLMConfigurationError(Exception):
    """Raised when the LLM provider configuration is invalid."""


class LLMProviderError(Exception):
    """Raised when an LLM provider fails during generation."""


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider used for local development and tests.

    The mock provider returns structured JSON for known marketing-agent
    prompts so the complete orchestration pipeline can be tested without
    external API keys.
    """

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:

        prompt_lower = prompt.lower()

        # ============================================================
        # REQUIRED TEST CASE
        # ============================================================
        if prompt.strip() == "Create an Instagram caption.":
            return f"Mock LLM response for: {prompt}"

        # ============================================================
        # COMPETITOR AGENT
        #
        # IMPORTANT:
        # This MUST come BEFORE RESEARCH detection.
        #
        # Competitor prompts contain research output such as:
        # audience_insights, market_trends, opportunities.
        # ============================================================
        if (
            "competitor analysis assistant" in prompt_lower
            or '"competitors": ["string"]' in prompt_lower
            or '"content_opportunities":["string"]' in prompt_lower
        ):
            return json.dumps(
                {
                    "competitors": [
                        "Mock Competitor A",
                        "Mock Competitor B",
                        "Mock Competitor C",
                    ],
                    "strengths": [
                        "Competitors have strong brand visibility in the fitness market.",
                        "Competitors provide convenient digital fitness experiences.",
                        "Competitors use clear benefit-focused marketing messages.",
                    ],
                    "weaknesses": [
                        "Competitor messaging can be generic for different audience segments.",
                        "Educational content opportunities are not fully utilized.",
                        "Personalized customer journeys can be improved.",
                    ],
                    "content_opportunities": [
                        "Create practical educational fitness content.",
                        "Publish detailed workout and wellness guides.",
                        "Use customer-focused fitness success stories.",
                    ],
                    "recommendations": [
                        "Differentiate through personalized fitness benefits.",
                        "Publish practical educational content for the target audience.",
                        "Highlight measurable customer outcomes and success stories.",
                    ],
                }
            )

        # ============================================================
        # SEO AGENT
        # ============================================================
        if (
            "seo recommendation assistant" in prompt_lower
            or '"primary_keywords"' in prompt_lower
            or '"secondary_keywords"' in prompt_lower
            or '"search_intent"' in prompt_lower
            or "seo analysis" in prompt_lower
        ):
            return json.dumps(
                {
                    "primary_keywords": [
                        "fitness training",
                        "online fitness program",
                        "personalized fitness",
                    ],
                    "secondary_keywords": [
                        "home workout",
                        "fitness coaching",
                        "healthy lifestyle",
                        "workout plan",
                        "wellness program",
                    ],
                    "search_intent": (
                        "Users are primarily looking for practical fitness "
                        "guidance, personalized workout programs, and wellness solutions."
                    ),
                    "meta_title": (
                        "Personalized Fitness Training and Wellness Programs"
                    ),
                    "meta_description": (
                        "Discover personalized fitness training, online workout "
                        "programs, wellness guidance, and practical fitness solutions."
                    ),
                    "content_gaps": [
                        "Personalized beginner workout guides",
                        "Home workout resources",
                        "Fitness and wellness educational content",
                    ],
                    "recommendations": [
                        "Create educational fitness content targeting practical user problems.",
                        "Build content around personalized workout and wellness guidance.",
                        "Use clear benefit-focused titles and descriptions.",
                    ],
                }
            )


                # ============================================================
        # IMAGE AGENT
        # ============================================================
        if (
            "image agent" in prompt_lower
            or "image generation" in prompt_lower
            or "visual creative" in prompt_lower
            or '"image_prompt"' in prompt_lower
        ):
            return json.dumps(
                {
                    "image_prompt": (
                        "Create a professional fitness marketing visual featuring "
                        "a modern wellness environment, an active person exercising, "
                        "clean composition, energetic but professional branding, "
                        "and space for marketing copy."
                    ),
                    "style": "professional realistic fitness photography",
                    "aspect_ratio": "1:1",
                    "purpose": (
                        "Create an engaging Instagram visual for a fitness "
                        "and wellness marketing campaign."
                    ),
                }
            )

        # ============================================================
        # CONTENT AGENT
        #
        # Required fields:
        # campaign_hook -> string
        # caption       -> string
        # cta           -> string
        # hashtags      -> list
        # strategy      -> NON-EMPTY list
        # ============================================================
        if (
            "content generation" in prompt_lower
            or "content agent" in prompt_lower
            or "campaign hook" in prompt_lower
            or "social media" in prompt_lower
            or "caption" in prompt_lower
            or "hashtags" in prompt_lower
        ):
            return json.dumps(
                {
                    "campaign_hook": (
                        "Your fitness journey starts with one small step."
                    ),
                    "caption": (
                        "Build a stronger, healthier routine with personalized "
                        "fitness guidance designed around your goals. Start today "
                        "and take one simple step toward a healthier lifestyle."
                    ),
                    "cta": (
                        "Start your fitness journey today and discover a routine "
                        "that works for you."
                    ),
                    "hashtags": [
                        "#Fitness",
                        "#Wellness",
                        "#Workout",
                        "#HealthyLifestyle",
                        "#FitnessJourney",
                    ],
                    "strategy": [
                        "Use benefit-focused Instagram content.",
                        "Combine educational fitness advice with personalized wellness messaging.",
                        "Use clear calls to action to encourage audience engagement.",
                        "Focus on practical and achievable fitness goals.",
                    ],
                    "image_prompt": (
    "Create a premium Instagram fitness advertisement for a modern "
    "fitness and wellness brand. Show an energetic person working out "
    "in a clean modern gym, with an inspiring and healthy lifestyle "
    "feel, professional lighting, realistic photography, vibrant but "
    "professional composition, suitable for an Instagram campaign."
),
                }
            )

        # ============================================================
        # ANALYTICS AGENT
        # ============================================================
        if (
            "analytics agent" in prompt_lower
            or "marketing analytics" in prompt_lower
            or "performance metrics" in prompt_lower
            or "campaign performance" in prompt_lower
            or "marketing insights" in prompt_lower
        ):
            return json.dumps(
                {
                    "insights": [
                        "Campaign engagement can be improved through more personalized messaging.",
                        "Educational content can support audience acquisition.",
                        "Consistent campaign measurement is important for optimization.",
                    ],
                    "recommendations": [
                        "Track engagement across campaign channels.",
                        "Compare content performance by audience segment.",
                        "Optimize future campaigns using observed performance patterns.",
                    ],
                    "summary": (
                        "Mock marketing analytics summary for development and testing."
                    ),
                }
            )

        

        # ============================================================
        # RESEARCH AGENT
        #
        # IMPORTANT:
        # Research detection comes AFTER Competitor because competitor
        # prompts contain research context.
        # ============================================================
        if (
            "research agent" in prompt_lower
            or "market research" in prompt_lower
            or "audience_insights" in prompt_lower
            or "market_trends" in prompt_lower
        ):
            return json.dumps(
                {
                    "topic": "Fitness and wellness market",
                    "summary": (
                        "Mock market research summary for development and testing."
                    ),
                    "audience_insights": [
                        "Customers value convenient and practical fitness solutions.",
                        "Users respond well to clear and achievable health goals.",
                        "Personalized guidance can improve engagement and retention.",
                    ],
                    "market_trends": [
                        "Growing interest in digital fitness solutions.",
                        "Increasing demand for personalized wellness experiences.",
                        "Short-form fitness content continues to attract audiences.",
                    ],
                    "opportunities": [
                        "Educational fitness content can attract new users.",
                        "Personalized workout guidance can improve engagement.",
                        "Community-driven campaigns can improve retention.",
                    ],
                }
            )

        # ============================================================
        # GENERIC FALLBACK
        # ============================================================
        return f"Mock LLM response for: {prompt}"


class GeminiProvider(LLMProvider):
    """
    Gemini implementation.

    This provider is only initialized when explicitly requested and
    configured with a valid Gemini API key.
    """

    def __init__(self) -> None:
        settings = get_settings()

        provider = getattr(settings, "LLM_PROVIDER", None)

        if provider != "gemini":
            raise LLMConfigurationError(
                "GeminiProvider requires LLM_PROVIDER='gemini'."
            )

        api_key = getattr(settings, "LLM_API_KEY", None)

        if api_key is None:
            raise LLMConfigurationError(
                "LLM_API_KEY is required for GeminiProvider."
            )

        if hasattr(api_key, "get_secret_value"):
            api_key = api_key.get_secret_value()

        if not api_key:
            raise LLMConfigurationError(
                "LLM_API_KEY is required for GeminiProvider."
            )

        model = getattr(settings, "LLM_MODEL", None)

        if not model:
            raise LLMConfigurationError(
                "LLM_MODEL is required for GeminiProvider."
            )

        self.model = model

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as exc:
            raise LLMConfigurationError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:

        full_prompt = prompt

        if system_prompt:
            full_prompt = (
                f"{system_prompt}\n\n"
                f"User/Task:\n{prompt}"
            )

        max_attempts = 3
        retryable_status_codes = {429, 500, 502, 503, 504}

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                )

                text = getattr(response, "text", None)

                if not text:
                    raise LLMProviderError(
                        "Gemini returned an empty response."
                    )

                return text

            except LLMProviderError:
                raise

            except Exception as exc:
                status_code = getattr(exc, "status_code", None)

                if status_code is None:
                    status_code = getattr(exc, "code", None)

                if (
                    status_code in retryable_status_codes
                    and attempt < max_attempts
                ):
                    delay = 2 ** (attempt - 1)
                    time.sleep(delay)
                    continue

                raise LLMProviderError(
                    f"Gemini generation failed: {exc}"
                ) from exc

        raise LLMProviderError(
            "Gemini generation failed after all retry attempts."
        )


class LLMService:
    """
    High-level LLM service.

    Selects the configured provider:
    - gemini -> GeminiProvider
    - anything else / unset -> MockLLMProvider
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        if provider is not None:
            self.provider = provider
            return

        settings = get_settings()
        configured_provider = (settings.LLM_PROVIDER or "mock").lower().strip()

        if configured_provider == "gemini":
            self.provider = GeminiProvider()
        else:
            self.provider = MockLLMProvider()

    def generate(self, request: LLMRequest) -> LLMResponse:
        content = self.provider.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
        )

        return LLMResponse(
            content=content,
            provider=self.provider.__class__.__name__,
        )

