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

from services.marketing_pipeline_service import MarketingPipelineService
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


def get_chat_service() -> ChatService:
    return ChatService()


def get_marketing_pipeline_service() -> MarketingPipelineService:
    return MarketingPipelineService()


# ---------------------------------------------------------
# Create conversation
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Get user's conversations
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Rename conversation
# ---------------------------------------------------------

@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def rename_conversation(
    conversation_id: str,
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        conversation = chat_service.rename_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user["_id"]),
            title=request.title,
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

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        ) from exc

    return ConversationResponse(
        **conversation_document_to_response(conversation)
    )


# ---------------------------------------------------------
# Delete conversation
# ---------------------------------------------------------

@router.delete(
    "/conversations/{conversation_id}",
)
def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        chat_service.delete_conversation(
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

    return {
        "success": True,
        "data": None,
        "message": "Conversation deleted successfully.",
    }


# ---------------------------------------------------------
# Get conversation messages
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Send message
# ---------------------------------------------------------

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
    pipeline_service: MarketingPipelineService = Depends(
        get_marketing_pipeline_service
    ),
):
    user_id = str(current_user["_id"])

    # -----------------------------------------------------
    # 1. Save user message
    # -----------------------------------------------------

    try:
        user_message = chat_service.add_user_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=request.content,
        )

        # Get complete conversation history AFTER saving
        # the current user message.
        conversation_messages = chat_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        conversation_history = []

        for message in conversation_messages:
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")
            else:
                role = getattr(message, "role", None)
                content = getattr(message, "content", None)

            if role and content:
                conversation_history.append(
                    {
                        "role": str(role),
                        "content": str(content),
                    }
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

    # -----------------------------------------------------
    # 2. Process request through MarketingOS pipeline
    # -----------------------------------------------------

    try:
        pipeline_result = pipeline_service.process_request(
            user_id=user_id,
            conversation_id=conversation_id,
            user_request=request.content,
            selected_agent=request.selected_agent,
            conversation_history=conversation_history,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "data": None,
                "message": "Failed to process marketing request.",
                "error": str(exc),
            },
        ) from exc

    # -----------------------------------------------------
    # 3. Build assistant response
    # -----------------------------------------------------

    clarification = pipeline_result.get("clarification")
    assistant_content = None

    # Gemini-generated clarification
    if clarification:
        questions = clarification.get("questions") or []

        if questions:
            formatted_questions = "\n".join(
                f"{index}. {question}"
                for index, question in enumerate(
                    questions,
                    start=1,
                )
            )

            assistant_content = (
                "Before I proceed, I need a little more "
                "information:\n\n"
                f"{formatted_questions}"
            )

        else:
            question = clarification.get("question")

            if question:
                assistant_content = (
                    "Before I proceed, I need a little more "
                    "information:\n\n"
                    f"{question}"
                )

    # Normal pipeline response
    if assistant_content is None:
        assistant_content = _build_assistant_response(
            pipeline_result
        )

    # -----------------------------------------------------
    # 4. Save assistant response
    # -----------------------------------------------------

    try:
        assistant_message = chat_service.add_assistant_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=assistant_content,
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

    # -----------------------------------------------------
    # 5. Return assistant message
    # -----------------------------------------------------

    return MessageResponse(
        **message_document_to_response(assistant_message)
    )


# ---------------------------------------------------------
# Assistant response formatting
# ---------------------------------------------------------

