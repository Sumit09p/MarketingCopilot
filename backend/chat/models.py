from datetime import datetime
from typing import Any


CONVERSATIONS_COLLECTION = "conversations"
MESSAGES_COLLECTION = "messages"


def build_conversation_document(
    user_id: str,
    title: str,
    now: datetime,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "title": title.strip(),
        "created_at": now,
        "updated_at": now,
    }


def build_message_document(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    now: datetime,
) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": now,
    }


def conversation_document_to_response(
    conversation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(conversation["_id"]),
        "title": conversation["title"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
    }


def message_document_to_response(
    message: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(message["_id"]),
        "conversation_id": message["conversation_id"],
        "role": message["role"],
        "content": message["content"],
        "created_at": message["created_at"],
    }