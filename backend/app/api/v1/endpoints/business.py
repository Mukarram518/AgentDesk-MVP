import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.business import Business

router = APIRouter()


class BusinessResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    timezone: str


@router.get("/business/demo", response_model=BusinessResponse)
async def get_demo_business(db: AsyncSession = Depends(get_db)) -> BusinessResponse:
    """Return the active demo business (Apex Dental Studio)."""
    stmt = select(Business).where(Business.name == "Apex Dental Studio")
    res = await db.execute(stmt)
    biz = res.scalar_one_or_none()
    if not biz:
        # Fallback to any business
        biz = (await db.execute(select(Business).limit(1))).scalar_one_or_none()
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo business not found. Please run the seed script.",
        )

    return BusinessResponse(
        id=biz.id,
        name=biz.name,
        description=biz.description,
        address=biz.address,
        phone=biz.phone,
        email=biz.email,
        website=biz.website,
        timezone=biz.timezone,
    )
