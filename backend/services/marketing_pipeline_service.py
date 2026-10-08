"""Central marketing request processing pipeline."""

from typing import Any, Callable

from backend.agents.adapter import AgentAdapter
from backend.agents.llm_adapter import build_agent_generator
from backend.agents.registry import build_registry

from backend.context.service import SharedContextService

from backend.guardrails.schemas import AgentType, GuardrailDecision
from backend.guardrails.service import AgentGuardrailService

from backend.intent.service import IntentDetectionService

from backend.orchestrator.service import OrchestratorService

from backend.planner.service import (
    PlannerClarificationError,
    PlannerService,
)

from backend.planner.validator import PlanValidator

from backend.services.agent_run_service import AgentRunService
from backend.services.brand_profile_service import BrandProfileService
from backend.services.knowledge_service import KnowledgeService
from backend.services.llm import LLMService


class MarketingPipelineService:
    """
    Coordinate the complete MarketingOS request pipeline.

    General mode:

        intent detection
        -> brand profile retrieval
        -> knowledge retrieval
        -> conversation context
        -> Gemini planner
        -> clarification OR execution plan
        -> plan validation
        -> shared context
        -> dependency-aware orchestration
        -> specialized marketing agents

    Explicit-agent mode:

        agent selection
        -> guardrail compatibility check
        -> intent detection
        -> brand profile retrieval
        -> knowledge retrieval
        -> conversation context
        -> Gemini planner
        -> clarification OR execution plan
        -> plan validation
        -> shared context
        -> orchestration

    Important:

    Clarification questions are NOT generated here.

    Gemini Planner decides:
        - whether clarification is required
        - what information is missing
        - how to ask for it

    Brand Profile, RAG and conversation history are supplied to
    the planner so the system does not repeatedly ask for information
    that is already available.
    """

    def __init__(
        self,
        agent_handlers: dict[str, Callable[..., Any]] | None = None,
        llm_service: LLMService | None = None,
        agent_run_service: AgentRunService | None = None,
        knowledge_service: KnowledgeService | None = None,
        brand_profile_service: BrandProfileService | None = None,
    ) -> None:

        # =========================================================
        # 1. Core request services
        # =========================================================

        self.intent_service = IntentDetectionService()

        self.guardrail_service = AgentGuardrailService(
            intent_service=self.intent_service,
        )

        self.plan_validator = PlanValidator()

        self.context_service = SharedContextService()

        # =========================================================
        # 2. Knowledge / RAG service
        # =========================================================

        self.knowledge_service = knowledge_service

        # =========================================================
        # 3. Brand Profile service
        # =========================================================

        self.brand_profile_service = brand_profile_service

        # =========================================================
        # 4. LLM service
        # =========================================================

        self.llm_service = llm_service or LLMService()

        # =========================================================
        # 5. Planner
        # =========================================================

        self.planner_service = PlannerService(
            llm_service=self.llm_service,
        )

        # =========================================================
        # 6. Agent execution persistence
        # =========================================================

        self.agent_run_service = (
            agent_run_service
            if agent_run_service is not None
            else AgentRunService()
        )

        # =========================================================
        # 7. Build real agent adapters
        # =========================================================

        if agent_handlers is None:

            generate = build_agent_generator(
                self.llm_service
            )

            agents = build_registry(generate)

            agent_handlers = {
                name: AgentAdapter(agent)
                for name, agent in agents.items()
            }

        # =========================================================
        # 8. Dependency-aware orchestrator
        # =========================================================

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

            service = self.knowledge_service

            if service is None:
                service = KnowledgeService()
                self.knowledge_service = service

            results = service.search(
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

        Brand profile retrieval is non-fatal.
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

            service = self.brand_profile_service

            if service is None:
                service = BrandProfileService()
                self.brand_profile_service = service

            profile = service.get_brand_profile(
                user_id=user_id,
            )

            if not profile:
                return {}

            return profile

        except Exception:
            # Brand profile must not crash the pipeline.
            return {}

    # =============================================================
    # CONVERSATION CONTEXT
    # =============================================================

    @staticmethod
    def _normalize_conversation_history(
        conversation_history: list[Any] | None,
    ) -> list[dict[str, str]]:
        """
        Normalize conversation history into a planner-friendly format.

        Supported inputs:
            {"role": "...", "content": "..."}
            objects with .role and .content

        Only useful textual messages are retained.
        """

        if not conversation_history:
            return []

        normalized: list[dict[str, str]] = []

        for message in conversation_history:

            if isinstance(message, dict):

                role = message.get("role")
                content = message.get("content")

            else:

                role = getattr(
                    message,
                    "role",
                    None,
                )

                content = getattr(
                    message,
                    "content",
                    None,
                )

            if not role or not content:
                continue

            content = str(content).strip()

            if not content:
                continue

            normalized.append(
                {
                    "role": str(role),
                    "content": content,
                }
            )

        return normalized

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
        conversation_history: list[Any] | None = None,
    ) -> dict[str, Any]:
        """
        Process a marketing request.

        The planner is responsible for deciding whether the request
        contains enough information to execute.

        Clarification questions are generated by Gemini through
        PlannerService.

        Existing brand profile, RAG knowledge and conversation history
        are supplied to Gemini to avoid repeatedly asking for known
        business information.
        """

        # =========================================================
        # 1. Explicit-agent guardrail
        # =========================================================

        guardrail_result = None

        if selected_agent is not None:
            if isinstance(selected_agent, str):
                selected_agent = AgentType(selected_agent)

            guardrail_result = self.guardrail_service.evaluate(
                agent=selected_agent,
                user_input=user_request,
            )

            # -----------------------------------------------------
            # INVALID
            #
            # This remains a guardrail concern.
            # Do NOT send clearly incompatible requests to an agent.
            # -----------------------------------------------------

            if (
                guardrail_result.decision
                == GuardrailDecision.INVALID
            ):

                return {
                    "mode": "EXPLICIT_AGENT",
                    "status": "INVALID",
                    "guardrail": guardrail_result.model_dump(
                        mode="json"
                    ),
                    "intent": {
                        "type": (
                            guardrail_result
                            .detected_intent
                            .value
                        ),
                        "confidence": (
                            guardrail_result.confidence
                        ),
                        "reasoning": (
                            guardrail_result.reason
                        ),
                    },
                    "plan": None,
                    "orchestration": None,
                }

            # -----------------------------------------------------
            # IMPORTANT
            #
            # DO NOT return here for guardrail
            # NEEDS_CLARIFICATION.
            #
            # Gemini Planner must make the clarification decision
            # because it has access to:
            #
            #   - current request
            #   - brand profile
            #   - RAG
            #   - conversation history
            #
            # Therefore all clarification is centralized through
            # Gemini.
            # -----------------------------------------------------

        # =========================================================
        # 2. Detect intent
        # =========================================================

        intent_result = self.intent_service.detect(
            user_request
        )

        # =========================================================
        # 3. Retrieve user's saved brand profile
        # =========================================================

        retrieved_brand_profile = (
            self._retrieve_brand_profile(
                user_id=user_id,
                existing_brand_profile=brand_profile,
            )
        )

        # =========================================================
        # 4. Retrieve user-specific knowledge / RAG
        # =========================================================

        retrieved_knowledge = self._retrieve_knowledge(
            user_id=user_id,
            user_request=user_request,
            existing_knowledge=knowledge,
        )

        # =========================================================
        # 5. Normalize conversation history
        # =========================================================

        normalized_history = (
            self._normalize_conversation_history(
                conversation_history
            )
        )

        # =========================================================
        # 6. Gemini Planner
        # =========================================================

        try:

            plan = self.planner_service.create_plan(
                user_input=user_request,
                intent=intent_result.intent.value,
                brand_profile=retrieved_brand_profile,
                knowledge=retrieved_knowledge,
                conversation_history=normalized_history,
                selected_agent=(
        selected_agent.value
        if selected_agent is not None
        else None),
            )

        except PlannerClarificationError as exc:

            # -----------------------------------------------------
            # Gemini decided that more information is required.
            #
            # No agent executes.
            # -----------------------------------------------------

            return {
                "mode": (
                    "EXPLICIT_AGENT"
                    if selected_agent is not None
                    else "GENERAL"
                ),
                "status": "NEEDS_CLARIFICATION",
                "clarification": {
                    "question": exc.question,
                    "questions": exc.questions,
                },
                "intent": {
                    "type": intent_result.intent.value,
                    "confidence": intent_result.confidence,
                    "reasoning": intent_result.reasoning,
                },
                "brand_profile": {
                    "loaded": bool(
                        retrieved_brand_profile
                    ),
                    "company_name": (
                        retrieved_brand_profile.get(
                            "company_name"
                        )
                    ),
                    "industry": (
                        retrieved_brand_profile.get(
                            "industry"
                        )
                    ),
                },
                "knowledge": {
                    "retrieved": len(
                        retrieved_knowledge
                    ),
                    "sources": list(
                        {
                            item.get("source")
                            for item in retrieved_knowledge
                            if isinstance(item, dict)
                            and item.get("source")
                        }
                    ),
                },
                "plan": None,
                "orchestration": None,
            }

        # =========================================================
        # 7. Validate execution plan
        # =========================================================

        self.plan_validator.validate(plan)

        # =========================================================
        # 8. Create shared context
        # =========================================================

        context = self.context_service.create_context(
            user_request=user_request,
            user_id=user_id,
            conversation_id=conversation_id,
            brand_profile=retrieved_brand_profile,
            knowledge=retrieved_knowledge,
            campaign_data=campaign_data,
            metadata=metadata,
        )

        # =========================================================
        # 9. Add pipeline-level context
        # =========================================================

        context_data = context.model_dump()

        # ---------------------------------------------------------
        # Conversation history
        # ---------------------------------------------------------

        context_data["conversation_history"] = (
            normalized_history
        )

        # ---------------------------------------------------------
        # Explicit selected agent
        # ---------------------------------------------------------

        if selected_agent is not None:

            context_data["selected_agent"] = (
                selected_agent.value
            )

        # =========================================================
        # 10. Execute dependency-aware plan
        # =========================================================

        orchestration_result = self.orchestrator.execute(
            plan=plan,
            context=context_data,
        )

        # =========================================================
        # 11. Return structured result
        # =========================================================

        result = {
            "mode": (
                "EXPLICIT_AGENT"
                if selected_agent is not None
                else "GENERAL"
            ),
            "status": "COMPLETED",
            "intent": {
                "type": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
            },
            "brand_profile": {
                "loaded": bool(
                    retrieved_brand_profile
                ),
                "company_name": (
                    retrieved_brand_profile.get(
                        "company_name"
                    )
                ),
                "industry": (
                    retrieved_brand_profile.get(
                        "industry"
                    )
                ),
            },
            "knowledge": {
                "retrieved": len(
                    retrieved_knowledge
                ),
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
            "orchestration": (
                orchestration_result.model_dump(
                    mode="json"
                )
            ),
        }

        # =========================================================
        # 12. Include guardrail result when explicit agent used
        # =========================================================

        if guardrail_result is not None:

            result["guardrail"] = (
                guardrail_result.model_dump(
                    mode="json"
                )
            )

        return result
