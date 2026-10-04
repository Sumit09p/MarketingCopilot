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
from services.agent_run_service import AgentRunService
from services.brand_profile_service import BrandProfileService
from services.knowledge_service import KnowledgeService
from services.llm import LLMService



class MarketingPipelineService:
    """
    Coordinate the complete MarketingOS request pipeline.

    General mode:

        intent detection
        -> brand profile retrieval
        -> knowledge retrieval
        -> planning
        -> plan validation
        -> shared context
        -> dependency-aware orchestration
        -> specialized marketing agents

    Explicit-agent mode:

        agent selection
        -> guardrail
        -> VALID
        -> intent detection
        -> brand profile retrieval
        -> knowledge retrieval
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
        agent_run_service: AgentRunService | None = None,
        knowledge_service: KnowledgeService | None = None,
        brand_profile_service: BrandProfileService | None = None,
    ) -> None:

        # ---------------------------------------------------------
        # 1. Core request services
        # ---------------------------------------------------------

        self.intent_service = IntentDetectionService()

        self.guardrail_service = AgentGuardrailService(
            intent_service=self.intent_service,
        )

        self.planner_service = PlannerService()

        self.plan_validator = PlanValidator()

        self.context_service = SharedContextService()

        # ---------------------------------------------------------
        # 2. Knowledge / RAG service
        # ---------------------------------------------------------

        self.knowledge_service = (
            knowledge_service
            if knowledge_service is not None
            else KnowledgeService()
        )

        # ---------------------------------------------------------
        # 3. Brand Profile service
        # ---------------------------------------------------------

        self.brand_profile_service = (
            brand_profile_service
            if brand_profile_service is not None
            else BrandProfileService()
        )

        # ---------------------------------------------------------
        # 4. LLM service
        # ---------------------------------------------------------

        self.llm_service = llm_service or LLMService()

        # ---------------------------------------------------------
        # 5. Agent execution persistence
        # ---------------------------------------------------------

        self.agent_run_service = (
            agent_run_service
            if agent_run_service is not None
            else AgentRunService()
        )

        # ---------------------------------------------------------
        # 6. Build real agent adapters
        # ---------------------------------------------------------

        if agent_handlers is None:

            generate = build_agent_generator(
                self.llm_service
            )

            agents = build_registry(generate)

            agent_handlers = {
                name: AgentAdapter(agent)
                for name, agent in agents.items()
            }

        # ---------------------------------------------------------
        # 7. Dependency-aware orchestrator
        # ---------------------------------------------------------

        self.orchestrator = OrchestratorService(
            agent_handlers=agent_handlers,
            agent_run_service=self.agent_run_service,
        )

    # =============================================================
    # KNOWLEDGE RETRIEVAL
    # =============================================================

    def _retrieve_knowledge(
        self,
        user_id: str | None,
        user_request: str,
        existing_knowledge: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant knowledge for the current user.

        Explicitly supplied knowledge is preserved.

        Otherwise semantic retrieval is performed against
        the user's private knowledge base.

        RAG failures are non-fatal.
        """

        # ---------------------------------------------------------
        # 1. Preserve explicitly supplied knowledge
        # ---------------------------------------------------------

        if existing_knowledge:
            return existing_knowledge

        # ---------------------------------------------------------
        # 2. Without user ID there is no user-specific RAG
        # ---------------------------------------------------------

        if not user_id:
            return []

        # ---------------------------------------------------------
        # 3. Perform semantic retrieval
        # ---------------------------------------------------------

        try:

            results = self.knowledge_service.search(
                user_id=user_id,
                query=user_request,
                top_k=5,
                min_score=0.0,
            )

            return [
                result.as_dict()
                if hasattr(result, "as_dict")
                else result
                for result in results
            ]

        except Exception:
            # RAG must never crash the complete pipeline.
            return []

    # =============================================================
    # BRAND PROFILE RETRIEVAL
    # =============================================================

    def _retrieve_brand_profile(
        self,
        user_id: str | None,
        existing_brand_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve the authenticated user's saved brand profile.

        Explicitly supplied brand_profile is preserved.

        Otherwise the profile is loaded from MongoDB using user_id.

        Brand profile retrieval is non-fatal. If the user does not
        have a profile or retrieval fails, an empty dictionary is
        returned.
        """

        # ---------------------------------------------------------
        # 1. Preserve explicitly supplied profile
        # ---------------------------------------------------------

        if existing_brand_profile:
            return existing_brand_profile

        # ---------------------------------------------------------
        # 2. No user ID means no user-specific profile
        # ---------------------------------------------------------

        if not user_id:
            return {}

        # ---------------------------------------------------------
        # 3. Retrieve saved profile
        # ---------------------------------------------------------

        try:

            profile = self.brand_profile_service.get_brand_profile(
                user_id=user_id,
            )

            if not profile:
                return {}

            return profile

        except Exception:
            # Brand profile must not crash the pipeline.
            return {}

    # =============================================================
    # MAIN REQUEST PROCESSING
    # =============================================================

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
        # 3. Retrieve user's saved brand profile
        # ---------------------------------------------------------

        retrieved_brand_profile = self._retrieve_brand_profile(
            user_id=user_id,
            existing_brand_profile=brand_profile,
        )

        # ---------------------------------------------------------
        # 4. Retrieve user-specific knowledge
        # ---------------------------------------------------------

        retrieved_knowledge = self._retrieve_knowledge(
            user_id=user_id,
            user_request=user_request,
            existing_knowledge=knowledge,
        )

        # ---------------------------------------------------------
        # 5. Create execution plan
        # ---------------------------------------------------------

        plan = self.planner_service.create_plan(
            user_input=user_request,
            intent=intent_result.intent.value,
        )

        # ---------------------------------------------------------
        # 6. Validate execution plan
        # ---------------------------------------------------------

        self.plan_validator.validate(plan)

        # ---------------------------------------------------------
        # 7. Create shared context
        # ---------------------------------------------------------

        context = self.context_service.create_context(
            user_request=user_request,
            user_id=user_id,
            conversation_id=conversation_id,
            brand_profile=retrieved_brand_profile,
            knowledge=retrieved_knowledge,
            campaign_data=campaign_data,
            metadata=metadata,
        )

        # ---------------------------------------------------------
        # 8. Add explicit-agent information to context
        # ---------------------------------------------------------

        context_data = context.model_dump()

        if selected_agent is not None:
            context_data["selected_agent"] = (
                selected_agent.value
            )

        # ---------------------------------------------------------
        # 9. Execute dependency-aware plan
        # ---------------------------------------------------------

        orchestration_result = self.orchestrator.execute(
            plan=plan,
            context=context_data,
        )

        # ---------------------------------------------------------
        # 10. Return structured result
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
            "brand_profile": {
                "loaded": bool(retrieved_brand_profile),
                "company_name": retrieved_brand_profile.get(
                    "company_name"
                ),
                "industry": retrieved_brand_profile.get(
                    "industry"
                ),
            },
            "knowledge": {
                "retrieved": len(retrieved_knowledge),
                "sources": list(
                    {
                        item.get("source")
                        for item in retrieved_knowledge
                        if isinstance(item, dict)
                        and item.get("source")
                    }
                ),
            },
            "plan": plan.model_dump(
                mode="json"
            ),
            "orchestration": orchestration_result.model_dump(
                mode="json"
            ),
        }

        # ---------------------------------------------------------
        # 11. Include guardrail result when explicit agent used
        # ---------------------------------------------------------

        if guardrail_result is not None:
            result["guardrail"] = (
                guardrail_result.model_dump(
                    mode="json"
                )
            )

        return result