import logging
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.lead import Lead
from app.schemas.chat import ChatLeadStatus, ChatResponse, ChatSource
from app.services.lead.extractor import LeadExtractor
from app.services.lead.scoring import LeadScoringService
from app.services.llm.base import LLMProvider
from app.services.llm import get_llm_provider
from app.services.prompt import get_grounded_system_prompt
from app.services.rag.search import SemanticSearchService

logger = logging.getLogger(__name__)

# Minimum cosine similarity threshold to consider retrieved knowledge relevant
MIN_RELEVANCE_THRESHOLD = 0.22


class ChatService:
    """Core application service managing customer chat interactions, RAG grounding, and lead capture."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        search_service: Optional[SemanticSearchService] = None,
    ):
        self.llm_provider = llm_provider or get_llm_provider()
        self.search_service = search_service or SemanticSearchService()

    async def get_or_default_business(
        self,
        db: AsyncSession,
        business_id: Optional[uuid.UUID] = None,
    ) -> Business:
        """Resolve the requested business, or default to the seeded Apex Dental Studio."""
        if business_id:
            stmt = select(Business).where(Business.id == business_id)
            result = await db.execute(stmt)
            biz = result.scalar_one_or_none()
            if biz:
                return biz
            raise ValueError(f"Business with ID {business_id} not found.")

        # Default to Apex Dental Studio demo business
        stmt = select(Business).where(Business.name == "Apex Dental Studio")
        result = await db.execute(stmt)
        biz = result.scalar_one_or_none()
        if biz:
            return biz

        # Fallback to any business in DB
        any_biz = (await db.execute(select(Business).limit(1))).scalar_one_or_none()
        if any_biz:
            return any_biz

        raise RuntimeError("No demo business found in database. Please run the database seed first.")

    async def answer_customer_message(
        self,
        db: AsyncSession,
        message: str,
        business_id: Optional[uuid.UUID] = None,
    ) -> ChatResponse:
        """Process customer question, retrieve grounded RAG context, capture leads, and generate an answer."""
        clean_msg = message.strip()
        if not clean_msg:
            raise ValueError("Message cannot be empty.")

        # 1. Resolve business
        business = await self.get_or_default_business(db, business_id)

        # 2. Lead Detection & Deterministic Scoring
        extracted_info = LeadExtractor.extract_info(clean_msg)
        score_result = LeadScoringService.evaluate(clean_msg, extracted_info)

        lead_status = ChatLeadStatus(created=False, status=None, score=None)
        if score_result.is_lead:
            try:
                lead_record = Lead(
                    business_id=business.id,
                    name=extracted_info.name,
                    email=extracted_info.email,
                    phone=extracted_info.phone,
                    message=clean_msg,
                    intent=score_result.intent,
                    status=score_result.status,
                    score=score_result.score,
                )
                db.add(lead_record)
                await db.commit()
                await db.refresh(lead_record)
                lead_status = ChatLeadStatus(
                    created=True,
                    status=score_result.status,
                    score=score_result.score,
                )
                logger.info(
                    f"Captured new lead for business {business.id}: "
                    f"id={lead_record.id}, status={score_result.status}, score={score_result.score}"
                )
            except Exception as e:
                logger.error(f"Failed to persist lead record: {e}", exc_info=True)
                await db.rollback()

        # 3. Run semantic search strictly scoped to this business
        raw_results = await self.search_service.search(
            db=db,
            business_id=business.id,
            query=clean_msg,
            top_k=3,
        )

        # 4. Filter by relevance threshold
        relevant_chunks = [r for r in raw_results if r.score >= MIN_RELEVANCE_THRESHOLD]

        # 5. If no relevant chunks, handle gracefully without hallucinating
        if not relevant_chunks:
            logger.info(
                f"No relevant knowledge above threshold ({MIN_RELEVANCE_THRESHOLD}) for query '{clean_msg}'"
            )
            phone_text = f" at {business.phone}" if business.phone else ""
            fallback_answer = (
                f"I'm sorry, but that information is not available in the {business.name} knowledge base. "
                f"Please contact us directly{phone_text} for assistance."
            )
            return ChatResponse(answer=fallback_answer, sources=[], lead=lead_status)

        # 6. Assemble grounded context and deduplicate sources
        context_parts: List[str] = []
        safe_sources: List[ChatSource] = []
        seen_titles = set()

        for chunk in relevant_chunks:
            title = chunk.document_title or "Clinic Information"
            context_parts.append(f"[{title}]\n{chunk.content}")
            if title not in seen_titles:
                safe_sources.append(ChatSource(document_title=title, score=chunk.score))
                seen_titles.add(title)

        grounded_context = "\n\n---\n\n".join(context_parts)

        # 7. Build prompt and invoke LLM
        system_prompt = get_grounded_system_prompt(
            business_name=business.name,
            phone=business.phone,
            email=business.email,
        )

        answer = await self.llm_provider.generate_response(
            system_prompt=system_prompt,
            user_message=clean_msg,
            context=grounded_context,
            temperature=0.2,
        )

        return ChatResponse(answer=answer, sources=safe_sources, lead=lead_status)
