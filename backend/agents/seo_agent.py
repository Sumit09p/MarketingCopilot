from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent


SEO_PROMPT = """
You are an SEO recommendation assistant.

Give qualitative keyword and on-page suggestions only.
Do NOT invent search volume, keyword difficulty, Google rankings,
traffic numbers, positions, or CTR forecasts.

Topic: {topic}
Product: {product}
Target audience: {target_audience}

Research context:
{research_context}

Competitor context:
{competitor_context}

Return ONLY JSON with exactly these keys:
{{
  "primary_keywords": ["string"],
  "secondary_keywords": ["string"],
  "search_intent": "string",
  "meta_title": "string",
  "meta_description": "string",
  "content_gaps": ["string"],
  "recommendations": ["string"]
}}

Lists must contain at least 1 non-empty string each.
search_intent, meta_title, and meta_description must be non-empty strings.
No markdown. No code fences. No fabricated SEO metrics.
"""


class SEOAgent(BaseAgent):
    name = "seo"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:

        payload = dict(input_data or {})

        # -----------------------------------------------------
        # 1. Resolve Research dependency
        # -----------------------------------------------------

        research = payload.get("research")

        if isinstance(research, dict):
            research_data = research
        else:
            research_data = {}

        # -----------------------------------------------------
        # 2. Resolve Competitor dependency
        # -----------------------------------------------------

        competitor = payload.get("competitor")

        if isinstance(competitor, dict):
            competitor_data = competitor
        else:
            competitor_data = {}

        # -----------------------------------------------------
        # 3. Resolve topic
        # -----------------------------------------------------

        topic = str(
            payload.get("topic")
            or payload.get("product")
            or research_data.get("topic")
            or competitor_data.get("product")
            or ""
        ).strip()

        if not topic:
            return self._fail(
                task_id,
                "Provide at least a topic, product, or research context.",
            )

        # -----------------------------------------------------
        # 4. Resolve product
        # -----------------------------------------------------

        product = str(
            payload.get("product")
            or research_data.get("topic")
            or competitor_data.get("product")
            or topic
        ).strip()

        # -----------------------------------------------------
        # 5. Resolve target audience
        # -----------------------------------------------------

        target_audience = str(
            payload.get("target_audience")
            or _extract_research_audience(
                research_data
            )
            or "not specified"
        ).strip()

        # -----------------------------------------------------
        # 6. Build research context
        # -----------------------------------------------------

        research_context = _build_research_context(
            research_data
        )

        # -----------------------------------------------------
        # 7. Build competitor context
        # -----------------------------------------------------

        competitor_context = _build_competitor_context(
            competitor_data
        )

        # -----------------------------------------------------
        # 8. Build SEO prompt
        # -----------------------------------------------------

        prompt = SEO_PROMPT.format(
            topic=topic,
            product=product,
            target_audience=target_audience,
            research_context=research_context,
            competitor_context=competitor_context,
        )

        # -----------------------------------------------------
        # 9. Execute LLM
        # -----------------------------------------------------

        try:
            raw = self.call_llm(prompt)

            parsed = self.parse_json(raw)

            data = {
                "primary_keywords": _min_string_list(
                    parsed,
                    "primary_keywords",
                ),
                "secondary_keywords": _min_string_list(
                    parsed,
                    "secondary_keywords",
                ),
                "search_intent": _non_empty_string(
                    parsed,
                    "search_intent",
                ),
                "meta_title": _non_empty_string(
                    parsed,
                    "meta_title",
                ),
                "meta_description": _non_empty_string(
                    parsed,
                    "meta_description",
                ),
                "content_gaps": _min_string_list(
                    parsed,
                    "content_gaps",
                ),
                "recommendations": _min_string_list(
                    parsed,
                    "recommendations",
                ),
            }

        except Exception as exc:
            return self._fail(
                task_id,
                str(exc),
            )

        # -----------------------------------------------------
        # 10. Return structured result
        # -----------------------------------------------------

        return self._ok(
            task_id,
            summary=data["meta_title"],
            data={
                **data,
                "topic": topic,
                "product": product,
                "research_used": bool(research_data),
                "competitor_used": bool(competitor_data),
            },
        )


def _extract_research_audience(
    research: dict[str, Any],
) -> str:

    audience = research.get(
        "audience_insights",
        [],
    )

    if not isinstance(audience, list):
        return ""

    values = [
        str(item).strip()
        for item in audience
        if str(item).strip()
    ]

    if not values:
        return ""

    return "; ".join(values)


def _build_research_context(
    research: dict[str, Any],
) -> str:

    if not research:
        return "No research context available."

    parts: list[str] = []

    topic = research.get("topic")

    if topic:
        parts.append(
            f"Topic: {topic}"
        )

    summary = research.get("summary")

    if summary:
        parts.append(
            f"Summary: {summary}"
        )

    audience_insights = research.get(
        "audience_insights",
        [],
    )

    if audience_insights:
        parts.append(
            "Audience insights: "
            + "; ".join(
                str(item)
                for item in audience_insights
            )
        )

    market_trends = research.get(
        "market_trends",
        [],
    )

    if market_trends:
        parts.append(
            "Market trends: "
            + "; ".join(
                str(item)
                for item in market_trends
            )
        )

    opportunities = research.get(
        "opportunities",
        [],
    )

    if opportunities:
        parts.append(
            "Opportunities: "
            + "; ".join(
                str(item)
                for item in opportunities
            )
        )

    return "\n".join(parts)


def _build_competitor_context(
    competitor: dict[str, Any],
) -> str:

    if not competitor:
        return "No competitor context available."

    parts: list[str] = []

    competitors = competitor.get(
        "competitors",
        [],
    )

    if competitors:
        parts.append(
            "Competitors: "
            + "; ".join(
                str(item)
                for item in competitors
            )
        )

    strengths = competitor.get(
        "strengths",
        [],
    )

    if strengths:
        parts.append(
            "Competitor strengths: "
            + "; ".join(
                str(item)
                for item in strengths
            )
        )

    weaknesses = competitor.get(
        "weaknesses",
        [],
    )

    if weaknesses:
        parts.append(
            "Competitor weaknesses: "
            + "; ".join(
                str(item)
                for item in weaknesses
            )
        )

    content_opportunities = competitor.get(
        "content_opportunities",
        [],
    )

    if content_opportunities:
        parts.append(
            "Content opportunities: "
            + "; ".join(
                str(item)
                for item in content_opportunities
            )
        )

    recommendations = competitor.get(
        "recommendations",
        [],
    )

    if recommendations:
        parts.append(
            "Competitor recommendations: "
            + "; ".join(
                str(item)
                for item in recommendations
            )
        )

    return "\n".join(parts)


def _non_empty_string(
    parsed: dict[str, Any],
    key: str,
) -> str:

    value = parsed.get(key)

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"Field '{key}' must be a non-empty string."
        )

    return value.strip()


def _min_string_list(
    parsed: dict[str, Any],
    key: str,
) -> list[str]:

    value = parsed.get(key)

    if not isinstance(value, list) or not value:
        raise ValueError(
            f"Field '{key}' must be a non-empty list."
        )

    cleaned = []

    for item in value:

        if (
            not isinstance(item, str)
            or not item.strip()
        ):
            raise ValueError(
                f"Each item in '{key}' "
                "must be a non-empty string."
            )

        cleaned.append(
            item.strip()
        )

    return cleaned