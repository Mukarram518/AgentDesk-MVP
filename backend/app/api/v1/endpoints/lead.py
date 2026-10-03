import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.business import Business
from app.models.lead import Lead
from app.schemas.lead import LeadListResponse, LeadResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/leads", response_model=LeadListResponse)
async def get_business_leads(
    business_id: uuid.UUID = Query(..., description="Business ID to retrieve leads for"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Optional filter by lead status (HOT, WARM, COLD)",
    ),
    db: AsyncSession = Depends(get_db),
) -> LeadListResponse:
    """Retrieve captured leads strictly scoped to a specific business with deterministic counts."""
    # 1. Verify business existence (enforces tenant validity)
    biz_stmt = select(Business).where(Business.id == business_id)
    biz_res = await db.execute(biz_stmt)
    biz = biz_res.scalar_one_or_none()
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found.",
        )

    # 2. Count overall leads by status for this business
    counts_stmt = (
        select(Lead.status, func.count(Lead.id))
        .where(Lead.business_id == business_id)
        .group_by(Lead.status)
    )
    counts_res = await db.execute(counts_stmt)
    status_counts = dict(counts_res.all())

    hot_count = status_counts.get("HOT", 0)
    warm_count = status_counts.get("WARM", 0)
    cold_count = status_counts.get("COLD", 0)
    total_count = hot_count + warm_count + cold_count

    # 3. Query leads for this business
    leads_stmt = select(Lead).where(Lead.business_id == business_id)
    if status_filter:
        clean_status = status_filter.strip().upper()
        leads_stmt = leads_stmt.where(Lead.status == clean_status)

    leads_stmt = leads_stmt.order_by(Lead.created_at.desc())
    leads_res = await db.execute(leads_stmt)
    lead_records = leads_res.scalars().all()

    return LeadListResponse(
        business_id=business_id,
        total_leads=total_count,
        hot_leads=hot_count,
        warm_leads=warm_count,
        cold_leads=cold_count,
        leads=[LeadResponse.model_validate(lr) for lr in lead_records],
    )