def _build_assistant_response(
    pipeline_result: dict,
) -> str:
    """
    Convert pipeline output into a chat-friendly response.

    Handles:
    - guardrail INVALID
    - guardrail NEEDS_CLARIFICATION
    - normal agent execution
    - image provider unavailable
    - structured Content Agent response
    - failed workflows
    """

    # -----------------------------------------------------
    # Guardrail response
    # -----------------------------------------------------

    guardrail = pipeline_result.get("guardrail")

    if guardrail:
        decision = guardrail.get("decision")

        agent = guardrail.get(
            "agent",
            guardrail.get("selected"),
        )

        reason = guardrail.get(
            "reason",
            "",
        )

        missing_information = guardrail.get(
            "missing_information",
            [],
        )

        if decision == "INVALID":
            return (
                f"The {agent} agent cannot handle this request.\n\n"
                f"{reason}"
            )

        if decision == "NEEDS_CLARIFICATION":
            if missing_information:
                missing = "\n".join(
                    f"- {item}"
                    for item in missing_information
                )

                return (
                    "I need a little more information before "
                    f"I can use the {agent} agent.\n\n"
                    f"Please provide:\n{missing}"
                )

            return (
                "I need a little more information before "
                f"I can use the {agent} agent."
            )

    # -----------------------------------------------------
    # Normal orchestration response
    # -----------------------------------------------------

    intent = pipeline_result.get(
        "intent",
        {},
    )

    orchestration = pipeline_result.get(
        "orchestration",
        {},
    )

    final_result = (
        orchestration.get(
            "final_result"
        )
        or {}
    )

    intent_type = intent.get(
        "type",
        "GENERAL",
    )

    status = final_result.get(
        "status",
        "FAILED",
    )

    summary = final_result.get(
        "summary"
    )

    data = final_result.get(
        "data"
    ) or {}

    error = final_result.get(
        "error"
    )

    # -----------------------------------------------------
    # Successful execution
    # -----------------------------------------------------

    if status == "COMPLETED":

        # -------------------------------------------------
        # Image provider unavailable
        # -------------------------------------------------

        if (
            data.get("status")
            == "IMAGE_PROVIDER_NOT_CONFIGURED"
        ):
            prompt = data.get(
                "image_prompt",
                data.get(
                    "prompt",
                    "",
                ),
            )

            return (
                "I understood this as an image-generation "
                "request.\n\n"
                "The Image Agent prepared the creative request, "
                "but no image-generation provider is currently "
                "configured.\n\n"
                f"Prompt: {prompt}"
            )

        # -------------------------------------------------
        # Content Agent structured response
        # -------------------------------------------------

        if (
            intent_type == "CONTENT_GENERATION"
            or "caption" in data
            or "campaign_hook" in data
        ):
            return _format_content_response(
                data=data,
                summary=summary,
            )

        # -------------------------------------------------
        # Generic successful response
        # -------------------------------------------------

        if summary:
            return summary

        return (
            "Request processed successfully using "
            f"the {intent_type} workflow."
        )

    # -----------------------------------------------------
    # Failed execution
    # -----------------------------------------------------

    if status == "FAILED":
        return (
            "I could not complete the requested workflow.\n\n"
            f"Reason: {error or 'Unknown agent error.'}"
        )

    # -----------------------------------------------------
    # Other state
    # -----------------------------------------------------

    return (
        "The marketing workflow could not be completed."
    )


# ---------------------------------------------------------
# Content response formatter
# ---------------------------------------------------------

def _format_content_response(
    data: dict,
    summary: str | None = None,
) -> str:
    """
    Format the structured Content Agent result into a
    human-readable chat response.
    """

    campaign_hook = data.get(
        "campaign_hook"
    )

    caption = data.get(
        "caption"
    )

    cta = data.get(
        "cta"
    )

    hashtags = data.get(
        "hashtags",
        [],
    )

    strategy = data.get(
        "strategy",
        [],
    )

    sections = []

    # -----------------------------------------------------
    # Campaign Hook
    # -----------------------------------------------------

    if campaign_hook:
        sections.append(
            f"### Campaign Hook\n{campaign_hook}"
        )

    # -----------------------------------------------------
    # Caption
    # -----------------------------------------------------

    if caption:
        sections.append(
            f"### Caption\n{caption}"
        )

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

    if cta:
        sections.append(
            f"### Call to Action\n{cta}"
        )

    # -----------------------------------------------------
    # Hashtags
    # -----------------------------------------------------

    if hashtags:
        formatted_hashtags = " ".join(
            str(tag)
            for tag in hashtags
        )

        sections.append(
            f"### Hashtags\n{formatted_hashtags}"
        )

    # -----------------------------------------------------
    # Strategy
    # -----------------------------------------------------

    if strategy:
        formatted_strategy = "\n".join(
            f"- {item}"
            for item in strategy
        )

        sections.append(
            f"### Strategy\n{formatted_strategy}"
        )

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    if sections:
        return "\n\n".join(sections)

    if summary:
        return summary

    return (
        "The Content Agent completed the request, "
        "but did not return formatted content."
    )