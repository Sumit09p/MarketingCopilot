from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.llm.provider import LLMService
from backend.services.llm.schemas import LLMRequest


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None


@router.post("/generate")
def generate_ai(request: GenerateRequest):
    try:
        service = LLMService()

        result = service.generate(
            LLMRequest(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
            )
        )

        return {
            "success": True,
            "data": {
                "content": result.content,
                "provider": result.provider,
            },
            "message": "AI response generated successfully.",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        )