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

Campaign context:
{campaign_context}

Brand profile:
{brand_profile}

Internal knowledge:
{knowledge}

Write qualitative insights and recommendations only.

Rules:
1. Treat Python-calculated metrics as the only numeric source of truth.
2. Do not invent additional numbers or KPIs.
3. Use campaign context when available.
4. Use brand profile when available.
5. Use internal knowledge when available.
6. Clearly distinguish interpretation from verified facts.

Return ONLY JSON:
{{
  "insights": ["string", "string", "string"],
  "recommendations": ["string", "string", "string"]
}}

Each list must contain exactly 3 non-empty strings.
No markdown.
No code fences.
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
        shared_context = dict(context or {})

        # ---------------------------------------------------------
        # 1. Resolve numeric inputs
        # ---------------------------------------------------------

        try:
            impressions = _to_float(
                payload.get("impressions"),
                "impressions",
            )

            clicks = _to_float(
                payload.get("clicks"),
                "clicks",
            )

            conversions = _to_float(
                payload.get("conversions"),
                "conversions",
            )

            spend = _to_float(
                payload.get("spend"),
                "spend",
            )

            revenue = _to_float(
                payload.get("revenue"),
                "revenue",
            )

        except ValueError as exc:
            return self._fail(
                task_id,
                str(exc),
            )

        # ---------------------------------------------------------
        # 2. Calculate authoritative metrics in Python
        # ---------------------------------------------------------

        metrics = {
            "ctr": _ratio(
                clicks,
                impressions,
                as_percent=True,
            ),
            "conversion_rate": _ratio(
                conversions,
                clicks,
                as_percent=True,
            ),
            "cpc": _ratio(
                spend,
                clicks,
                as_percent=False,
            ),
            "cpa": _ratio(
                spend,
                conversions,
                as_percent=False,
            ),
            "roas": _ratio(
                revenue,
                spend,
                as_percent=False,
            ),
        }

        # ---------------------------------------------------------
        # 3. Resolve campaign context
        # ---------------------------------------------------------

        campaign_data = (
            payload.get("campaign_data")
            or shared_context.get("campaign_data")
            or {}
        )

        if not isinstance(campaign_data, dict):
            campaign_data = {}

        campaign_context = _build_campaign_context(
            campaign_data
        )

        # ---------------------------------------------------------
        # 4. Resolve Brand Profile
        # ---------------------------------------------------------

        brand_profile = (
            shared_context.get("brand_profile")
            or {}
        )

        if not isinstance(brand_profile, dict):
            brand_profile = {}

        brand_profile_context = _build_brand_profile_context(
            brand_profile
        )

        # ---------------------------------------------------------
        # 5. Resolve RAG knowledge
        # ---------------------------------------------------------

        knowledge = (
            shared_context.get("knowledge")
            or []
        )

        knowledge_context = _build_knowledge_context(
            knowledge
        )

        # ---------------------------------------------------------
        # 6. Safe fallback insights
        # ---------------------------------------------------------

        insights = [
            "Python-calculated metrics are shown; treat LLM comments as interpretation only."
        ]

        recommendations = [
            "Review campaigns with weak CTR or conversion rate before increasing spend."
        ]

        # ---------------------------------------------------------
        # 7. Generate qualitative interpretation
        # ---------------------------------------------------------

        try:
            raw = self.call_llm(
                INSIGHT_PROMPT.format(
                    metrics=json.dumps(metrics),
                    campaign_context=campaign_context,
                    brand_profile=brand_profile_context,
                    knowledge=knowledge_context,
                )
            )

            parsed = self.parse_json(raw)

            generated_insights = _string_list(
                parsed.get("insights")
            )

            generated_recommendations = _string_list(
                parsed.get("recommendations")
            )

            if len(generated_insights) >= 3:
                insights = generated_insights[:3]

            if len(generated_recommendations) >= 3:
                recommendations = generated_recommendations[:3]

        except Exception:
            # Calculations remain the source of truth
            # if interpretation fails.
            pass

        # ---------------------------------------------------------
        # 8. Return structured result
        # ---------------------------------------------------------

        data = {
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "campaign_context_used": bool(campaign_data),
            "brand_profile_used": bool(brand_profile),
            "knowledge_used": bool(knowledge),
        }

        return self._ok(
            task_id,
            summary="Marketing performance metrics calculated in Python.",
            data=data,
            confidence=0.9,
        )


def _to_float(
    value: Any,
    field: str,
) -> float:

    if value is None or value == "":
        raise ValueError(
            f"Missing required numeric input: {field}."
        )

    try:
        number = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Input '{field}' must be numeric."
        ) from exc

    if number < 0:
        raise ValueError(
            f"Input '{field}' cannot be negative."
        )

    return number


def _ratio(
    numerator: float,
    denominator: float,
    as_percent: bool,
) -> Optional[float]:

    if denominator == 0:
        return None

    result = numerator / denominator

    if as_percent:
        result *= 100

    return result


def _build_campaign_context(
    campaign_data: dict[str, Any],
) -> str:

    if not campaign_data:
        return "No campaign context available."

    parts: list[str] = []

    fields = [
        ("Campaign name", "name"),
        ("Campaign objective", "objective"),
        ("Platform", "platform"),
        ("Audience", "target_audience"),
        ("Description", "description"),
    ]

    for label, key in fields:
        value = campaign_data.get(key)

        if value:
            parts.append(
                f"{label}: {value}"
            )

    return (
        "\n".join(parts)
        or "Campaign context available but no descriptive fields were provided."
    )


def _build_brand_profile_context(
    brand_profile: dict[str, Any],
) -> str:

    if not brand_profile:
        return "No brand profile available."

    parts: list[str] = []

    fields = [
        ("Company", "company_name"),
        ("Industry", "industry"),
        ("Description", "description"),
        ("Target audience", "target_audience"),
        ("Products/services", "products_services"),
        ("Brand tone", "brand_tone"),
        ("Website", "website"),
        ("Location", "location"),
    ]

    for label, key in fields:
        value = brand_profile.get(key)

        if isinstance(value, list):
            value = ", ".join(
                str(item)
                for item in value
                if str(item).strip()
            )

        if value:
            parts.append(
                f"{label}: {value}"
            )

    return (
        "\n".join(parts)
        or "No brand profile available."
    )


def _build_knowledge_context(
    knowledge: Any,
) -> str:

    if not knowledge:
        return "No internal knowledge available."

    if isinstance(knowledge, str):
        return knowledge

    if isinstance(knowledge, list):
        parts: list[str] = []

        for item in knowledge:
            if isinstance(item, dict):
                text = (
                    item.get("text")
                    or item.get("content")
                    or item.get("chunk")
                )

                if text:
                    parts.append(
                        str(text)
                    )

            elif item:
                parts.append(
                    str(item)
                )

        return (
            "\n".join(parts)
            or "No internal knowledge available."
        )

    if isinstance(knowledge, dict):
        chunks = (
            knowledge.get("chunks")
            or knowledge.get("results")
            or knowledge.get("documents")
        )

        if isinstance(chunks, list):
            return _build_knowledge_context(
                chunks
            )

        text = (
            knowledge.get("text")
            or knowledge.get("content")
        )

        if text:
            return str(text)

    return str(knowledge)


def _string_list(
    value: Any,
) -> list[str]:

    if not isinstance(value, list):
        return []

    cleaned: list[str] = []

    for item in value:

        if (
            isinstance(item, str)
            and item.strip()
        ):
            cleaned.append(
                item.strip()
            )

    return cleaned