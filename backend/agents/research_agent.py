from __future__ import annotations

import json
from typing import Any, Optional

from .base import AgentResult, BaseAgent
from services.research.search_provider import SearchProvider


RESEARCH_PROMPT = """
You are a research agent.

Perform marketing research for the user's request.

Use the following context when available:
- User request
- Brand profile
- Internal RAG knowledge
- External research sources

Do not invent statistics, percentages, rankings, market sizes, or citations.
Clearly distinguish verified/external information from qualitative AI analysis.

USER REQUEST:
{user_request}

TOPIC:
{topic}

PRODUCT / SERVICE:
{product}

TARGET AUDIENCE:
{target_audience}

INDUSTRY:
{industry}

BRAND PROFILE:
{brand_profile}

INTERNAL KNOWLEDGE:
{knowledge}

EXTERNAL RESEARCH:
{external_research}

Return ONLY JSON with exactly these keys:

{{
  "topic": "string",
  "summary": "string",
  "audience_insights": [
    "string",
    "string",
    "string"
  ],
  "market_trends": [
    "string",
    "string",
    "string"
  ],
  "opportunities": [
    "string",
    "string",
    "string"
  ]
}}

Each list must contain exactly 3 non-empty strings.

No markdown.
No code fences.
"""


class ResearchAgent(BaseAgent):
    name = "research"

    def __init__(
        self,
        generate,
        search_provider: SearchProvider | None = None,
    ) -> None:
        super().__init__(generate)
        self.search_provider = search_provider or SearchProvider()

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:

        payload = dict(input_data or {})
        context = dict(context or {})

        # ---------------------------------------------------------
        # 1. Resolve user request
        # ---------------------------------------------------------

        user_request = str(
            context.get("user_request")
            or payload.get("user_request")
            or payload.get("topic")
            or payload.get("product")
            or ""
        ).strip()

        # ---------------------------------------------------------
        # 2. Resolve topic
        # ---------------------------------------------------------

        topic = str(
            payload.get("topic")
            or payload.get("product")
            or user_request
            or ""
        ).strip()

        if not topic:
            return self._fail(
                task_id,
                "Provide at least a topic or product.",
            )

        # ---------------------------------------------------------
        # 3. Resolve brand profile
        # ---------------------------------------------------------

        brand_profile = context.get("brand_profile") or {}

        if not isinstance(brand_profile, dict):
            brand_profile = {}

        product = str(
            payload.get("product")
            or _first_non_empty(
                brand_profile.get("products_services")
            )
            or topic
        ).strip()

        target_audience = str(
            payload.get("target_audience")
            or brand_profile.get("target_audience")
            or "not specified"
        ).strip()

        industry = str(
            payload.get("industry")
            or brand_profile.get("industry")
            or "not specified"
        ).strip()

        # ---------------------------------------------------------
        # 4. Resolve RAG knowledge
        # ---------------------------------------------------------

        knowledge = context.get("knowledge") or []

        if not isinstance(knowledge, list):
            knowledge = []

        knowledge_text = _format_knowledge(knowledge)

        # ---------------------------------------------------------
        # 5. Format brand profile
        # ---------------------------------------------------------

        brand_profile_text = _format_brand_profile(
            brand_profile
        )

        # ---------------------------------------------------------
        # 6. External research
        # ---------------------------------------------------------

        external_research = self._collect_external_research(
            topic=topic,
            product=product,
            target_audience=target_audience,
            industry=industry,
        )

        # ---------------------------------------------------------
        # 7. Build context-aware LLM prompt
        # ---------------------------------------------------------

        prompt = RESEARCH_PROMPT.format(
            user_request=user_request,
            topic=topic,
            product=product,
            target_audience=target_audience,
            industry=industry,
            brand_profile=brand_profile_text,
            knowledge=knowledge_text,
            external_research=external_research,
        )

        # ---------------------------------------------------------
        # 8. Call LLM
        # ---------------------------------------------------------

        try:
            raw = self.call_llm(prompt)

            parsed = self.parse_json(raw)

            data = self._validate(
                parsed,
                fallback_topic=topic,
            )

        except Exception as exc:
            return self._fail(
                task_id,
                str(exc),
            )

        # ---------------------------------------------------------
        # 9. Research mode
        # ---------------------------------------------------------

        if self.search_provider.available:
            data["research_mode"] = "external_search_augmented"
        else:
            data["research_mode"] = "qualitative_fallback"

        # ---------------------------------------------------------
        # 10. Context metadata
        # ---------------------------------------------------------

        data["context_used"] = {
            "brand_profile": bool(brand_profile),
            "brand_company": brand_profile.get("company_name"),
            "internal_knowledge": bool(knowledge),
            "knowledge_sources": _knowledge_sources(knowledge),
            "external_research": self.search_provider.available,
        }

        return self._ok(
            task_id,
            summary=data["summary"],
            data=data,
        )

    def _collect_external_research(
        self,
        *,
        topic: str,
        product: str,
        target_audience: str,
        industry: str,
    ) -> str:

        queries = [
            f"{topic} market trends",
            f"{product} target audience trends {industry}",
            f"{topic} competitors marketing trends",
        ]

        collected: list[str] = []

        for query in queries:

            result = self.search_provider.search(
                query,
                max_results=3,
            )

            if not result.get("available"):
                continue

            for item in result.get("results", []):

                title = str(
                    item.get("title") or ""
                ).strip()

                content = str(
                    item.get("content") or ""
                ).strip()

                url = str(
                    item.get("url") or ""
                ).strip()

                if not title and not content:
                    continue

                source_text = (
                    f"Title: {title}\n"
                    f"Content: {content}\n"
                    f"Source: {url}"
                )

                collected.append(source_text)

        if not collected:
            return (
                "No external research is currently available. "
                "Use qualitative AI reasoning only and clearly label it "
                "as qualitative research."
            )

        return "\n\n--- SOURCE ---\n\n".join(
            collected
        )

    def _validate(
        self,
        parsed: dict[str, Any],
        fallback_topic: str,
    ) -> dict[str, Any]:

        topic = parsed.get("topic") or fallback_topic
        summary = parsed.get("summary")

        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(
                "Field 'topic' must be a non-empty string."
            )

        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(
                "Field 'summary' must be a non-empty string."
            )

        return {
            "topic": topic.strip(),
            "summary": summary.strip(),
            "audience_insights": _require_string_list(
                parsed,
                "audience_insights",
                3,
            ),
            "market_trends": _require_string_list(
                parsed,
                "market_trends",
                3,
            ),
            "opportunities": _require_string_list(
                parsed,
                "opportunities",
                3,
            ),
        }


