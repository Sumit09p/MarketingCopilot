from __future__ import annotations

import json
from typing import Any, Optional

from .base import AgentResult, BaseAgent

INSIGHT_PROMPT = """
You are a marketing analytics interpreter.

The metrics below were calculated by Python and are AUTHORITATIVE.
Do not recalculate them. Do not invent additional numeric KPIs.

Metrics JSON:
{metrics}

Write qualitative insights and recommendations only.

Return ONLY JSON:
{{
  "insights": ["string", "string", "string"],
  "recommendations": ["string", "string", "string"]
}}

Each list must contain exactly 3 non-empty strings.
No markdown. No code fences.
"""


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        payload = dict(input_data or {})
        try:
            impressions = _to_float(payload.get("impressions"), "impressions")
            clicks = _to_float(payload.get("clicks"), "clicks")
            conversions = _to_float(payload.get("conversions"), "conversions")
            spend = _to_float(payload.get("spend"), "spend")
            revenue = _to_float(payload.get("revenue"), "revenue")
        except ValueError as exc:
            return self._fail(task_id, str(exc))

        metrics = {
            "ctr": _ratio(clicks, impressions, as_percent=True),
            "conversion_rate": _ratio(conversions, clicks, as_percent=True),
            "cpc": _ratio(spend, clicks, as_percent=False),
            "cpa": _ratio(spend, conversions, as_percent=False),
            "roas": _ratio(revenue, spend, as_percent=False),
        }

        insights = [
            "Python-calculated metrics are shown; treat LLM comments as interpretation only."
        ]
        recommendations = [
            "Review campaigns with weak CTR or conversion rate before increasing spend."
        ]

        try:
            raw = self.call_llm(INSIGHT_PROMPT.format(metrics=json.dumps(metrics)))
            parsed = self.parse_json(raw)
            insights = _string_list(parsed.get("insights")) or insights
            recommendations = _string_list(parsed.get("recommendations")) or recommendations
        except Exception:
            # Calculations remain the source of truth if interpretation fails.
            pass

        data = {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
        }
        return self._ok(
            task_id,
            summary="Marketing performance metrics calculated in Python.",
            data=data,
            confidence=0.9,
        )


def _to_float(value: Any, field: str) -> float:
    if value is None or value == "":
        raise ValueError(f"Missing required numeric input: {field}.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Input '{field}' must be numeric.") from exc
    if number < 0:
        raise ValueError(f"Input '{field}' cannot be negative.")
    return number


def _ratio(numerator: float, denominator: float, as_percent: bool) -> Optional[float]:
    if denominator == 0:
        return None
    result = numerator / denominator
    if as_percent:
        result *= 100
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned.append(item.strip())
    return cleaned
