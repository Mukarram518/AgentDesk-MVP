from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    connected: bool
    pg_version: Optional[str] = None
    pgvector_available: bool = False
    pgvector_version: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application status: healthy or degraded")
    project_name: str
    version: str
    environment: str
    timestamp: datetime
    database: DatabaseHealth
    services: Dict[str, Any] = Field(default_factory=dict)
