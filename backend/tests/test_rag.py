import uuid
import pytest
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.local import LocalEmbeddingProvider, get_embedding_provider
from app.services.rag.ingestion import RAGIngestionService, chunk_text
from app.services.rag.search import SemanticSearchService
from app.seeds.seed_service import seed_apex_dental_studio


# Deterministic test embedding provider producing predictable 384-dimensional unit vectors
class Deterministic384EmbeddingProvider(EmbeddingProvider):
    @property
    def dimension(self) -> int:
        return 384

    def embed_text(self, text: str) -> list[float]:
        # Generate deterministic vector based on character hash
        vec = [0.0] * 384
        if not text:
            return vec
        # Simple deterministic hashing into 384 dimensions
        for i, char in enumerate(text.lower()):
            idx = (ord(char) * (i + 1) * 31) % 384
            vec[idx] += 1.0
        # Normalize
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


def test_chunk_text_utility():
    text = "Paragraph one with some info.\n\nParagraph two with more details.\n\nParagraph three."
    chunks = chunk_text(text, max_chunk_size=100)
    assert len(chunks) == 3
    assert "Paragraph one" in chunks[0]
    assert "Paragraph two" in chunks[1]
    assert "Paragraph three" in chunks[2]


def test_embedding_provider_dimension_contract():
    provider = Deterministic384EmbeddingProvider()
    assert provider.dimension == 384
    vec = provider.embed_text("Apex Dental Studio")
    assert len(vec) == 384
    assert isinstance(vec[0], float)


def test_local_embedding_provider_real_model():
    provider = LocalEmbeddingProvider()
    assert provider.dimension == 384
    vec = provider.embed_text("Teeth whitening and dental exams")
    assert len(vec) == 384
    assert isinstance(vec[0], float)
    
    batch = provider.embed_batch(["First sentence", "Second sentence"])
    assert len(batch) == 2
    assert len(batch[0]) == 384
    assert len(batch[1]) == 384


@pytest.mark.asyncio
async def test_business_model_crud(db_session: AsyncSession):
    test_id = uuid.uuid4()
    biz_name = f"Test Dental Clinic {test_id.hex[:6]}"
    
    biz = Business(
        id=test_id,
        name=biz_name,
        description="A test dental clinic",
        address="100 Test Way",
        phone="555-0100",
        email="test@clinic.test",
        website="https://clinic.test",
        timezone="America/New_York",
    )
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    assert biz.id == test_id
    assert biz.name == biz_name
    assert biz.created_at is not None
    assert biz.updated_at is not None

    # Cleanup
    await db_session.delete(biz)
    await db_session.commit()


@pytest.mark.asyncio
async def test_knowledge_document_and_chunks(db_session: AsyncSession):
    provider = Deterministic384EmbeddingProvider()
    biz = Business(
        name=f"Clinic {uuid.uuid4().hex[:6]}",
        timezone="UTC",
    )
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    doc = KnowledgeDocument(
        business_id=biz.id,
        title="FAQ Document",
        source_type="faq",
        content="Question: What are hours? Answer: 9-5.",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    vec = provider.embed_text("Question: What are hours? Answer: 9-5.")
    chunk = KnowledgeChunk(
        business_id=biz.id,
        document_id=doc.id,
        content="Question: What are hours? Answer: 9-5.",
        chunk_index=0,
        embedding=vec,
        chunk_metadata={"section": "hours"},
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.business_id == biz.id
    assert chunk.document_id == doc.id
    assert len(chunk.embedding) == 384

    # Verify cascade delete when business is deleted
    await db_session.delete(biz)
    await db_session.commit()

    # Document and chunks should be gone
    res_doc = await db_session.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc.id))
    assert res_doc.scalar_one_or_none() is None
    res_chunk = await db_session.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == chunk.id))
    assert res_chunk.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_rag_ingestion_service(db_session: AsyncSession):
    provider = Deterministic384EmbeddingProvider()
    ingestion = RAGIngestionService(embedding_provider=provider)

    biz = Business(name=f"Ingest Clinic {uuid.uuid4().hex[:6]}")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)

    content = (
        "Apex Services:\nTeeth Whitening is $350.\n\n"
        "Dental Cleanings:\nRoutine cleaning is $180."
    )
    doc = await ingestion.ingest_document(
        db=db_session,
        business_id=biz.id,
        title="Services & Pricing",
        content=content,
        source_type="services",
    )

    assert doc.id is not None
    assert doc.business_id == biz.id

    chunks_stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
    result = await db_session.execute(chunks_stmt)
    chunks = result.scalars().all()
    assert len(chunks) == 2
    for c in chunks:
        assert c.business_id == biz.id
        assert len(c.embedding) == 384

    # Cleanup
    await db_session.delete(biz)
    await db_session.commit()


@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession):
    provider = Deterministic384EmbeddingProvider()
    ingestion = RAGIngestionService(embedding_provider=provider)
    search_service = SemanticSearchService(embedding_provider=provider)

    # Business A: Dental clinic
    biz_a = Business(name=f"Tenant A Dental {uuid.uuid4().hex[:6]}")
    db_session.add(biz_a)
    await db_session.commit()
    await db_session.refresh(biz_a)

    await ingestion.ingest_document(
        db=db_session,
        business_id=biz_a.id,
        title="Dental Whitening",
        content="Teeth whitening costs $350 at our dental clinic.",
        source_type="services",
    )

    # Business B: Auto repair shop
    biz_b = Business(name=f"Tenant B Auto {uuid.uuid4().hex[:6]}")
    db_session.add(biz_b)
    await db_session.commit()
    await db_session.refresh(biz_b)

    await ingestion.ingest_document(
        db=db_session,
        business_id=biz_b.id,
        title="Brake Service",
        content="Brake rotor and pad replacement costs $250 at our auto shop.",
        source_type="services",
    )

    # Search for "teeth whitening" under Business B
    # MUST return 0 results because Business B has no dental content
    results_for_b = await search_service.search(
        db=db_session,
        business_id=biz_b.id,
        query="teeth whitening",
    )
    # Check that NONE of the results belong to Business A
    for r in results_for_b:
        assert r.business_id == biz_b.id
        assert "teeth whitening" not in r.content.lower()

    # Search for "teeth whitening" under Business A
    results_for_a = await search_service.search(
        db=db_session,
        business_id=biz_a.id,
        query="teeth whitening",
    )
    assert len(results_for_a) > 0
    assert results_for_a[0].business_id == biz_a.id
    assert "teeth whitening" in results_for_a[0].content.lower()

    # Cleanup
    await db_session.delete(biz_a)
    await db_session.delete(biz_b)
    await db_session.commit()


@pytest.mark.asyncio
async def test_deterministic_apex_dental_seed(db_session: AsyncSession):
    # Run seed once using standard RAG ingestion to preserve real embeddings
    biz1, stats1 = await seed_apex_dental_studio(db_session)
    assert biz1.name == "Apex Dental Studio"
    assert stats1["documents_ingested"] == 4
    assert stats1["total_chunks"] >= 4

    # Run seed again - must be idempotent and not create duplicate businesses or duplicate chunks
    biz2, stats2 = await seed_apex_dental_studio(db_session)
    assert biz1.id == biz2.id
    assert stats2["documents_ingested"] == 4
    assert stats2["total_chunks"] == stats1["total_chunks"]

    # Verify only 1 Apex Dental Studio exists
    stmt = select(Business).where(Business.name == "Apex Dental Studio")
    res = await db_session.execute(stmt)
    all_apex = res.scalars().all()
    assert len(all_apex) == 1
