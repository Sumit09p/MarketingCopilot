"""Schemas for orchestrator execution state and results."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from planner.schemas import PlannerTask


class TaskStatus(str, Enum):
    """Possible execution states for an orchestrator task."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class TaskExecution(BaseModel):
    """Runtime state and result of one planner task."""

    task: PlannerTask
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None
    attempts: int = Field(default=0, ge=0)


class OrchestrationResult(BaseModel):
    """Final result of an orchestration run."""

    status: str
    tasks: list[TaskExecution]
    final_result: Any | None = None