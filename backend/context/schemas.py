"""Schemas for shared agent context."""

from typing import Any

from pydantic import BaseModel, Field


class SharedContext(BaseModel):
    """Context shared across planner and agent execution."""

    user_id: str | None = None
    conversation_id: str | None = None

    user_request: str = ""

    brand_profile: dict[str, Any] = Field(default_factory=dict)

    knowledge: list[dict[str, Any]] = Field(
        default_factory=list
    )

    agent_outputs: dict[str, Any] = Field(
        default_factory=dict
    )

    campaign_data: dict[str, Any] = Field(
        default_factory=dict
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    def add_agent_output(
        self,
        agent: str,
        output: Any,
    ) -> None:
        """Store the output produced by an agent."""

        self.agent_outputs[agent] = output

    def get_agent_output(
        self,
        agent: str,
    ) -> Any | None:
        """Return a previously stored agent output."""

        return self.agent_outputs.get(agent)