from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_database_connection, check_redis_connection
from app.schemas.health import DatabaseHealth, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check endpoint verifying core components."""
    db_health_info = await check_database_connection()
    redis_available = await check_redis_connection()
    
    db_health = DatabaseHealth(
        connected=db_health_info.get("connected", False),
        pg_version=db_health_info.get("pg_version"),
        pgvector_available=db_health_info.get("pgvector_available", False),
        pgvector_version=db_health_info.get("pgvector_version"),
        error=db_health_info.get("error"),
    )
    
    overall_status = "healthy" if db_health.connected else "degraded"
    
    return HealthResponse(
        status=overall_status,
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        database=db_health,
        services={
            "redis_configured": bool(settings.REDIS_HOST),
            "redis_available": redis_available,
            "groq_configured": bool(settings.GROQ_API_KEY),
            "groq_model": settings.GROQ_MODEL,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "embedding_api_configured": bool(settings.EMBEDDING_API_KEY),
        },
    )
