from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId

from chat.models import (
    build_conversation_document,
    build_message_document,
    conversation_document_to_response,
    message_document_to_response,
)


def test_build_conversation_document():
    now = datetime.now(UTC)

    document = build_conversation_document(
        user_id="user-123",
        title="  Test Chat  ",
        now=now,
    )

    assert document["user_id"] == "user-123"
    assert document["title"] == "Test Chat"
    assert document["created_at"] == now
    assert document["updated_at"] == now


def test_build_message_document():
    now = datetime.now(UTC)

    document = build_message_document(
        conversation_id="conversation-123",
        user_id="user-123",
        role="user",
        content="  Hello world  ",
        now=now,
    )

    assert document["conversation_id"] == "conversation-123"
    assert document["user_id"] == "user-123"
    assert document["role"] == "user"
    assert document["content"] == "Hello world"
    assert document["created_at"] == now


def test_conversation_document_to_response():
    object_id = ObjectId()
    now = datetime.now(UTC)

    document = {
        "_id": object_id,
        "user_id": "user-123",
        "title": "Test Chat",
        "created_at": now,
        "updated_at": now,
    }

    response = conversation_document_to_response(document)

    assert response["id"] == str(object_id)
    assert response["title"] == "Test Chat"
    assert response["created_at"] == now
    assert response["updated_at"] == now


def test_message_document_to_response():
    object_id = ObjectId()
    now = datetime.now(UTC)

    document = {
        "_id": object_id,
        "conversation_id": "conversation-123",
        "user_id": "user-123",
        "role": "user",
        "content": "Hello",
        "created_at": now,
    }

    response = message_document_to_response(document)

    assert response["id"] == str(object_id)
    assert response["conversation_id"] == "conversation-123"
    assert response["role"] == "user"
    assert response["content"] == "Hello"
    assert response["created_at"] == now