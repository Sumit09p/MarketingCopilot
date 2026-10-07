"""MongoDB document helpers for agent execution runs."""

from datetime import datetime
from typing import Any


AGENT_RUNS_COLLECTION = "agent_runs"


def build_agent_run_document(
    *,
    user_id: str | None,
    conversation_id: str | None,
    task_id: str,
    agent: str,
    input_data: dict[str, Any] | None,
    status: str,
    attempt: int,
    created_at: datetime,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    result: Any = None,
    confidence: float | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """
    Build a MongoDB document representing one agent execution.
    """

    return {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "task_id": task_id,
        "agent": agent,
        "input": input_data or {},
        "status": status,
        "attempt": attempt,
        "created_at": created_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "result": result,
        "confidence": confidence,
        "error": error,
    }


def agent_run_document_to_response(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Convert an agent-run MongoDB document to a safe response."""

    return {
        "id": str(document["_id"]),
        "user_id": document.get("user_id"),
        "conversation_id": document.get(
            "conversation_id"
        ),
        "task_id": document["task_id"],
        "agent": document["agent"],
        "input": document.get("input", {}),
        "status": document["status"],
        "attempt": document.get("attempt", 1),
        "created_at": document.get("created_at"),
        "started_at": document.get("started_at"),
        "completed_at": document.get("completed_at"),
        "result": document.get("result"),
        "confidence": document.get("confidence"),
        "error": document.get("error"),
    }