"""Adapters connecting marketing agents to the orchestration layer."""

from typing import Any

from backend.agents.base import BaseAgent
from backend.planner.schemas import PlannerTask


class AgentAdapter:
    """Adapt a BaseAgent to the orchestrator handler contract."""

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent

    def __call__(
        self,
        task: PlannerTask,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the agent and return a serializable result."""

        result = self.agent.run(
            task_id=task.id,
            input_data=inputs,
            context=context,
        )

        return result.as_dict()
