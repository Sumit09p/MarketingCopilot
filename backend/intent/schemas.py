"""Schemas for user intent detection."""

from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported high-level user intents."""

    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    SEO_ANALYSIS = "SEO_ANALYSIS"
    CONTENT_GENERATION = "CONTENT_GENERATION"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    ANALYTICS = "ANALYTICS"


class IntentResult(BaseModel):
    """Structured result produced by the intent detection service."""

    intent: IntentType
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    reasoning: str | None = None