"""Schemas for agent guardrail evaluation."""

from enum import Enum

from pydantic import BaseModel, Field

from backend.intent.schemas import IntentType


class GuardrailDecision(str, Enum):
    """Possible outcomes of an agent guardrail evaluation."""

    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class AgentType(str, Enum):
    """Specialized marketing agents supported by the system."""

    RESEARCH = "research"
    COMPETITOR = "competitor"
    SEO = "seo"
    CONTENT = "content"
    IMAGE = "image"
    ANALYTICS = "analytics"


class GuardrailResult(BaseModel):
    """Structured result returned by an agent guardrail."""

    decision: GuardrailDecision
    agent: AgentType
    detected_intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    missing_information: list[str] = Field(default_factory=list)
