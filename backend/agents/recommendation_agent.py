from __future__ import annotations

import json
from typing import Any

from .base import AgentResult, BaseAgent


class RecommendationAgent(BaseAgent):
    """Combines previously generated marketing outputs into recommendations."""

    name = "recommendation"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        try:
            if not input_data:
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="Agent outputs are required.",
                )

            prompt = self._build_prompt(input_data)

            raw = self.generate(prompt)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="Model returned invalid JSON.",
                )

            if not isinstance(data, dict):
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="Recommendation output must be a JSON object.",
                )

            recommendations = data.get("recommendations")
            priority_actions = data.get("priority_actions")

            if not isinstance(recommendations, list):
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="recommendations must be a list.",
                )

            if not isinstance(priority_actions, list):
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="priority_actions must be a list.",
                )

            if len(recommendations) != 3:
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="Exactly 3 recommendations are required.",
                )

            if len(priority_actions) != 2:
                return AgentResult(
                    status="FAILED",
                    agent=self.name,
                    task_id=task_id,
                    data=None,
                    error="Exactly 2 priority actions are required.",
                )

            return AgentResult(
                status="COMPLETED",
                agent=self.name,
                task_id=task_id,
                data={
                    "recommendations": recommendations,
                    "priority_actions": priority_actions,
                },
                error=None,
            )

        except Exception as exc:
            return AgentResult(
                status="FAILED",
                agent=self.name,
                task_id=task_id,
                data=None,
                error=str(exc),
            )

    @staticmethod
    def _build_prompt(input_data: dict[str, Any]) -> str:
        return f"""
You are the Recommendation Agent for a digital marketing platform.

Use ONLY the supplied outputs from previous marketing agents.

Do not invent statistics, market share, pricing, product features,
customer information, performance claims, or unsupported facts.

Do not perform new research.

Create:
1. Exactly 3 actionable recommendations.
2. Exactly 2 priority actions.

Return ONLY valid JSON in this format:

{{
  "recommendations": [
    "recommendation 1",
    "recommendation 2",
    "recommendation 3"
  ],
  "priority_actions": [
    "priority action 1",
    "priority action 2"
  ]
}}

Previous agent outputs:
{json.dumps(input_data, ensure_ascii=False, indent=2)}
""".strip()
