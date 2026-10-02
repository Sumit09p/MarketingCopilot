from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent
from prompts.content_prompt import CONTENT_GENERATION_PROMPT


REQUIRED_INPUTS = (
    "product_name",
    "description",
    "target_audience",
    "platform",
    "tone",
)

REQUIRED_OUTPUT_KEYS = {
    "campaign_hook",
    "caption",
    "cta",
    "hashtags",
    "strategy",
}


class ContentAgent(BaseAgent):
    name = "content"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:

        payload = dict(input_data or {})
        shared_context = dict(context or {})

        # -----------------------------------------------------
        # 1. Fill missing values from shared context
        # -----------------------------------------------------

        for key in REQUIRED_INPUTS:
            if not payload.get(key):
                value = shared_context.get(key)

                if value:
                    payload[key] = value

        # -----------------------------------------------------
        # 2. Support natural-language requests
        # -----------------------------------------------------

        natural_prompt = (
            payload.get("user_request")
            or payload.get("query")
            or payload.get("prompt")
            or payload.get("input")
            or shared_context.get("user_request")
            or ""
        )

        if natural_prompt:
            payload = _enrich_from_natural_prompt(
                payload,
                str(natural_prompt),
            )

        # -----------------------------------------------------
        # 3. Validate required inputs
        # -----------------------------------------------------

        missing = [
            key
            for key in REQUIRED_INPUTS
            if not str(payload.get(key) or "").strip()
        ]

        if missing:
            return self._fail(
                task_id,
                "Missing required inputs: "
                + ", ".join(missing),
            )

        # -----------------------------------------------------
        # 4. Build generation prompt
        # -----------------------------------------------------

        prompt = CONTENT_GENERATION_PROMPT.format(
            product_name=payload["product_name"],
            description=payload["description"],
            target_audience=payload["target_audience"],
            platform=payload["platform"],
            tone=payload["tone"],
        )

        # -----------------------------------------------------
        # 5. Call LLM and validate output
        # -----------------------------------------------------

        try:
            raw = self.call_llm(prompt)

            content = self.parse_json(raw)

            validated = self._validate_output(content)

        except Exception as exc:
            return self._fail(
                task_id,
                str(exc),
            )

        # -----------------------------------------------------
        # 6. Return structured result
        # -----------------------------------------------------

        return self._ok(
            task_id,
            summary=validated["campaign_hook"],
            data=validated,
        )

    def _validate_output(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(content, dict):
            raise ValueError(
                "LLM output must be a JSON object."
            )

        missing_keys = (
            REQUIRED_OUTPUT_KEYS
            - set(content.keys())
        )

        if missing_keys:
            raise ValueError(
                "LLM output missing required keys: "
                + ", ".join(sorted(missing_keys))
            )

        campaign_hook = content.get(
            "campaign_hook"
        )

        caption = content.get(
            "caption"
        )

        cta = content.get(
            "cta"
        )

        hashtags = content.get(
            "hashtags"
        )

        strategy = content.get(
            "strategy"
        )

        if not isinstance(
            campaign_hook,
            str,
        ) or not campaign_hook.strip():
            raise ValueError(
                "campaign_hook must be a non-empty string."
            )

        if not isinstance(
            caption,
            str,
        ) or not caption.strip():
            raise ValueError(
                "caption must be a non-empty string."
            )

        if not isinstance(
            cta,
            str,
        ) or not cta.strip():
            raise ValueError(
                "cta must be a non-empty string."
            )

        if (
            not isinstance(hashtags, list)
            or not hashtags
        ):
            raise ValueError(
                "hashtags must be a non-empty list."
            )

        if (
            not isinstance(strategy, list)
            or not strategy
        ):
            raise ValueError(
                "strategy must be a non-empty list."
            )

        for item in hashtags:
            if (
                not isinstance(item, str)
                or not item.strip()
            ):
                raise ValueError(
                    "Each hashtag must be a non-empty string."
                )

        for item in strategy:
            if (
                not isinstance(item, str)
                or not item.strip()
            ):
                raise ValueError(
                    "Each strategy item must be a non-empty string."
                )

        return {
            "campaign_hook": campaign_hook.strip(),
            "caption": caption.strip(),
            "cta": cta.strip(),
            "hashtags": [
                item.strip()
                for item in hashtags
            ],
            "strategy": [
                item.strip()
                for item in strategy
            ],
        }


def _enrich_from_natural_prompt(
    payload: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:

    text = prompt.strip()

    # ---------------------------------------------------------
    # Platform
    # ---------------------------------------------------------

    if not payload.get("platform"):
        payload["platform"] = _detect_platform(
            text
        )

    # ---------------------------------------------------------
    # Product name
    # ---------------------------------------------------------

    if not payload.get("product_name"):
        payload["product_name"] = _extract_product_name(
            text
        )

    # ---------------------------------------------------------
    # Description
    # ---------------------------------------------------------

    if not payload.get("description"):
        payload["description"] = _build_description(
            text
        )

    # ---------------------------------------------------------
    # Target audience
    # ---------------------------------------------------------

    if not payload.get("target_audience"):
        payload["target_audience"] = _extract_target_audience(
            text
        )

    # ---------------------------------------------------------
    # Tone
    # ---------------------------------------------------------

    if not payload.get("tone"):
        payload["tone"] = _detect_tone(
            text
        )

    return payload


def _detect_platform(
    text: str,
) -> str:

    lowered = text.lower()

    if "instagram" in lowered:
        return "Instagram"

    if "linkedin" in lowered:
        return "LinkedIn"

    if "facebook" in lowered:
        return "Facebook"

    if (
        "twitter" in lowered
        or " x post" in lowered
        or lowered.startswith("x ")
    ):
        return "X"

    if "youtube" in lowered:
        return "YouTube"

    if "email" in lowered:
        return "Email"

    if "newsletter" in lowered:
        return "Email"

    if "blog" in lowered:
        return "Blog"

    return "Social Media"


def _extract_product_name(
    text: str,
) -> str:

    lowered = text.lower()

    markers = [
        "for a new ",
        "for the new ",
        "for my ",
        "for our ",
        "about ",
    ]

    for marker in markers:

        index = lowered.find(marker)

        if index != -1:

            candidate = text[
                index + len(marker):
            ].strip()

            if candidate:

                candidate = candidate.split(
                    " for "
                )[0]

                candidate = candidate.split(
                    " on "
                )[0]

                candidate = candidate.split(
                    " with "
                )[0]

                if candidate:
                    return candidate.strip()

    return "AI Product"


def _build_description(
    text: str,
) -> str:

    return (
        "Marketing content requested from the "
        f"following user brief: {text}"
    )


def _extract_target_audience(
    text: str,
) -> str:

    lowered = text.lower()

    if "developer" in lowered:
        return "Software developers and technology professionals"

    if "student" in lowered:
        return "Students and young professionals"

    if "business" in lowered:
        return "Business owners and professionals"

    if "startup" in lowered:
        return "Startup founders and technology professionals"

    return "Digital audiences interested in the product"


def _detect_tone(
    text: str,
) -> str:

    lowered = text.lower()

    if "professional" in lowered:
        return "Professional"

    if "formal" in lowered:
        return "Formal"

    if "funny" in lowered:
        return "Funny"

    if "casual" in lowered:
        return "Casual"

    if "friendly" in lowered:
        return "Friendly"

    return "Engaging"