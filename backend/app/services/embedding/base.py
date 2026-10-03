from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding providers.
    
    Ensures provider replaceability between local models and future embedding services.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Expected output vector dimension."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a single embedding vector for the provided text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate a list of embedding vectors for the provided texts."""
        pass
