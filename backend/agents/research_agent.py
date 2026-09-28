from __future__ import annotations

from typing import Any, Optional

from agents.base import AgentResult, BaseAgent

RESEARCH_PROMPT = """
You are a marketing research assistant.

Produce qualitative, AI-generated research insights based ONLY on the
information below. Do not pretend this is verified external research.
Do not invent numerical market statistics, market size, growth rates,
percentages, rankings, or citations to studies that were not provided.

Topic: {topic}
Product: {product}
Target audience: {target_audience}
Industry: {industry}

Return ONLY JSON with exactly these keys:
{{
  "topic": "string",
  "summary": "string",
  "audience_insights": ["string", "string", "string"],
  "market_trends": ["string", "string", "string"],
  "opportunities": ["string", "string", "string"]
}}

Each list must contain exactly 3 non-empty strings.
Label insights as qualitative AI-generated research, not as proven facts.
No markdown. No code fences.
"""


class ResearchAgent(BaseAgent):
    name = "research"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        payload = dict(input_data or {})
        topic = str(payload.get("topic") or payload.get("product") or "").strip()
        if not topic:
            return self._fail(task_id, "Provide at least a topic or product.")

        prompt = RESEARCH_PROMPT.format(
            topic=topic,
            product=str(payload.get("product") or topic).strip(),
            target_audience=str(payload.get("target_audience") or "not specified").strip(),
            industry=str(payload.get("industry") or "not specified").strip(),
        )

        try:
            raw = self.call_llm(prompt)
            parsed = self.parse_json(raw)
            data = self._validate(parsed, fallback_topic=topic)
        except Exception as exc:
            return self._fail(task_id, str(exc))

        return self._ok(task_id, summary=data["summary"], data=data)

    def _validate(self, parsed: dict[str, Any], fallback_topic: str) -> dict[str, Any]:
        topic = parsed.get("topic") or fallback_topic
        summary = parsed.get("summary")
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("Field 'topic' must be a non-empty string.")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Field 'summary' must be a non-empty string.")

        return {
            "topic": topic.strip(),
            "summary": summary.strip(),
            "audience_insights": _require_string_list(parsed, "audience_insights", 3),
            "market_trends": _require_string_list(parsed, "market_trends", 3),
            "opportunities": _require_string_list(parsed, "opportunities", 3),
        }


def _require_string_list(parsed: dict[str, Any], key: str, count: int) -> list[str]:
    value = parsed.get(key)
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f"Field '{key}' must contain exactly {count} items.")
    cleaned = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Each item in '{key}' must be a non-empty string.")
        cleaned.append(item.strip())
    return cleaned
