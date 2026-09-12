from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from app.config.settings import settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers (Ollama, OpenAI, Fake/Mock).
    Ensures vendor-agnostic generation and structured output parsing.
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates free-form natural language text from a prompt.
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        """
        Generates JSON output matching a Pydantic response schema.
        """
        pass


def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Factory function to instantiate configured LLM provider based on settings or override.
    """
    target = (provider_name or settings.LLM_PROVIDER).lower().strip()

    if target == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider()
    elif target in ["openai", "openai-compatible"]:
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif target == "fake" or target == "mock":
        from app.llm.fake_provider import FakeLLMProvider
        return FakeLLMProvider()
    else:
        # Fallback to FakeLLMProvider for unknown providers to prevent app crashing
        from app.llm.fake_provider import FakeLLMProvider
        return FakeLLMProvider()
