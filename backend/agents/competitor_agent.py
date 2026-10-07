from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent


COMPETITOR_PROMPT = """
You are a competitor analysis assistant for marketing teams.

Analyze the product using the supplied research, brand profile,
and internal knowledge context.

IMPORTANT RULES:
1. Use qualitative reasoning only.
2. Do not invent revenue, market share, follower counts,
   rankings, percentages, or other precise statistics.
3. Clearly distinguish AI-generated analysis from verified facts.
4. Use the research context when it is available.
5. Use the brand profile when it is available.
6. Use internal knowledge when it is available.
7. Do not fabricate competitors as verified real-world companies
   unless they are explicitly provided in the input.

Product: {product}
Industry: {industry}

Known competitors:
{competitors}

Brand profile:
{brand_profile}

Internal knowledge:
{knowledge}

Research context:
{research_context}

Return ONLY valid JSON with exactly these keys:

{{
  "competitors": ["string"],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "content_opportunities": ["string"],
  "recommendations": ["string"]
}}

Each field must contain at least 1 non-empty string.

No markdown.
No code fences.
No fabricated numerical claims.
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
        context = context or {}

        # ============================================================
        # 1. Resolve research dependency
        # ============================================================

        research = payload.get("research")

        if isinstance(research, dict):
            research_data = research
        else:
            research_data = {}

        # ============================================================
        # 2. Resolve product/topic
        # ============================================================

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

        # ============================================================
        # 3. Resolve industry
        # ============================================================

        brand_profile = context.get("brand_profile") or {}

        industry = str(
            payload.get("industry")
            or research_data.get("industry")
            or brand_profile.get("industry")
            or "not specified"
        ).strip()

        # ============================================================
        # 4. Resolve known competitors
        # ============================================================

        competitors = (
            payload.get("competitors")
            or brand_profile.get("competitors")
        )

        if isinstance(competitors, list):

            competitor_names = [
                str(item).strip()
                for item in competitors
                if str(item).strip()
            ]

            competitor_text = ", ".join(competitor_names)

        elif competitors:

            competitor_text = str(competitors).strip()

        else:

            competitor_text = "not specified"

        if not competitor_text:
            competitor_text = "not specified"

        # ============================================================
        # 5. Build research context
        # ============================================================

        research_context = _build_research_context(
            research_data
        )

        # ============================================================
        # 6. Build brand profile context
        # ============================================================

        brand_profile_text = _build_brand_profile_context(
            brand_profile
        )

        # ============================================================
        # 7. Build internal knowledge context
        # ============================================================

        knowledge = context.get("knowledge") or {}

        knowledge_text = _build_knowledge_context(
            knowledge
        )

        # ============================================================
        # 8. Build LLM prompt
        # ============================================================

        prompt = COMPETITOR_PROMPT.format(
            product=product,
            industry=industry,
            competitors=competitor_text,
            brand_profile=brand_profile_text,
            knowledge=knowledge_text,
            research_context=research_context,
        )

        # ============================================================
        # 9. Execute LLM
        # ============================================================

        try:

            raw = self.call_llm(prompt)

            parsed = self.parse_json(raw)

            # --------------------------------------------------------
            # Validate every required output field
            # --------------------------------------------------------

            data = {
                "competitors": _require_string_list(
                    parsed,
                    "competitors",
                ),
                "strengths": _require_string_list(
                    parsed,
                    "strengths",
                ),
                "weaknesses": _require_string_list(
                    parsed,
                    "weaknesses",
                ),
                "content_opportunities": _require_string_list(
                    parsed,
                    "content_opportunities",
                ),
                "recommendations": _require_string_list(
                    parsed,
                    "recommendations",
                ),
            }

        except Exception as exc:

            return self._fail(
                task_id,
                str(exc),
            )

        # ============================================================
        # 10. Return structured result
        # ============================================================

        return self._ok(
            task_id,
            summary=f"Competitor analysis for {product}",
            data={
                **data,
                "product": product,
                "industry": industry,
                "research_used": bool(research_data),
                "brand_profile_used": bool(brand_profile),
                "knowledge_used": bool(knowledge),
            },
        )


# ====================================================================
# Research context helper
# ====================================================================

def _build_research_context(
    research: dict[str, Any],
) -> str:
    """
    Convert Research Agent output into compact context
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


# ====================================================================
# Brand profile helper
# ====================================================================

def _build_brand_profile_context(
    brand_profile: dict[str, Any],
) -> str:
    """
    Convert saved brand profile into compact context.
    """

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
        ("Competitors", "competitors"),
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


# ====================================================================
# RAG / knowledge helper
# ====================================================================

def _build_knowledge_context(
    knowledge: Any,
) -> str:
    """
    Convert retrieved RAG knowledge into compact context.
    """

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


# ====================================================================
# Strict JSON list validation
# ====================================================================

def _require_string_list(
    parsed: dict[str, Any],
    key: str,
) -> list[str]:

    value = parsed.get(key)

    if not isinstance(value, list) or not value:

        raise ValueError(
            f"Field '{key}' must be a non-empty list."
        )

    cleaned: list[str] = []

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