def _first_non_empty(
    value: Any,
) -> str | None:

    if not isinstance(value, list):
        return None

    for item in value:

        if isinstance(item, str) and item.strip():
            return item.strip()

    return None


def _format_brand_profile(
    brand_profile: dict[str, Any],
) -> str:

    if not brand_profile:
        return "No brand profile is available."

    relevant_fields = {
        "company_name": brand_profile.get("company_name"),
        "industry": brand_profile.get("industry"),
        "description": brand_profile.get("description"),
        "target_audience": brand_profile.get("target_audience"),
        "products_services": brand_profile.get("products_services"),
        "brand_tone": brand_profile.get("brand_tone"),
        "website": brand_profile.get("website"),
        "location": brand_profile.get("location"),
        "competitors": brand_profile.get("competitors"),
    }

    return json.dumps(
        relevant_fields,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def _format_knowledge(
    knowledge: list[dict[str, Any]],
) -> str:

    if not knowledge:
        return "No internal knowledge was retrieved."

    formatted: list[str] = []

    for index, item in enumerate(
        knowledge,
        start=1,
    ):

        if not isinstance(item, dict):
            continue

        source = str(
            item.get("source") or "unknown"
        ).strip()

        text = str(
            item.get("text") or ""
        ).strip()

        score = item.get("score")

        if not text:
            continue

        formatted.append(
            f"[Knowledge {index}]\n"
            f"Source: {source}\n"
            f"Score: {score}\n"
            f"Content: {text}"
        )

    if not formatted:
        return "No usable internal knowledge was retrieved."

    return "\n\n".join(formatted)


def _knowledge_sources(
    knowledge: list[dict[str, Any]],
) -> list[str]:

    sources: list[str] = []

    for item in knowledge:

        if not isinstance(item, dict):
            continue

        source = str(
            item.get("source") or ""
        ).strip()

        if source and source not in sources:
            sources.append(source)

    return sources


def _require_string_list(
    parsed: dict[str, Any],
    key: str,
    count: int,
) -> list[str]:

    value = parsed.get(key)

    if not isinstance(value, list) or len(value) != count:
        raise ValueError(
            f"Field '{key}' must contain exactly {count} items."
        )

    cleaned = []

    for item in value:

        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"Each item in '{key}' must be a non-empty string."
            )

        cleaned.append(item.strip())

    return cleaned