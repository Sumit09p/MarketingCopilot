"""Central marketing request processing pipeline."""

from typing import Any, Callable

from agents.adapter import AgentAdapter
from agents.llm_adapter import build_agent_generator
from agents.registry import build_registry
from context.service import SharedContextService
from guardrails.schemas import AgentType, GuardrailDecision
from guardrails.service import AgentGuardrailService
from intent.service import IntentDetectionService
from orchestrator.service import OrchestratorService
from planner.service import PlannerService
from planner.validator import PlanValidator
from services.llm import LLMService


class MarketingPipelineService:
    """
    Coordinate the complete MarketingOS request pipeline.

    General mode:

        intent detection
        -> planning
        -> plan validation
        -> shared context
        -> dependency-aware orchestration
        -> specialized marketing agents

    Explicit-agent mode:

        agent selection
        -> guardrail
        -> VALID
        -> planning
        -> plan validation
        -> shared context
        -> orchestration

        or

        NEEDS_CLARIFICATION
        -> no agent execution

        or

        INVALID
        -> no agent execution
    """

    def __init__(
        self,
        agent_handlers: dict[str, Callable[..., Any]] | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.intent_service = IntentDetectionService()

        self.guardrail_service = AgentGuardrailService(
            intent_service=self.intent_service,
        )

        self.planner_service = PlannerService()

        self.plan_validator = PlanValidator()

        self.context_service = SharedContextService()

        self.llm_service = llm_service or LLMService()

        if agent_handlers is None:
            generate = build_agent_generator(
                self.llm_service
            )

            agents = build_registry(generate)

            agent_handlers = {
                name: AgentAdapter(agent)
                for name, agent in agents.items()
            }

        self.orchestrator = OrchestratorService(
            agent_handlers=agent_handlers,
        )

    def process_request(
        self,
        user_request: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        brand_profile: dict[str, Any] | None = None,
        knowledge: list[dict[str, Any]] | None = None,
        campaign_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        selected_agent: AgentType | None = None,
    ) -> dict[str, Any]:
        """
        Process a marketing request.

        If selected_agent is None:
            the request follows General Mode.

        If selected_agent is provided:
            the selected agent is evaluated by the guardrail
            before any execution takes place.
        """

        # ---------------------------------------------------------
        # 1. Guardrail for explicitly selected agent
        # ---------------------------------------------------------

        guardrail_result = None

        if selected_agent is not None:

            guardrail_result = self.guardrail_service.evaluate(
                agent=selected_agent,
                user_input=user_request,
            )

            # -----------------------------------------------------
            # INVALID
            # -----------------------------------------------------

            if (
                guardrail_result.decision
                == GuardrailDecision.INVALID
            ):
                return {
                    "mode": "EXPLICIT_AGENT",
                    "guardrail": guardrail_result.model_dump(
                        mode="json"
                    ),
                    "intent": {
                        "type": guardrail_result.detected_intent.value,
                        "confidence": guardrail_result.confidence,
                        "reasoning": guardrail_result.reason,
                    },
                    "plan": None,
                    "orchestration": None,
                }

            # -----------------------------------------------------
            # NEEDS CLARIFICATION
            # -----------------------------------------------------

            if (
                guardrail_result.decision
                == GuardrailDecision.NEEDS_CLARIFICATION
            ):
                return {
                    "mode": "EXPLICIT_AGENT",
                    "guardrail": guardrail_result.model_dump(
                        mode="json"
                    ),
                    "intent": {
                        "type": guardrail_result.detected_intent.value,
                        "confidence": guardrail_result.confidence,
                        "reasoning": guardrail_result.reason,
                    },
                    "plan": None,
                    "orchestration": None,
                }

        # ---------------------------------------------------------
        # 2. Detect intent
        # ---------------------------------------------------------

        intent_result = self.intent_service.detect(
            user_request
        )

        # ---------------------------------------------------------
        # 3. Create execution plan
        # ---------------------------------------------------------

        plan = self.planner_service.create_plan(
            user_input=user_request,
            intent=intent_result.intent.value,
        )

        # ---------------------------------------------------------
        # 4. Validate execution plan
        # ---------------------------------------------------------

        self.plan_validator.validate(plan)

        # ---------------------------------------------------------
        # 5. Create shared context
        # ---------------------------------------------------------
        #
        # IMPORTANT:
        # The shared-memory architecture remains unchanged.
        #
        # The user request, brand profile, knowledge,
        # campaign data and metadata are stored in the
        # SharedContextService.
        # ---------------------------------------------------------

        context = self.context_service.create_context(
            user_request=user_request,
            user_id=user_id,
            conversation_id=conversation_id,
            brand_profile=brand_profile,
            knowledge=knowledge,
            campaign_data=campaign_data,
            metadata=metadata,
        )

        # ---------------------------------------------------------
        # 6. Add explicit-agent information to context
        #
        # This is contextual metadata, NOT task execution input.
        # ---------------------------------------------------------

        context_data = context.model_dump()

        if selected_agent is not None:
            context_data["selected_agent"] = (
                selected_agent.value
            )

        # ---------------------------------------------------------
        # 7. Execute dependency-aware plan
        # ---------------------------------------------------------

        orchestration_result = self.orchestrator.execute(
            plan=plan,
            context=context_data,
        )

        # ---------------------------------------------------------
        # 8. Return structured result
        # ---------------------------------------------------------

        result = {
            "mode": (
                "EXPLICIT_AGENT"
                if selected_agent is not None
                else "GENERAL"
            ),
            "intent": {
                "type": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
            },
            "plan": plan.model_dump(
                mode="json"
            ),
            "orchestration": orchestration_result.model_dump(
                mode="json"
            ),
        }

        if guardrail_result is not None:
            result["guardrail"] = (
                guardrail_result.model_dump(
                    mode="json"
                )
            )

        return result