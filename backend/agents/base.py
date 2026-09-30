from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


GenerateFn = Callable[[str], str]


@dataclass
class AgentResult:
    agent: str
    status: str
    summary: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    confidence: Optional[float] = None
    task_id: Optional[str] = field(default=None, repr=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "status": self.status,
            "summary": self.summary,
            "data": self.data,
            "error": self.error,
            "confidence": self.confidence,
        }


class BaseAgent:
    name = ""

    def __init__(self, generate: GenerateFn):
        self.generate = generate

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        raise NotImplementedError

    def _ok(
        self,
        task_id: str,
        summary: str,
        data: dict[str, Any],
        confidence: float = 0.8,
    ) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status="COMPLETED",
            summary=summary,
            data=data,
            error=None,
            confidence=confidence,
            task_id=task_id,
        )

    def _fail(self, task_id: str, error: str) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status="FAILED",
            summary=None,
            data=None,
            error=f"[{self.name} / {task_id}] {error}",
            confidence=None,
            task_id=task_id,
        )

    def call_llm(self, prompt: str) -> str:
        return self.generate(prompt)

    def parse_json(self, raw: str) -> dict[str, Any]:
        text = (raw or "").strip()
        if not text:
            raise ValueError("LLM returned an empty response.")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("LLM JSON must be an object.")
        return parsed
