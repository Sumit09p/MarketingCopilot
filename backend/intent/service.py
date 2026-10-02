"""Service for detecting high-level user intent."""

from intent.schemas import IntentResult, IntentType


class IntentDetectionError(Exception):
    """Raised when intent detection cannot be completed."""


class IntentDetectionService:
    """Detect the primary intent of a user's request."""

    def detect(self, user_input: str) -> IntentResult:
        """
        Detect the primary intent from a user request.

        This implementation uses deterministic keyword rules.
        The service interface can later be backed by an LLM without
        changing callers.
        """

        if not user_input or not user_input.strip():
            raise IntentDetectionError(
                "User input cannot be empty."
            )

        text = user_input.strip().lower()

        # ---------------------------------------------------------
        # Analytics-related requests
        # ---------------------------------------------------------
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
                "revenue",
                "campaign metrics",
                "marketing metrics",
            ],
        ):
            return IntentResult(
                intent=IntentType.ANALYTICS,
                confidence=0.95,
                reasoning=(
                    "The request contains marketing analytics "
                    "or performance-related terms."
                ),
            )

        # ---------------------------------------------------------
        # Image-generation requests
        # ---------------------------------------------------------
        if self._contains_any(
            text,
            [
                "generate an image",
                "generate image",
                "generate a picture",
                "generate picture",
                "create an image",
                "create image",
                "create a picture",
                "create picture",
                "marketing image",
                "marketing creative",
                "social media image",
                "social media graphic",
                "instagram image",
                "facebook image",
                "linkedin image",
                "ad creative",
                "advertisement creative",
                "advertising creative",
                "visual creative",
                "product image",
                "product creative",
                "campaign image",
                "campaign creative",
                "banner",
                "poster",
            ],
        ):
            return IntentResult(
                intent=IntentType.IMAGE_GENERATION,
                confidence=0.95,
                reasoning=(
                    "The request asks for a marketing image "
                    "or visual creative."
                ),
            )

        # ---------------------------------------------------------
        # SEO-related requests
        # ---------------------------------------------------------
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
                "on page seo",
                "seo audit",
                "seo analysis",
                "seo optimization",
            ],
        ):
            return IntentResult(
                intent=IntentType.SEO_ANALYSIS,
                confidence=0.95,
                reasoning=(
                    "The request contains SEO-related terms."
                ),
            )

        # ---------------------------------------------------------
        # Competitor-analysis requests
        # ---------------------------------------------------------
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
                "competitor content",
                "competitor comparison",
                "compare competitors",
            ],
        ):
            return IntentResult(
                intent=IntentType.COMPETITOR_ANALYSIS,
                confidence=0.95,
                reasoning=(
                    "The request asks about competitors "
                    "or competitive analysis."
                ),
            )

        # ---------------------------------------------------------
        # General research requests
        # ---------------------------------------------------------
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
                "customer research",
                "audience analysis",
                "market opportunity",
                "market opportunities",
            ],
        ):
            return IntentResult(
                intent=IntentType.RESEARCH,
                confidence=0.90,
                reasoning=(
                    "The request asks for market, audience, "
                    "or general research."
                ),
            )

        # ---------------------------------------------------------
        # Content-generation requests
        # ---------------------------------------------------------
        if self._contains_any(
            text,
            [
                "write",
                "create a caption",
                "create caption",
                "generate caption",
                "instagram caption",
                "linkedin post",
                "facebook post",
                "twitter post",
                "x post",
                "tweet",
                "social media post",
                "social media content",
                "blog",
                "blog post",
                "write a blog",
                "create a blog",
                "generate a blog",
                "ad copy",
                "advertisement copy",
                "advertising copy",
                "email",
                "email campaign",
                "newsletter",
                "product description",
                "call to action",
                "cta",
                "hashtags",
                "generate content",
                "create content",
                "marketing copy",
                "marketing content",
            ],
        ):
            return IntentResult(
                intent=IntentType.CONTENT_GENERATION,
                confidence=0.90,
                reasoning=(
                    "The request asks for marketing "
                    "content generation."
                ),
            )

        # ---------------------------------------------------------
        # General intent fallback
        # ---------------------------------------------------------
        return IntentResult(
            intent=IntentType.GENERAL,
            confidence=0.60,
            reasoning=(
                "No specialized marketing intent was detected."
            ),
        )

    @staticmethod
    def _contains_any(
        text: str,
        keywords: list[str],
    ) -> bool:
        """Return True when any keyword appears in the text."""
        return any(
            keyword in text
            for keyword in keywords
        )