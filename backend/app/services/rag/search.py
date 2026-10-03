import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.local import get_embedding_provider

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    business_id: uuid.UUID
    content: str
    chunk_index: int
    score: float  # Cosine similarity (0 to 1, higher is more similar)
    distance: float  # Cosine distance (0 to 2, lower is more similar)
    document_title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SemanticSearchService:
    """Service performing pgvector similarity search scoped strictly to a single business."""

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def search(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        query: str,
        top_k: int = 4,
        min_similarity: float = 0.0,
    ) -> List[SearchResult]:
        """Perform semantic search against business knowledge base.
        
        CRITICAL ARCHITECTURAL RULE:
        Always filters by `business_id` to strictly preserve tenant isolation.
        """
        if not query or not query.strip():
            return []

        # 1. Embed query
        query_vector = self.embedding_provider.embed_text(query)

        # 2. Query pgvector with cosine distance, strictly scoped to business_id
        # In pgvector: cosine_distance = 1 - cosine_similarity
        distance_col = KnowledgeChunk.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(KnowledgeChunk, distance_col)
            .options(selectinload(KnowledgeChunk.document))
            .where(KnowledgeChunk.business_id == business_id)
            .order_by(distance_col.asc())
            .limit(top_k)
        )

        result = await db.execute(stmt)
        rows = result.all()

        search_results: List[SearchResult] = []
        for chunk, distance_val in rows:
            # Cosine similarity = 1 - distance
            similarity = max(0.0, 1.0 - float(distance_val))
            if similarity < min_similarity:
                continue

            doc_title = chunk.document.title if chunk.document else None
            search_results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    business_id=chunk.business_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    score=round(similarity, 4),
                    distance=round(float(distance_val), 4),
                    document_title=doc_title,
                    metadata=chunk.chunk_metadata,
                )
            )

        logger.debug(
            f"Semantic search for '{query}' (business={business_id}) returned {len(search_results)} results."
        )
        return search_results
