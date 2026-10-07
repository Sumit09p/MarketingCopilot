"""Adapter between the central LLM service and marketing agents."""

from backend.services.llm import LLMService
from backend.services.llm.schemas import LLMRequest


def build_agent_generator(
    llm_service: LLMService,
):
    """
    Create the generate(prompt) callable expected by BaseAgent.
    """

    def generate(prompt: str) -> str:
        response = llm_service.generate(
            LLMRequest(prompt=prompt)
        )
        return response.content

    return generate
