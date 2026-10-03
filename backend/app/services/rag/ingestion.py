import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.local import get_embedding_provider

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    max_chunk_size: int = 500,
    overlap_size: int = 50,
) -> List[str]:
    """Deterministically split text into readable, coherent semantic chunks.
    
    Splits preferentially by paragraphs or structured questions/answers,
    falling back to sentence/window chunking for lengthy sections.
    """
    if not text or not text.strip():
        return []

    # First split by double newlines (paragraphs, sections, or QA items)
    raw_sections = [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]
    chunks: List[str] = []

    for section in raw_sections:
        if len(section) <= max_chunk_size:
            chunks.append(section)
        else:
            # Split longer sections by lines or sentences
            lines = [l.strip() for l in section.split("\n") if l.strip()]
            current_chunk = ""
            for line in lines:
                if not current_chunk:
                    current_chunk = line
                elif len(current_chunk) + len(line) + 1 <= max_chunk_size:
                    current_chunk += " " + line
                else:
                    chunks.append(current_chunk)
                    # Begin next chunk with overlap if possible
                    overlap = current_chunk[-overlap_size:] if len(current_chunk) > overlap_size else ""
                    current_chunk = (overlap + " " + line).strip() if overlap else line
            if current_chunk:
                chunks.append(current_chunk)

    return chunks if chunks else [text.strip()]


class RAGIngestionService:
    """Service to ingest knowledge documents, generate embeddings, and persist chunks."""

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def ingest_document(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        title: str,
        content: str,
        source_type: str = "general",
        source_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeDocument:
        """Ingest or re-ingest a document for a specific business.
        
        If a document with the same title exists for this business, it replaces
        the existing chunks to ensure idempotency.
        """
        # 1. Check for existing document with same title & business_id
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.business_id == business_id,
            KnowledgeDocument.title == title,
        )
        result = await db.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc:
            doc = existing_doc
            doc.content = content
            doc.source_type = source_type
            doc.source_name = source_name
            # Delete existing chunks for this document
            await db.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
            )
            await db.flush()
        else:
            doc = KnowledgeDocument(
                business_id=business_id,
                title=title,
                source_type=source_type,
                source_name=source_name,
                content=content,
            )
            db.add(doc)
            await db.flush()

        # 2. Chunk document content
        text_chunks = chunk_text(content)
        if not text_chunks:
            logger.warning(f"No chunks extracted for document '{title}' (id={doc.id})")
            return doc

        # 3. Generate embeddings batch
        embeddings = self.embedding_provider.embed_batch(text_chunks)

        # 4. Create chunk records
        chunk_records: List[KnowledgeChunk] = []
        for idx, (chunk_text_str, vector) in enumerate(zip(text_chunks, embeddings)):
            chunk_meta = dict(metadata or {})
            chunk_meta.update({
                "source_title": title,
                "source_type": source_type,
                "chunk_index": idx,
            })
            chunk_record = KnowledgeChunk(
                business_id=business_id,
                document_id=doc.id,
                content=chunk_text_str,
                chunk_index=idx,
                embedding=vector,
                chunk_metadata=chunk_meta,
            )
            chunk_records.append(chunk_record)

        db.add_all(chunk_records)
        await db.commit()
        await db.refresh(doc)

        logger.info(
            f"Successfully ingested '{title}' for business {business_id}: "
            f"{len(chunk_records)} chunks indexed."
        )
        return doc
