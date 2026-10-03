from typing import Optional
from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.groq import GroqProvider
from app.services.llm.mock import MockLLMProvider

_llm_provider_instance: Optional[LLMProvider] = None


def get_llm_provider(force_mock: bool = False) -> LLMProvider:
    """Factory to get configured LLM provider.
    
    If force_mock is True, or if Groq is not configured, falls back to MockLLMProvider safely.
    """
    global _llm_provider_instance
    if force_mock:
        return MockLLMProvider()

    if _llm_provider_instance is None:
        # Check if Groq API key is configured with a valid key
        has_groq_key = bool(
            settings.GROQ_API_KEY
            and settings.GROQ_API_KEY.strip() not in ("", "your_groq_api_key_here")
        )
        if has_groq_key:
            _llm_provider_instance = GroqProvider()
        else:
            # Safe fallback for environments before key is supplied
            _llm_provider_instance = MockLLMProvider()

    return _llm_provider_instance


__all__ = [
    "LLMProvider",
    "GroqProvider",
    "MockLLMProvider",
    "get_llm_provider",
]
