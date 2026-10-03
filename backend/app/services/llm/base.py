from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Abstract interface for Large Language Model providers.
    
    Decouples application services from specific LLM vendors (e.g. Groq).
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active LLM model."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate a grounded assistant response based on the system prompt, context, and user message."""
        pass
