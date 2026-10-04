"""Image generation agent."""

from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent


IMAGE_PROMPT_TEMPLATE = """
You are a marketing image prompt specialist.

Create a detailed image-generation prompt for the user's marketing request.

Request:
{request}

Content context:
{content_context}

Brand profile:
{brand_profile}

Internal knowledge:
{knowledge}

Rules:
- image_prompt must be detailed and usable by an image-generation model.
- style should describe the visual style.
- aspect_ratio should be one of: "1:1", "4:5", "16:9".
- purpose should explain the marketing purpose.
- Respect the brand identity and tone when available.
- Use internal knowledge when available.
- Do not invent specific brand facts.
- Do not include markdown.
- Do not use code fences.

Return ONLY valid JSON with exactly these keys:

{{
  "image_prompt": "string",
  "style": "string",
  "aspect_ratio": "string",
  "purpose": "string"
}}
"""


class ImageAgent(BaseAgent):
    """Prepare marketing image requests and support future image providers."""

    name = "image"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:

        payload = dict(input_data or {})
        shared_context = dict(context or {})

        # ---------------------------------------------------------
        # 1. Resolve image request
        # ---------------------------------------------------------

        request = str(
            payload.get("prompt")
            or payload.get("image_prompt")
            or payload.get("request")
            or shared_context.get("user_request")
            or ""
        ).strip()

        if not request:
            return self._fail(
                task_id,
                "Missing image generation prompt.",
            )

        # ---------------------------------------------------------
        # 2. Resolve Content dependency
        # ---------------------------------------------------------

        content = payload.get("content")

        if not content:
            agent_outputs = shared_context.get(
                "agent_outputs"
            ) or {}

            content = agent_outputs.get("content")

        if isinstance(content, dict):
            content_context = _build_content_context(
                content
            )
        elif content:
            content_context = str(content)
        else:
            content_context = (
                "No content-generation context available."
            )

        # ---------------------------------------------------------
        # 3. Resolve Brand Profile
        # ---------------------------------------------------------

        brand_profile = shared_context.get(
            "brand_profile"
        ) or {}

        if not isinstance(brand_profile, dict):
            brand_profile = {}

        brand_profile_context = _build_brand_profile_context(
            brand_profile
        )

        # ---------------------------------------------------------
        # 4. Resolve RAG knowledge
        # ---------------------------------------------------------

        knowledge = shared_context.get(
            "knowledge"
        ) or []

        knowledge_context = _build_knowledge_context(
            knowledge
        )

        # ---------------------------------------------------------
        # 5. Build image-generation prompt
        # ---------------------------------------------------------

        prompt = IMAGE_PROMPT_TEMPLATE.format(
            request=request,
            content_context=content_context,
            brand_profile=brand_profile_context,
            knowledge=knowledge_context,
        )

        # ---------------------------------------------------------
        # 6. Generate structured image prompt
        # ---------------------------------------------------------

        try:
            raw = self.call_llm(prompt)
            parsed = self.parse_json(raw)

            image_prompt = _require_string(
                parsed,
                "image_prompt",
            )

            style = _require_string(
                parsed,
                "style",
            )

            aspect_ratio = _require_string(
                parsed,
                "aspect_ratio",
            )

            purpose = _require_string(
                parsed,
                "purpose",
            )

            if aspect_ratio not in {
                "1:1",
                "4:5",
                "16:9",
            }:
                raise ValueError(
                    "aspect_ratio must be one of: "
                    "1:1, 4:5, 16:9."
                )

        except Exception as exc:
            return self._fail(
                task_id,
                str(exc),
            )

        # ---------------------------------------------------------
        # 7. Provider-ready response
        # ---------------------------------------------------------
        #
        # We intentionally do NOT fabricate an image URL.
        # A real image provider can be connected later without
        # changing the planner/orchestrator contract.
        #

        return self._ok(
            task_id,
            summary="Marketing image generation request prepared.",
            data={
                "status": "IMAGE_PROVIDER_NOT_CONFIGURED",
                "image_prompt": image_prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "purpose": purpose,
                "image_url": None,
                "provider": None,
                "source_request": request,
                "content_used": bool(content),
                "brand_profile_used": bool(brand_profile),
                "knowledge_used": bool(knowledge),
            },
            confidence=1.0,
        )


def _build_content_context(
    content: dict[str, Any],
) -> str:
    """Convert Content Agent output into useful image context."""

    parts: list[str] = []

    title = content.get("title")

    if title:
        parts.append(
            f"Title: {title}"
        )

    campaign_hook = content.get("campaign_hook")

    if campaign_hook:
        parts.append(
            f"Campaign hook: {campaign_hook}"
        )

    caption = content.get("caption")

    if caption:
        parts.append(
            f"Caption: {caption}"
        )

    body = content.get("body")

    if body:
        parts.append(
            f"Body: {body}"
        )

    platform = content.get("platform")

    if platform:
        parts.append(
            f"Platform: {platform}"
        )

    hashtags = content.get("hashtags")

    if isinstance(hashtags, list) and hashtags:
        parts.append(
            "Hashtags: "
            + ", ".join(
                str(item)
                for item in hashtags
            )
        )

    strategy = content.get("strategy")

    if isinstance(strategy, list) and strategy:
        parts.append(
            "Strategy: "
            + "; ".join(
                str(item)
                for item in strategy
            )
        )

    if not parts:
        return (
            "Content context was provided "
            "but contained no usable fields."
        )

    return "\n".join(parts)


def _build_brand_profile_context(
    brand_profile: dict[str, Any],
) -> str:
    """Convert brand profile into compact image-generation context."""

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
    """Convert RAG knowledge into compact image context."""

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


def _require_string(
    parsed: dict[str, Any],
    key: str,
) -> str:
    """Validate a required non-empty string field."""

    value = parsed.get(key)

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"Field '{key}' must be a non-empty string."
        )

    return value.strip()