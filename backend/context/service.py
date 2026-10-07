"""Service for managing shared agent context."""

from typing import Any

from backend.context.schemas import SharedContext


class SharedContextService:
    """Manage shared context during agent orchestration."""

    def create_context(
        self,
        user_request: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        brand_profile: dict[str, Any] | None = None,
        knowledge: list[dict[str, Any]] | None = None,
        campaign_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SharedContext:
        """Create a new shared context."""

        return SharedContext(
            user_id=user_id,
            conversation_id=conversation_id,
            user_request=user_request,
            brand_profile=brand_profile or {},
            knowledge=knowledge or [],
            campaign_data=campaign_data or {},
            metadata=metadata or {},
        )

    def add_agent_output(
        self,
        context: SharedContext,
        agent: str,
        output: Any,
    ) -> SharedContext:
        """Add an agent output to shared context."""

        context.add_agent_output(
            agent=agent,
            output=output,
        )

        return context

    def get_agent_output(
        self,
        context: SharedContext,
        agent: str,
    ) -> Any | None:
        """Get an agent's previous output."""

        return context.get_agent_output(agent)

    def get_agent_inputs(
        self,
        context: SharedContext,
        required_inputs: list[str],
    ) -> dict[str, Any]:
        """
        Build a filtered input package for an agent.

        Only requested context fields are returned.
        """

        inputs: dict[str, Any] = {}

        for required_input in required_inputs:
            if required_input == "user_request":
                inputs["user_request"] = context.user_request

            elif required_input == "brand_profile":
                inputs["brand_profile"] = context.brand_profile

            elif required_input == "knowledge":
                inputs["knowledge"] = context.knowledge

            elif required_input == "campaign_data":
                inputs["campaign_data"] = context.campaign_data

            elif required_input in context.agent_outputs:
                inputs[required_input] = (
                    context.agent_outputs[required_input]
                )

        return inputs
