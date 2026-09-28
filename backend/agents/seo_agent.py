from __future__ import annotations

from typing import Any, Optional

from agents.base import AgentResult, BaseAgent

SEO_PROMPT = """
You are an SEO recommendation assistant.

Give qualitative keyword and on-page suggestions only.
Do NOT invent search volume, keyword difficulty, Google rankings,
traffic numbers, positions, or CTR forecasts.

Topic: {topic}
Product: {product}
Target audience: {target_audience}
Existing content notes: {content}

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
        topic = str(payload.get("topic") or payload.get("product") or "").strip()
        if not topic:
            return self._fail(task_id, "Provide at least a topic or product.")

        prompt = SEO_PROMPT.format(
            topic=topic,
            product=str(payload.get("product") or topic).strip(),
            target_audience=str(payload.get("target_audience") or "not specified").strip(),
            content=str(payload.get("content") or "not specified").strip(),
        )

        try:
            raw = self.call_llm(prompt)
            parsed = self.parse_json(raw)
            data = {
                "primary_keywords": _min_string_list(parsed, "primary_keywords"),
                "secondary_keywords": _min_string_list(parsed, "secondary_keywords"),
                "search_intent": _non_empty_string(parsed, "search_intent"),
                "meta_title": _non_empty_string(parsed, "meta_title"),
                "meta_description": _non_empty_string(parsed, "meta_description"),
                "content_gaps": _min_string_list(parsed, "content_gaps"),
                "recommendations": _min_string_list(parsed, "recommendations"),
            }
        except Exception as exc:
            return self._fail(task_id, str(exc))

        return self._ok(task_id, summary=data["meta_title"], data=data)


def _non_empty_string(parsed: dict[str, Any], key: str) -> str:
    value = parsed.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field '{key}' must be a non-empty string.")
    return value.strip()


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
