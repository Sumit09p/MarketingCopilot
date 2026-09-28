from __future__ import annotations

from typing import Any, Optional

from .base import AgentResult, BaseAgent
from ..prompts.content_prompt import CONTENT_GENERATION_PROMPT

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
        if context:
            for key in REQUIRED_INPUTS:
                if not payload.get(key) and context.get(key):
                    payload[key] = context[key]

        missing = [key for key in REQUIRED_INPUTS if not str(payload.get(key) or "").strip()]
        if missing:
            return self._fail(
                task_id,
                f"Missing required inputs: {', '.join(missing)}.",
            )

        prompt = CONTENT_GENERATION_PROMPT.format(
            product_name=payload["product_name"],
            description=payload["description"],
            target_audience=payload["target_audience"],
            platform=payload["platform"],
            tone=payload["tone"],
        )

        try:
            raw = self.call_llm(prompt)
            content = self.parse_json(raw)
            validated = self._validate_output(content)
        except Exception as exc:
            return self._fail(task_id, str(exc))

        return self._ok(
            task_id,
            summary=validated["campaign_hook"],
            data=validated,
        )

    def _validate_output(self, content: dict[str, Any]) -> dict[str, Any]:
        if not REQUIRED_OUTPUT_KEYS.issubset(content.keys()):
            raise ValueError("Missing required fields in content output.")

        for key in ("campaign_hook", "caption", "cta"):
            value = content.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Field '{key}' must be a non-empty string.")

        hashtags = content.get("hashtags")
        if not isinstance(hashtags, list) or len(hashtags) != 5:
            raise ValueError("Expected exactly 5 hashtags.")
        if any(not isinstance(item, str) or not item.strip() for item in hashtags):
            raise ValueError("Each hashtag must be a non-empty string.")

        strategy = content.get("strategy")
        if not isinstance(strategy, list) or len(strategy) != 3:
            raise ValueError("Expected exactly 3 strategy suggestions.")
        if any(not isinstance(item, str) or not item.strip() for item in strategy):
            raise ValueError("Each strategy suggestion must be a non-empty string.")

        return {
            "campaign_hook": content["campaign_hook"].strip(),
            "caption": content["caption"].strip(),
            "cta": content["cta"].strip(),
            "hashtags": [item.strip() for item in hashtags],
            "strategy": [item.strip() for item in strategy],
        }
