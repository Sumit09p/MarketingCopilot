from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from backend.chat.models import (
    CONVERSATIONS_COLLECTION,
    MESSAGES_COLLECTION,
    build_conversation_document,
    build_message_document,
)
from backend.database import get_database


class ConversationNotFoundError(Exception):
    pass


class MessageNotFoundError(Exception):
    pass


class ChatService:
    def __init__(self) -> None:
        database = get_database()

        self.conversations = database[CONVERSATIONS_COLLECTION]
        self.messages = database[MESSAGES_COLLECTION]

    def create_conversation(
        self,
        user_id: str,
        title: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)

        conversation = build_conversation_document(
            user_id=user_id,
            title=title,
            now=now,
        )

        result = self.conversations.insert_one(conversation)

        conversation["_id"] = result.inserted_id

        return conversation

    def get_user_conversations(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        return list(
            self.conversations.find(
                {"user_id": user_id}
            ).sort("updated_at", -1)
        )

    def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        try:
            object_id = ObjectId(conversation_id)
        except (InvalidId, TypeError) as exc:
            raise ConversationNotFoundError(
                "Conversation not found."
            ) from exc

        conversation = self.conversations.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if conversation is None:
            raise ConversationNotFoundError(
                "Conversation not found."
            )

        return conversation

    def rename_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: str,
    ) -> dict[str, Any]:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        clean_title = title.strip()

        if not clean_title:
            raise ValueError("Conversation title cannot be empty.")

        now = datetime.now(UTC)

        self.conversations.update_one(
            {
                "_id": conversation["_id"],
                "user_id": user_id,
            },
            {
                "$set": {
                    "title": clean_title,
                    "updated_at": now,
                }
            },
        )

        conversation["title"] = clean_title
        conversation["updated_at"] = now

        return conversation

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> None:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        conversation_object_id = conversation["_id"]
        conversation_id_string = str(conversation_object_id)

        # Delete all messages belonging to this conversation.
        self.messages.delete_many(
            {
                "conversation_id": conversation_id_string,
                "user_id": user_id,
            }
        )

        # Delete the conversation itself.
        self.conversations.delete_one(
            {
                "_id": conversation_object_id,
                "user_id": user_id,
            }
        )

    def add_user_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
    ) -> dict[str, Any]:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        now = datetime.now(UTC)

        message = build_message_document(
            conversation_id=str(conversation["_id"]),
            user_id=user_id,
            role="user",
            content=content.strip(),
            now=now,
        )

        result = self.messages.insert_one(message)

        message["_id"] = result.inserted_id

        self.conversations.update_one(
            {"_id": conversation["_id"]},
            {
                "$set": {
                    "updated_at": now,
                }
            },
        )

        return message

    def add_assistant_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Persist an assistant message in a conversation."""

        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        now = datetime.now(UTC)

        message = build_message_document(
            conversation_id=str(conversation["_id"]),
            user_id=user_id,
            role="assistant",
            content=content.strip(),
            now=now,
        )

        result = self.messages.insert_one(message)

        message["_id"] = result.inserted_id

        self.conversations.update_one(
            {"_id": conversation["_id"]},
            {
                "$set": {
                    "updated_at": now,
                }
            },
        )

        return message

    def get_messages(
        self,
        conversation_id: str,
        user_id: str,
    ) -> list[dict[str, Any]]:
        conversation = self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return list(
            self.messages.find(
                {
                    "conversation_id": str(conversation["_id"]),
                    "user_id": user_id,
                }
            ).sort("created_at", 1)
        )

