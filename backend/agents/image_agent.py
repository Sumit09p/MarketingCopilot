"""Image generation agent."""

from __future__ import annotations

from typing import Any

from .base import BaseAgent


class ImageAgent(BaseAgent):
    """Generate marketing images or return a controlled unavailable response."""

    name = "image"

    def run(
        self,
        task_id: str,
        input_data: dict[str, Any],
        context: dict[str, Any],
    ):
        prompt = (
            input_data.get("prompt")
            or input_data.get("image_prompt")
            or context.get("user_request")
        )

        if not prompt:
            return self._fail(
                task_id,
                "Missing image generation prompt.",
            )

        # Image provider is intentionally handled separately.
        # Until a real provider is configured, do not fabricate an image URL.
        return self._ok(
            task_id,
            summary=(
                "Image generation request prepared, "
                "but no image provider is configured."
            ),
            data={
                "status": "IMAGE_PROVIDER_NOT_CONFIGURED",
                "prompt": prompt,
                "image_url": None,
                "provider": None,
            },
            confidence=1.0,
        )