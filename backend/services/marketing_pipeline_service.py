"""Central marketing request processing pipeline."""

from typing import Any, Callable

from context.service import SharedContextService
from guardrails.schemas import AgentType
from intent.service import IntentDetectionService
from orchestrator.schemas import OrchestrationResult
from orchestrator.service import OrchestratorService
from planner.service import PlannerService
from planner.validator import PlanValidator


class MarketingPipelineService:
    """
    Coordinate the complete marketing request pipeline.

    The pipeline is responsible for connecting:
    intent detection -> planning -> validation ->
    shared context -> orchestration.
    """

    def __init__(
        self,
        agent_handlers: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.intent_service = IntentDetectionService()
        self.planner_service = PlannerService()
        self.plan_validator = PlanValidator()
        self.context_service = SharedContextService()

        self.orchestrator = OrchestratorService(
            agent_handlers=agent_handlers or {},
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
    ) -> dict[str, Any]:
        """
        Process a marketing request through the complete pipeline.
        """

        # --------------------------------------------------
        # 1. Detect intent
        # --------------------------------------------------

        intent_result = self.intent_service.detect(
            user_request
        )

        # --------------------------------------------------
        # 2. Create execution plan
        # --------------------------------------------------

        plan = self.planner_service.create_plan(
            user_input=user_request,
            intent=intent_result.intent.value,
        )

        # --------------------------------------------------
        # 3. Validate execution plan
        # --------------------------------------------------

        self.plan_validator.validate(plan)

        # --------------------------------------------------
        # 4. Create shared context
        # --------------------------------------------------

        context = self.context_service.create_context(
            user_request=user_request,
            user_id=user_id,
            conversation_id=conversation_id,
            brand_profile=brand_profile,
            knowledge=knowledge,
            campaign_data=campaign_data,
            metadata=metadata,
        )

        # --------------------------------------------------
        # 5. Execute dependency-aware plan
        # --------------------------------------------------

        orchestration_result = self.orchestrator.execute(
            plan=plan,
            context=context.model_dump(),
        )

        # --------------------------------------------------
        # 6. Return structured pipeline result
        # --------------------------------------------------

        return {
            "intent": {
                "type": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
            },
            "plan": plan.model_dump(mode="json"),
            "orchestration": orchestration_result.model_dump(
                mode="json"
            ),
        }