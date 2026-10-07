from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Base interface for all LLM providers.

    Higher-level application code should depend on this
    interface rather than a specific provider SDK.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a text response from the LLM.
        """
        raise NotImplementedError
