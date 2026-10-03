import logging
from typing import Dict, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.seeds.apex_dental_data import APEX_DENTAL_BUSINESS, APEX_DENTAL_DOCUMENTS
from app.services.rag.ingestion import RAGIngestionService

logger = logging.getLogger(__name__)


async def seed_apex_dental_studio(
    db: AsyncSession,
    ingestion_service: RAGIngestionService = None,
) -> Tuple[Business, Dict[str, int]]:
    """Deterministically seed Apex Dental Studio and its knowledge documents.
    
    Safe to execute multiple times without creating duplicate records.
    """
    if ingestion_service is None:
        ingestion_service = RAGIngestionService()

    # 1. Upsert business
    business_name = APEX_DENTAL_BUSINESS["name"]
    stmt = select(Business).where(Business.name == business_name)
    result = await db.execute(stmt)
    business = result.scalar_one_or_none()

    if not business:
        business = Business(
            name=business_name,
            description=APEX_DENTAL_BUSINESS["description"],
            address=APEX_DENTAL_BUSINESS["address"],
            phone=APEX_DENTAL_BUSINESS["phone"],
            email=APEX_DENTAL_BUSINESS["email"],
            website=APEX_DENTAL_BUSINESS["website"],
            timezone=APEX_DENTAL_BUSINESS["timezone"],
        )
        db.add(business)
        await db.commit()
        await db.refresh(business)
        logger.info(f"Created demo business: {business.name} (id={business.id})")
    else:
        # Update existing business info
        business.description = APEX_DENTAL_BUSINESS["description"]
        business.address = APEX_DENTAL_BUSINESS["address"]
        business.phone = APEX_DENTAL_BUSINESS["phone"]
        business.email = APEX_DENTAL_BUSINESS["email"]
        business.website = APEX_DENTAL_BUSINESS["website"]
        business.timezone = APEX_DENTAL_BUSINESS["timezone"]
        await db.commit()
        await db.refresh(business)
        logger.info(f"Existing demo business updated: {business.name} (id={business.id})")

    # 2. Ingest documents and generate chunks + embeddings
    doc_count = 0
    chunk_count = 0

    for doc_data in APEX_DENTAL_DOCUMENTS:
        doc = await ingestion_service.ingest_document(
            db=db,
            business_id=business.id,
            title=doc_data["title"],
            content=doc_data["content"],
            source_type=doc_data["source_type"],
            source_name=doc_data["source_name"],
            metadata={"seed": True, "business_name": business.name},
        )
        doc_count += 1

    # Count total chunks for this business
    chunk_stmt = select(KnowledgeChunk).where(KnowledgeChunk.business_id == business.id)
    chunk_res = await db.execute(chunk_stmt)
    total_chunks = len(chunk_res.scalars().all())

    stats = {
        "documents_ingested": doc_count,
        "total_chunks": total_chunks,
    }
    logger.info(f"Seed complete for {business.name}: {stats}")
    return business, stats
