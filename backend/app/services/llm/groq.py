import logging
from typing import Optional
from app.core.config import settings
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq LLM Provider utilizing the configured Groq model (openai/gpt-oss-20b).
    
    Enforces server-side API key management and safe execution.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = api_key or settings.GROQ_API_KEY
        self._model_name = model_name or settings.GROQ_MODEL
        self._client = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self):
        if not self._api_key or self._api_key.strip() in ("", "your_groq_api_key_here"):
            raise ValueError(
                "Groq API key is not configured. Please set GROQ_API_KEY in your server-side environment (.env)."
            )
        if self._client is None:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize AsyncGroq client: {e}")
                raise RuntimeError(f"Could not initialize Groq client: {e}") from e
        return self._client

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Call Groq API with grounded prompt and return the assistant response."""
        client = self._get_client()

        # Build user content incorporating retrieved context with strict boundary markers
        if context and context.strip():
            user_content = (
                f"<retrieved_knowledge>\n{context.strip()}\n</retrieved_knowledge>\n\n"
                f"Customer Question: {user_message.strip()}"
            )
        else:
            user_content = (
                f"<retrieved_knowledge>\n[No relevant knowledge found for this query]\n</retrieved_knowledge>\n\n"
                f"Customer Question: {user_message.strip()}"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            logger.info(f"Calling Groq LLM model '{self._model_name}'...")
            chat_completion = await client.chat.completions.create(
                messages=messages,
                model=self._model_name,
                temperature=temperature,
                max_tokens=600,
            )
            response_content = chat_completion.choices[0].message.content
            return (response_content or "").strip()
        except Exception as e:
            logger.error(f"Groq API error during completion: {e}")
            raise RuntimeError(f"Groq generation failed: {str(e)}") from e
