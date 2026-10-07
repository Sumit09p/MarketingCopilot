"""Service for validating requests against selected agents."""

from guardrails.schemas import (
    AgentType,
    GuardrailDecision,
    GuardrailResult,
)
from intent.schemas import IntentType
from intent.service import IntentDetectionError, IntentDetectionService


class GuardrailEvaluationError(Exception):
    """Raised when guardrail evaluation cannot be completed."""


class AgentGuardrailService:
    """Evaluate whether a request is appropriate for a selected agent."""

    def __init__(
        self,
        intent_service: IntentDetectionService | None = None,
    ) -> None:
        self.intent_service = (
            intent_service or IntentDetectionService()
        )

    def evaluate(
        self,
        agent: AgentType,
        user_input: str,
    ) -> GuardrailResult:
        """
        Evaluate whether the selected agent should handle the request.

        The guardrail first detects the user's intent and then evaluates
        whether the selected agent can appropriately handle that intent.
        """

        if not user_input or not user_input.strip():
            raise GuardrailEvaluationError(
                "User input cannot be empty."
            )

        try:
            intent_result = self.intent_service.detect(
                user_input
            )
        except IntentDetectionError as exc:
            raise GuardrailEvaluationError(
                str(exc)
            ) from exc

        intent = intent_result.intent

        # ---------------------------------------------------------
        # 1. Explicitly vague request
        # ---------------------------------------------------------
        #
        # Example:
        #   Content + "Write something"
        #   Content + "Make something good"
        #
        # These are not clearly incompatible with the selected
        # agent. They are relevant but lack sufficient information.
        #
        # Therefore they must be evaluated BEFORE _is_invalid().
        # ---------------------------------------------------------

        if self._needs_clarification(
            agent,
            intent,
            user_input,
        ):
            missing_information = self._missing_information(
                agent,
                user_input,
            )

            return GuardrailResult(
                decision=GuardrailDecision.NEEDS_CLARIFICATION,
                agent=agent,
                detected_intent=intent,
                confidence=intent_result.confidence,
                reason=self._clarification_reason(agent),
                missing_information=missing_information,
            )

        # ---------------------------------------------------------
        # 2. Clearly incompatible request
        # ---------------------------------------------------------

        if self._is_invalid(
            agent,
            intent,
        ):
            return GuardrailResult(
                decision=GuardrailDecision.INVALID,
                agent=agent,
                detected_intent=intent,
                confidence=intent_result.confidence,
                reason=self._invalid_reason(
                    agent,
                    intent,
                ),
            )

        # ---------------------------------------------------------
        # 3. Valid request
        # ---------------------------------------------------------

        return GuardrailResult(
            decision=GuardrailDecision.VALID,
            agent=agent,
            detected_intent=intent,
            confidence=intent_result.confidence,
            reason=self._valid_reason(
                agent,
                intent,
            ),
        )

    # =============================================================
    # INVALID REQUEST CHECK
    # =============================================================

    @staticmethod
    def _is_invalid(
        agent: AgentType,
        intent: IntentType,
    ) -> bool:
        """Return whether an intent is incompatible with an agent."""

        compatible_intents: dict[
            AgentType,
            set[IntentType],
        ] = {
            AgentType.RESEARCH: {
                IntentType.RESEARCH,
            },
            AgentType.COMPETITOR: {
                IntentType.COMPETITOR_ANALYSIS,
            },
            AgentType.SEO: {
                IntentType.SEO_ANALYSIS,
            },
            AgentType.CONTENT: {
                IntentType.CONTENT_GENERATION,
            },
            AgentType.IMAGE: {
                IntentType.IMAGE_GENERATION,
            },
            AgentType.ANALYTICS: {
                IntentType.ANALYTICS,
            },
        }

        return intent not in compatible_intents[agent]

    # =============================================================
    # CLARIFICATION CHECK
    # =============================================================

    @staticmethod
    def _needs_clarification(
        agent: AgentType,
        intent: IntentType,
        user_input: str,
    ) -> bool:
        """
        Return whether a relevant request lacks important information.

        General intent is normally handled by the general planner.

        However, explicitly vague requests such as:
            "Write something"
            "Create something"
            "Make something good"

        can still be recognized as requests for a selected
        specialized agent and therefore require clarification.
        """

        normalized_input = user_input.strip().lower()

        if not normalized_input:
            return True

        # ---------------------------------------------------------
        # CONTENT
        # ---------------------------------------------------------

        if agent == AgentType.CONTENT:

            vague_content_requests = {
                "write something",
                "create something",
                "make something",
                "write",
                "create",
                "make",
                "make something good",
                "create something good",
                "write something good",
            }

            if normalized_input in vague_content_requests:
                return True

            # Very short content requests are ambiguous.
            if (
                intent == IntentType.CONTENT_GENERATION
                and len(normalized_input) < 15
            ):
                return True

        # ---------------------------------------------------------
        # SEO
        # ---------------------------------------------------------

        if (
            agent == AgentType.SEO
            and intent == IntentType.SEO_ANALYSIS
        ):
            return not any(
                indicator in normalized_input
                for indicator in [
                    "website",
                    "url",
                    "domain",
                    "page",
                    "seo audit",
                    "seo analysis",
                    "keyword",
                ]
            )

        # ---------------------------------------------------------
        # IMAGE
        # ---------------------------------------------------------

        if (
            agent == AgentType.IMAGE
            and intent == IntentType.IMAGE_GENERATION
        ):
            return len(normalized_input) < 15

        # ---------------------------------------------------------
        # RESEARCH
        # ---------------------------------------------------------

        if (
            agent == AgentType.RESEARCH
            and intent == IntentType.RESEARCH
        ):
            return len(normalized_input) < 15

        # ---------------------------------------------------------
        # COMPETITOR
        # ---------------------------------------------------------

        if (
            agent == AgentType.COMPETITOR
            and intent == IntentType.COMPETITOR_ANALYSIS
        ):
            return len(normalized_input) < 15

        # ---------------------------------------------------------
        # ANALYTICS
        # ---------------------------------------------------------

        if (
            agent == AgentType.ANALYTICS
            and intent == IntentType.ANALYTICS
        ):
            return len(normalized_input) < 15

        return False

    # =============================================================
    # MISSING INFORMATION
    # =============================================================

    @staticmethod
    def _missing_information(
        agent: AgentType,
        user_input: str,
    ) -> list[str]:
        """Return information needed to make an ambiguous request actionable."""

        if agent == AgentType.SEO:
            return [
                "website URL, domain, page, or existing SEO context"
            ]

        if agent == AgentType.CONTENT:
            return [
                "content type, topic, product, or campaign context"
            ]

        if agent == AgentType.IMAGE:
            return [
                "creative purpose, subject, or campaign context"
            ]

        if agent == AgentType.RESEARCH:
            return [
                "research topic or market context"
            ]

        if agent == AgentType.COMPETITOR:
            return [
                "competitor, company, product, or market context"
            ]

        if agent == AgentType.ANALYTICS:
            return [
                "campaign, metric, or analytics context"
            ]

        return []

    # =============================================================
    # REASONS
    # =============================================================

    @staticmethod
    def _invalid_reason(
        agent: AgentType,
        intent: IntentType,
    ) -> str:
        """Explain why the request is incompatible with the agent."""

        return (
            f"The detected intent '{intent.value}' is not appropriate "
            f"for the {agent.value} agent."
        )

    @staticmethod
    def _clarification_reason(
        agent: AgentType,
    ) -> str:
        """Explain why additional information is required."""

        return (
            f"The request is relevant to the {agent.value} agent, "
            "but additional information is required before execution."
        )

    @staticmethod
    def _valid_reason(
        agent: AgentType,
        intent: IntentType,
    ) -> str:
        """Explain why the request can be handled."""

        return (
            f"The detected intent '{intent.value}' is compatible "
            f"with the {agent.value} agent."
        )