"""Service for creating structured execution plans."""

from __future__ import annotations

from planner.schemas import ExecutionPlan, PlannerTask


class PlannerService:
    """Create dependency-aware execution plans from user requests."""

    def create_plan(
        self,
        user_input: str,
        intent: str | None = None,
    ) -> ExecutionPlan:
        """
        Create a structured execution plan.

        The planner decides which specialized agents are required
        and how those agents depend on each other.

        The returned plan is validated by PlanValidator before
        execution by the orchestrator.
        """

        if not user_input or not user_input.strip():
            raise ValueError("User input cannot be empty.")

        normalized_input = user_input.strip().lower()

        normalized_intent = (
            intent.strip().upper()
            if intent is not None
            else None
        )

        # ---------------------------------------------------------
        # Explicit intent-based planning
        # ---------------------------------------------------------

        if normalized_intent in {
            "RESEARCH",
            "MARKET_RESEARCH",
        }:
            return self._research_plan(user_input)

        if normalized_intent in {
            "COMPETITOR_ANALYSIS",
            "COMPETITOR",
        }:
            return self._competitor_plan(user_input)

        if normalized_intent in {
            "SEO_ANALYSIS",
            "SEO",
        }:
            return self._seo_plan(user_input)

        if normalized_intent in {
            "CONTENT_GENERATION",
            "CONTENT",
        }:
            return self._content_plan(user_input)

        if normalized_intent in {
            "IMAGE_GENERATION",
            "IMAGE",
            "IMAGE_CREATION",
        }:
            return self._image_plan(user_input)

        if normalized_intent in {
            "ANALYTICS",
            "MARKETING_ANALYTICS",
        }:
            return self._analytics_plan(user_input)

        # ---------------------------------------------------------
        # Multi-agent campaign planning
        # ---------------------------------------------------------

        if self._is_campaign_request(normalized_input):
            return self._campaign_plan(user_input)

        # ---------------------------------------------------------
        # Fallback: detect specialized request directly
        # ---------------------------------------------------------

        if self._is_image_request(normalized_input):
            return self._image_plan(user_input)

        if self._is_research_request(normalized_input):
            return self._research_plan(user_input)

        if self._is_competitor_request(normalized_input):
            return self._competitor_plan(user_input)

        if self._is_seo_request(normalized_input):
            return self._seo_plan(user_input)

        if self._is_content_request(normalized_input):
            return self._content_plan(user_input)

        if self._is_analytics_request(normalized_input):
            return self._analytics_plan(user_input)

        raise ValueError(
            "Unable to create a specialized execution plan "
            "for the provided request."
        )

    # =============================================================
    # Individual agent plans
    # =============================================================

    @staticmethod
    def _research_plan(user_input: str) -> ExecutionPlan:
        """Create a research-only execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent="research",
                    depends_on=[],
                    required_inputs=["topic"],
                )
            ],
        )

    @staticmethod
    def _competitor_plan(user_input: str) -> ExecutionPlan:
        """Create a competitor-analysis execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="competitor_1",
                    agent="competitor",
                    depends_on=[],
                    required_inputs=["topic"],
                )
            ],
        )

    @staticmethod
    def _seo_plan(user_input: str) -> ExecutionPlan:
        """Create an SEO-analysis execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="seo_1",
                    agent="seo",
                    depends_on=[],
                    required_inputs=["topic"],
                )
            ],
        )

    @staticmethod
    def _content_plan(user_input: str) -> ExecutionPlan:
        """Create a content-generation execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="content_1",
                    agent="content",
                    depends_on=[],
                    required_inputs=["prompt"],
                )
            ],
        )

    @staticmethod
    def _image_plan(user_input: str) -> ExecutionPlan:
        """Create an image-generation execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="image_1",
                    agent="image",
                    depends_on=[],
                    required_inputs=["prompt"],
                )
            ],
        )

    @staticmethod
    def _analytics_plan(user_input: str) -> ExecutionPlan:
        """Create an analytics execution plan."""

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="analytics_1",
                    agent="analytics",
                    depends_on=[],
                    required_inputs=["data"],
                )
            ],
        )

    # =============================================================
    # Campaign plan
    # =============================================================

    @staticmethod
    def _campaign_plan(user_input: str) -> ExecutionPlan:
        """
        Create a dependency-aware multi-agent campaign plan.

        Dependency flow:

            Research
                |
                v
            Competitor
              /   \
             v     v
            SEO  Content
                  |
                  v
                Image
        """

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                # -------------------------------------------------
                # 1. Research
                # -------------------------------------------------
                PlannerTask(
                    id="research_1",
                    agent="research",
                    depends_on=[],
                    required_inputs=["topic"],
                ),

                # -------------------------------------------------
                # 2. Competitor analysis
                # -------------------------------------------------
                PlannerTask(
                    id="competitor_1",
                    agent="competitor",
                    depends_on=["research_1"],
                    required_inputs=["research"],
                ),

                # -------------------------------------------------
                # 3. SEO
                # -------------------------------------------------
                PlannerTask(
                    id="seo_1",
                    agent="seo",
                    depends_on=[
                        "research_1",
                        "competitor_1",
                    ],
                    required_inputs=[
                        "research",
                        "competitor",
                    ],
                ),

                # -------------------------------------------------
                # 4. Content
                # -------------------------------------------------
                PlannerTask(
                    id="content_1",
                    agent="content",
                    depends_on=[
                        "research_1",
                        "competitor_1",
                        "seo_1",
                    ],
                    required_inputs=[
                        "research",
                        "competitor",
                        "seo",
                    ],
                ),

                # -------------------------------------------------
                # 5. Image
                # -------------------------------------------------
                PlannerTask(
                    id="image_1",
                    agent="image",
                    depends_on=["content_1"],
                    required_inputs=["content"],
                ),
            ],
        )

    # =============================================================
    # Request detection helpers
    # =============================================================

    @staticmethod
    def _is_image_request(text: str) -> bool:
        """Detect common image-generation requests."""

        keywords = [
            "generate image",
            "create image",
            "make image",
            "generate a picture",
            "create a picture",
            "marketing image",
            "marketing creative",
            "social media image",
            "instagram image",
            "facebook image",
            "linkedin image",
            "ad creative",
            "advertisement creative",
            "banner",
            "poster",
            "visual creative",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_research_request(text: str) -> bool:
        """Detect common research requests."""

        keywords = [
            "market research",
            "research market",
            "research audience",
            "market trends",
            "customer research",
            "audience research",
            "research trends",
            "research industry",
            "industry research",
            "product research",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_competitor_request(text: str) -> bool:
        """Detect competitor-analysis requests."""

        keywords = [
            "competitor analysis",
            "competitor research",
            "analyze competitors",
            "analyse competitors",
            "competitor comparison",
            "compare competitors",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_seo_request(text: str) -> bool:
        """Detect SEO requests."""

        keywords = [
            "seo analysis",
            "analyze seo",
            "analyse seo",
            "seo audit",
            "seo keywords",
            "keyword research",
            "improve seo",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_content_request(text: str) -> bool:
        """Detect content-generation requests."""

        keywords = [
            "write caption",
            "create caption",
            "generate caption",
            "write blog",
            "create blog",
            "generate blog",
            "social media post",
            "linkedin post",
            "instagram caption",
            "facebook post",
            "marketing copy",
            "ad copy",
            "email campaign",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_analytics_request(text: str) -> bool:
        """Detect analytics requests."""

        keywords = [
            "analyze campaign performance",
            "analyse campaign performance",
            "campaign analytics",
            "marketing analytics",
            "campaign performance",
            "calculate roi",
            "marketing roi",
            "conversion rate",
            "click through rate",
            "ctr",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _is_campaign_request(text: str) -> bool:
        """Determine whether a request requires a campaign workflow."""

        campaign_keywords = [
            "instagram campaign",
            "facebook campaign",
            "linkedin campaign",
            "social media campaign",
            "marketing campaign",
            "campaign strategy",
            "campaign plan",
            "launch campaign",
            "create campaign",
        ]

        return any(
            keyword in text
            for keyword in campaign_keywords
        )