from fastapi import APIRouter, Depends, HTTPException

from chat.models import (
    conversation_document_to_response,
    message_document_to_response,
)
from chat.service import (
    ChatService,
    ConversationNotFoundError,
)
from schemas.chat import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
)
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


def get_chat_service() -> ChatService:
    return ChatService()


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201,
)
def create_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    conversation = chat_service.create_conversation(
        user_id=str(current_user["_id"]),
        title=request.title,
    )

    return ConversationResponse(
        **conversation_document_to_response(conversation)
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def get_conversations(
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    conversations = chat_service.get_user_conversations(
        user_id=str(current_user["_id"])
    )

    return [
        ConversationResponse(
            **conversation_document_to_response(conversation)
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        messages = chat_service.get_messages(
            conversation_id=conversation_id,
            user_id=str(current_user["_id"]),
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    return [
        MessageResponse(
            **message_document_to_response(message)
        )
        for message in messages
    ]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        message = chat_service.add_user_message(
            conversation_id=conversation_id,
            user_id=str(current_user["_id"]),
            content=request.content,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    return MessageResponse(
        **message_document_to_response(message)
    )