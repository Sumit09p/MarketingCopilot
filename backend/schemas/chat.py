from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.guardrails.schemas import AgentType


class CreateConversationRequest(BaseModel):
    title: str = Field(
        default="New Chat",
        min_length=1,
        max_length=200,
    )


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    # ---------------------------------------------------------
    # Optional specialized-agent selection.
    #
    # None  -> General Mode
    # Value -> Explicit Agent Mode
    # ---------------------------------------------------------
    selected_agent: AgentType | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
