"""Schemas for planner tasks and execution plans."""

from pydantic import BaseModel, Field

from guardrails.schemas import AgentType


class PlannerTask(BaseModel):
    """A single task proposed by the planner."""

    id: str = Field(min_length=1)
    agent: AgentType
    depends_on: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """Structured execution plan proposed by the planner."""

    goal: str = Field(min_length=1)
    tasks: list[PlannerTask] = Field(min_length=1)
    