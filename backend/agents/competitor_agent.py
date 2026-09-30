from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent

COMPETITOR_PROMPT = """
You are a competitor analysis assistant for marketing teams.

Analyze only at a qualitative level. Do not invent precise competitor
metrics, revenue, market share, rankings, follower counts, or statistics.

Product: {product}
Industry: {industry}
Known competitors: {competitors}

Return ONLY JSON with exactly these keys:
{{
  "competitors": ["string"],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "content_opportunities": ["string"],
  "recommendations": ["string"]
}}

Each list must contain at least 1 non-empty string.
No markdown. No code fences. No fabricated numbers.
"""


class CompetitorAgent(BaseAgent):
    name = "competitor"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        payload = dict(input_data or {})
        product = str(payload.get("product") or "").strip()
        if not product:
            return self._fail(task_id, "Missing required input: product.")

        competitors = payload.get("competitors")
        if isinstance(competitors, list):
            competitor_text = ", ".join(str(item) for item in competitors if str(item).strip())
        else:
            competitor_text = str(competitors or "not specified").strip()

        prompt = COMPETITOR_PROMPT.format(
            product=product,
            industry=str(payload.get("industry") or "not specified").strip(),
            competitors=competitor_text or "not specified",
        )

        try:
            raw = self.call_llm(prompt)
            parsed = self.parse_json(raw)
            data = {
                "competitors": _min_string_list(parsed, "competitors"),
                "strengths": _min_string_list(parsed, "strengths"),
                "weaknesses": _min_string_list(parsed, "weaknesses"),
                "content_opportunities": _min_string_list(parsed, "content_opportunities"),
                "recommendations": _min_string_list(parsed, "recommendations"),
            }
        except Exception as exc:
            return self._fail(task_id, str(exc))

        return self._ok(
            task_id,
            summary=f"Competitor analysis for {product}",
            data=data,
        )


def _min_string_list(parsed: dict[str, Any], key: str) -> list[str]:
    value = parsed.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Field '{key}' must be a non-empty list.")
    cleaned = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Each item in '{key}' must be a non-empty string.")
        cleaned.append(item.strip())
    return cleaned
