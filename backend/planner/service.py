"""Service for creating structured execution plans."""

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

        This initial implementation uses deterministic planning rules.
        It does not call an external LLM.

        The planner is responsible for deciding which specialized
        agents are required and how those agents depend on each other.

        The returned plan is intended to be validated by PlanValidator
        before being passed to the orchestrator.
        """

        if not user_input or not user_input.strip():
            raise ValueError("User input cannot be empty.")

        normalized_input = user_input.strip().lower()

        normalized_intent = (
            intent.strip().upper()
            if intent is not None
            else None
        )

        # Explicit intent-based planning.
        if normalized_intent == "RESEARCH":
            return self._research_plan(user_input)

        if normalized_intent == "COMPETITOR_ANALYSIS":
            return self._competitor_plan(user_input)

        if normalized_intent == "SEO_ANALYSIS":
            return self._seo_plan(user_input)

        if normalized_intent == "CONTENT_GENERATION":
            return self._content_plan(user_input)

        if normalized_intent == "IMAGE_GENERATION":
            return self._image_plan(user_input)

        if normalized_intent == "ANALYTICS":
            return self._analytics_plan(user_input)

        # Multi-agent campaign planning.
        if self._is_campaign_request(normalized_input):
            return self._campaign_plan(user_input)

        # If no specialized plan can be determined, fail explicitly
        # instead of returning an invalid execution plan.
        raise ValueError(
            "Unable to create a specialized execution plan "
            "for the provided request."
        )

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
                    required_inputs=[],
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
                    required_inputs=[],
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
                    required_inputs=[],
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
                    required_inputs=[],
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
                    required_inputs=[],
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
                    required_inputs=[],
                )
            ],
        )

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

        Research runs first.

        Competitor analysis depends on research.

        SEO depends on both research and competitor analysis.

        Content depends on research, competitor analysis,
        and SEO.

        Image generation depends on the completed content.
        """

        return ExecutionPlan(
            goal=user_input,
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent="research",
                    depends_on=[],
                    required_inputs=[],
                ),
                PlannerTask(
                    id="competitor_1",
                    agent="competitor",
                    depends_on=["research_1"],
                    required_inputs=["research"],
                ),
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
                PlannerTask(
                    id="image_1",
                    agent="image",
                    depends_on=["content_1"],
                    required_inputs=["content"],
                ),
            ],
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