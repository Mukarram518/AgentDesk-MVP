import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LeadResponse(BaseModel):
    """Business lead response model for owner dashboard."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: str
    intent: Optional[str] = None
    status: str
    score: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    """List of leads along with summary counters for the owner dashboard."""
    business_id: uuid.UUID
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    leads: List[LeadResponse]
