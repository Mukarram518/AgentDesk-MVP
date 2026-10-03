import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == settings.VERSION
    assert "/api/v1/health" in data["health"]


@pytest.mark.asyncio
async def test_health_endpoint_structure(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    
    # Assert core fields exist
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert data["project_name"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert data["environment"] == settings.ENVIRONMENT
    assert "timestamp" in data
    assert "database" in data
    assert "services" in data
    
    # Assert services configuration
    services = data["services"]
    assert services["groq_model"] == "openai/gpt-oss-20b"
    assert services["embedding_provider"] == "local"
    assert services["embedding_dimension"] == 384
    assert services["redis_configured"] is True
    assert services["redis_available"] is True
    
    # Assert database and pgvector verification
    database = data["database"]
    assert database["connected"] is True
    assert database["pgvector_available"] is True
    assert database["pgvector_version"] is not None


def test_settings_configuration():
    assert settings.PROJECT_NAME == "AgentDesk MVP"
    assert settings.GROQ_MODEL == "openai/gpt-oss-20b"
    assert settings.EMBEDDING_MODEL_NAME == "all-MiniLM-L6-v2"
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.POSTGRES_PORT == 5434
