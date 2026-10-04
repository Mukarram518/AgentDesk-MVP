import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class APIEmbeddingProvider(EmbeddingProvider):
    """Remote HTTP embedding provider for sentence-transformers/all-MiniLM-L6-v2.
    
    Delegates embedding computation to a hosted inference API over HTTP (e.g. Hugging Face
    Inference API), completely eliminating in-memory PyTorch / SentenceTransformer footprint
    for memory-constrained production environments (512 MB RAM).
    """

    EXPECTED_DIMENSION: int = 384

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_url = (api_url or settings.EMBEDDING_API_URL).strip()
        self.api_key = (api_key or settings.EMBEDDING_API_KEY).strip()
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    @property
    def dimension(self) -> int:
        return self.EXPECTED_DIMENSION

    def _get_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "x-wait-for-model": "true",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def embed_text(self, text: str) -> List[float]:
        """Embed a single string via HTTP request and verify vector dimension."""
        if not text or not text.strip():
            return [0.0] * self.EXPECTED_DIMENSION

        payload = {"inputs": text}

        try:
            response = self._client.post(
                self.api_url,
                json=payload,
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.error(f"Embedding API connection error: {e}")
            raise RuntimeError(f"Embedding API connection failed: {e}") from e

        if response.status_code != 200:
            error_msg = (
                f"Embedding API returned status {response.status_code}: {response.text[:300]}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Embedding API returned non-JSON response: {e}") from e

        # Hugging Face feature-extraction returns either a 1D list of floats: [0.1, ...]
        # or a 2D list: [[0.1, ...]]
        vector: Optional[List[float]] = None
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list):
                vector = data[0]
            elif isinstance(data[0], (int, float)):
                vector = data

        if vector is None or not isinstance(vector, list):
            raise ValueError(
                f"Unexpected response structure from embedding API: {type(data)}"
            )

        if len(vector) != self.EXPECTED_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.EXPECTED_DIMENSION}, "
                f"but API returned {len(vector)} dimensions."
            )

        return [float(x) for x in vector]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings via HTTP request and verify all vector dimensions."""
        if not texts:
            return []

        clean_texts = [t if t and t.strip() else " " for t in texts]
        payload = {"inputs": clean_texts}

        try:
            response = self._client.post(
                self.api_url,
                json=payload,
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.error(f"Embedding API batch connection error: {e}")
            raise RuntimeError(f"Embedding API batch connection failed: {e}") from e

        if response.status_code != 200:
            error_msg = (
                f"Embedding API returned status {response.status_code}: {response.text[:300]}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Embedding API returned non-JSON response: {e}") from e

        if not isinstance(data, list):
            raise ValueError(
                f"Expected list response from embedding API batch, got {type(data)}"
            )

        vectors: List[List[float]] = []
        for idx, item in enumerate(data):
            vec: Optional[List[float]] = None
            if isinstance(item, list) and len(item) > 0:
                if isinstance(item[0], list):
                    vec = item[0]
                elif isinstance(item[0], (int, float)):
                    vec = item

            if vec is None or len(vec) != self.EXPECTED_DIMENSION:
                actual_dim = len(vec) if isinstance(vec, list) else type(item)
                raise ValueError(
                    f"Embedding dimension mismatch at batch index {idx}: "
                    f"expected {self.EXPECTED_DIMENSION}, but got {actual_dim}."
                )

            vectors.append([float(x) for x in vec])

        return vectors

    def close(self):
        """Close underlying HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()


# Singleton instance for API provider
_api_embedding_provider: Optional[APIEmbeddingProvider] = None


def get_api_embedding_provider() -> APIEmbeddingProvider:
    global _api_embedding_provider
    if _api_embedding_provider is None:
        _api_embedding_provider = APIEmbeddingProvider()
    return _api_embedding_provider
