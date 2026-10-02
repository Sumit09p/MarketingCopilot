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

Research context:
{research_context}

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

        # -----------------------------------------------------
        # 1. Resolve research dependency
        # -----------------------------------------------------

        research = payload.get("research")

        if isinstance(research, dict):
            research_data = research
        else:
            research_data = {}

        # -----------------------------------------------------
        # 2. Resolve product/topic
        # -----------------------------------------------------

        product = str(
            payload.get("product")
            or research_data.get("topic")
            or payload.get("topic")
            or ""
        ).strip()

        if not product:
            return self._fail(
                task_id,
                "Missing required input: product or research topic.",
            )

        # -----------------------------------------------------
        # 3. Resolve industry
        # -----------------------------------------------------

        industry = str(
            payload.get("industry")
            or research_data.get("industry")
            or "not specified"
        ).strip()

        # -----------------------------------------------------
        # 4. Resolve known competitors
        # -----------------------------------------------------

        competitors = payload.get("competitors")

        if isinstance(competitors, list):
            competitor_text = ", ".join(
                str(item)
                for item in competitors
                if str(item).strip()
            )
        else:
            competitor_text = str(
                competitors or "not specified"
            ).strip()

        # -----------------------------------------------------
        # 5. Build research context
        # -----------------------------------------------------

        research_context = _build_research_context(
            research_data
        )

        # -----------------------------------------------------
        # 6. Build LLM prompt
        # -----------------------------------------------------

        prompt = COMPETITOR_PROMPT.format(
            product=product,
            industry=industry,
            competitors=competitor_text or "not specified",
            research_context=research_context,
        )

        # -----------------------------------------------------
        # 7. Execute LLM
        # -----------------------------------------------------

        try:
            raw = self.call_llm(prompt)
            parsed = self.parse_json(raw)

            data = {
                "competitors": _min_string_list(
                    parsed,
                    "competitors",
                ),
                "strengths": _min_string_list(
                    parsed,
                    "strengths",
                ),
                "weaknesses": _min_string_list(
                    parsed,
                    "weaknesses",
                ),
                "content_opportunities": _min_string_list(
                    parsed,
                    "content_opportunities",
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
        # 8. Return structured result
        # -----------------------------------------------------

        return self._ok(
            task_id,
            summary=f"Competitor analysis for {product}",
            data={
                **data,
                "product": product,
                "industry": industry,
                "research_used": bool(research_data),
            },
        )


def _build_research_context(
    research: dict[str, Any],
) -> str:
    """
    Convert Research Agent output into a compact context
    for the Competitor Agent.
    """

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
            "Market opportunities: "
            + "; ".join(
                str(item)
                for item in opportunities
            )
        )

    return "\n".join(parts)


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