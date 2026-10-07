"""Schemas for planner tasks and execution plans."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.guardrails.schemas import AgentType


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


class PlannerDecision(BaseModel):
    """
    Final decision produced by the LLM planner.

    READY:
        The request contains enough information and an execution
        plan can be safely executed.

    NEEDS_CLARIFICATION:
        More information is required before execution.
    """

    status: Literal["READY", "NEEDS_CLARIFICATION"]

    clarification_question: str | None = None

    clarification_questions: list[str] = Field(
        default_factory=list
    )

    plan: ExecutionPlan | None = None
