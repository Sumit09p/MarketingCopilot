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

        try:
            intent_result = self.intent_service.detect(user_input)
        except IntentDetectionError as exc:
            raise GuardrailEvaluationError(str(exc)) from exc

        intent = intent_result.intent

        if self._is_invalid(agent, intent):
            return GuardrailResult(
                decision=GuardrailDecision.INVALID,
                agent=agent,
                detected_intent=intent,
                confidence=intent_result.confidence,
                reason=self._invalid_reason(agent, intent),
            )

        if self._needs_clarification(agent, intent, user_input):
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

        return GuardrailResult(
            decision=GuardrailDecision.VALID,
            agent=agent,
            detected_intent=intent,
            confidence=intent_result.confidence,
            reason=self._valid_reason(agent, intent),
        )

    @staticmethod
    def _is_invalid(
        agent: AgentType,
        intent: IntentType,
    ) -> bool:
        """Return whether an intent is incompatible with an agent."""

        compatible_intents: dict[AgentType, set[IntentType]] = {
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

    @staticmethod
    def _needs_clarification(
        agent: AgentType,
        intent: IntentType,
        user_input: str,
    ) -> bool:
        """
        Return whether a relevant request lacks important information.

        General intent is not treated as clarification here because it
        is normally handled by the general planner rather than an
        explicitly selected specialized agent.
        """

        if not user_input.strip():
            return True

        if agent == AgentType.SEO and intent == IntentType.SEO_ANALYSIS:
            return not any(
                indicator in user_input.lower()
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

        if (
            agent == AgentType.CONTENT
            and intent == IntentType.CONTENT_GENERATION
        ):
            vague_content_requests = {
                "write something",
                "create something",
                "make something",
                "write",
                "create",
                "make",
            }

            normalized_input = user_input.strip().lower()

            if normalized_input in vague_content_requests:
                return True

            return len(user_input.strip()) < 15

        if (
            agent == AgentType.IMAGE
            and intent == IntentType.IMAGE_GENERATION
        ):
            return len(user_input.strip()) < 15

        if (
            agent == AgentType.RESEARCH
            and intent == IntentType.RESEARCH
        ):
            return len(user_input.strip()) < 15

        if (
            agent == AgentType.COMPETITOR
            and intent == IntentType.COMPETITOR_ANALYSIS
        ):
            return len(user_input.strip()) < 15

        if (
            agent == AgentType.ANALYTICS
            and intent == IntentType.ANALYTICS
        ):
            return len(user_input.strip()) < 15

        return False

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