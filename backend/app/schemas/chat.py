import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatSource(BaseModel):
    """Safe, explainable source metadata for frontend/debugging."""
    document_title: str = Field(..., description="Title of the source knowledge document")
    score: float = Field(..., description="Cosine similarity score (0 to 1)")


class ChatLeadStatus(BaseModel):
    """Lead detection and status captured from chat interaction."""
    created: bool = Field(False, description="Whether a new lead was captured from this interaction")
    status: Optional[str] = Field(None, description="HOT, WARM, or COLD")
    score: Optional[int] = Field(None, description="Deterministic lead score (0-100)")


class ChatRequest(BaseModel):
    """Customer chat message request payload."""
    business_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Target business ID. If omitted, defaults to the seeded demo business (Apex Dental Studio).",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The customer's question or message",
    )


class ChatResponse(BaseModel):
    """Grounded AI chat response payload."""
    answer: str = Field(..., description="Grounded assistant answer")
    sources: List[ChatSource] = Field(
        default_factory=list,
        description="List of verified knowledge sources used to ground the answer",
    )
    lead: ChatLeadStatus = Field(
        default_factory=ChatLeadStatus,
        description="Lead status resulting from the customer's message",
    )
