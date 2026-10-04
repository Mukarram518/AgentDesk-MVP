import logging
from typing import List, Optional
from app.core.config import settings
from app.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider utilizing Sentence Transformers (all-MiniLM-L6-v2).
    
    Generates 384-dimensional embeddings completely offline without hosted APIs.
    """

    EXPECTED_DIMENSION: int = 384

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None

    @property
    def dimension(self) -> int:
        return self.EXPECTED_DIMENSION

    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading local embedding model: {self.model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {e}")
                raise RuntimeError(
                    f"Could not load local embedding model '{self.model_name}'. "
                    f"Ensure sentence-transformers is installed. Details: {e}"
                ) from e
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Embed a single string and verify vector dimension."""
        if not text or not text.strip():
            # Return zero vector for empty content
            return [0.0] * self.EXPECTED_DIMENSION

        model = self._get_model()
        vector = model.encode(text, convert_to_numpy=True).tolist()
        
        if len(vector) != self.EXPECTED_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.EXPECTED_DIMENSION}, "
                f"but model produced {len(vector)} dimensions."
            )
        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings and verify all vector dimensions."""
        if not texts:
            return []

        # Replace empty strings with placeholder or empty vector
        clean_texts = [t if t and t.strip() else " " for t in texts]
        model = self._get_model()
        vectors = model.encode(clean_texts, convert_to_numpy=True).tolist()

        for idx, vector in enumerate(vectors):
            if len(vector) != self.EXPECTED_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch at index {idx}: expected {self.EXPECTED_DIMENSION}, "
                    f"but model produced {len(vector)} dimensions."
                )
        return vectors


# Singleton instance
_local_embedding_provider: Optional[LocalEmbeddingProvider] = None


def get_local_embedding_provider() -> LocalEmbeddingProvider:
    global _local_embedding_provider
    if _local_embedding_provider is None:
        _local_embedding_provider = LocalEmbeddingProvider()
    return _local_embedding_provider


def get_embedding_provider() -> EmbeddingProvider:
    """Unified embedding provider factory based on settings.EMBEDDING_PROVIDER."""
    if settings.EMBEDDING_PROVIDER.lower() in ("api", "huggingface", "remote"):
        from app.services.embedding.api import get_api_embedding_provider
        return get_api_embedding_provider()
    return get_local_embedding_provider()
