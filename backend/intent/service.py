"""Service for detecting high-level user intent."""

from intent.schemas import IntentResult, IntentType


class IntentDetectionError(Exception):
    """Raised when intent detection cannot be completed."""


class IntentDetectionService:
    """Detect the primary intent of a user's request."""

    def detect(self, user_input: str) -> IntentResult:
        """
        Detect the primary intent from a user request.

        This initial implementation uses deterministic keyword rules.
        The service interface can later be backed by an LLM without
        changing callers.
        """

        if not user_input or not user_input.strip():
            raise IntentDetectionError(
                "User input cannot be empty."
            )

        text = user_input.strip().lower()

        # Analytics-related requests.
        if self._contains_any(
            text,
            [
                "analytics",
                "performance",
                "campaign performance",
                "conversion",
                "conversions",
                "ctr",
                "roi",
                "engagement rate",
                "traffic",
            ],
        ):
            return IntentResult(
                intent=IntentType.ANALYTICS,
                confidence=0.95,
                reasoning="The request contains marketing analytics or performance terms.",
            )

        # Image-generation requests.
        if self._contains_any(
            text,
            [
                "generate an image",
                "generate image",
                "create an image",
                "create image",
                "marketing creative",
                "social media graphic",
                "banner",
                "ad creative",
            ],
        ):
            return IntentResult(
                intent=IntentType.IMAGE_GENERATION,
                confidence=0.95,
                reasoning="The request asks for a marketing image or creative.",
            )

        # SEO-related requests.
        if self._contains_any(
            text,
            [
                "seo",
                "search engine optimization",
                "keyword research",
                "keywords",
                "meta title",
                "meta description",
                "search intent",
                "technical seo",
                "on-page seo",
            ],
        ):
            return IntentResult(
                intent=IntentType.SEO_ANALYSIS,
                confidence=0.95,
                reasoning="The request contains SEO-related terms.",
            )

        # Competitor-analysis requests.
        if self._contains_any(
            text,
            [
                "competitor",
                "competitors",
                "competitive analysis",
                "competitor analysis",
                "competitor research",
                "competitor website",
                "competitor keywords",
            ],
        ):
            return IntentResult(
                intent=IntentType.COMPETITOR_ANALYSIS,
                confidence=0.95,
                reasoning="The request asks about competitors or competitive analysis.",
            )

        # General research requests.
        if self._contains_any(
            text,
            [
                "research",
                "market research",
                "market trends",
                "trends",
                "target audience",
                "audience research",
                "customer preferences",
                "market analysis",
                "industry analysis",
            ],
        ):
            return IntentResult(
                intent=IntentType.RESEARCH,
                confidence=0.90,
                reasoning="The request asks for market, audience, or general research.",
            )

        # Content-generation requests.
        if self._contains_any(
            text,
            [
                "write",
                "create a caption",
                "create caption",
                "instagram caption",
                "linkedin post",
                "facebook post",
                "tweet",
                "social media post",
                "blog",
                "blog post",
                "ad copy",
                "advertisement copy",
                "email",
                "newsletter",
                "product description",
                "call to action",
                "cta",
                "hashtags",
                "generate content",
                "create content",
            ],
        ):
            return IntentResult(
                intent=IntentType.CONTENT_GENERATION,
                confidence=0.90,
                reasoning="The request asks for marketing content generation.",
            )

        # Fall back to general intent when no specialized intent is detected.
        return IntentResult(
            intent=IntentType.GENERAL,
            confidence=0.60,
            reasoning="No specialized marketing intent was detected.",
        )

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        """Return True when any keyword appears in the text."""
        return any(keyword in text for keyword in keywords)