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


def test_database_url_ssl_handling():
    from app.core.config import Settings
    from sqlalchemy.engine import make_url
    from sqlalchemy.dialects.postgresql.asyncpg import PGDialect_asyncpg

    dialect = PGDialect_asyncpg()

    # 1. Neon production URL with ?sslmode=require
    neon_settings = Settings(
        DATABASE_URL="postgresql://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?sslmode=require",
        SYNC_DATABASE_URL=None,
    )
    assert neon_settings.async_database_url == "postgresql+asyncpg://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?ssl=require"
    _, cparams = dialect.create_connect_args(make_url(neon_settings.async_database_url))
    assert "sslmode" not in cparams
    assert cparams.get("ssl") == "require"
    assert neon_settings.sync_database_url == "postgresql+psycopg2://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?sslmode=require"

    # 2. Neon URL with channel_binding and sslmode
    neon_cb_settings = Settings(
        DATABASE_URL="postgresql://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
        SYNC_DATABASE_URL=None,
    )
    assert neon_cb_settings.async_database_url == "postgresql+asyncpg://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?ssl=require"
    _, cb_cparams = dialect.create_connect_args(make_url(neon_cb_settings.async_database_url))
    assert "sslmode" not in cb_cparams
    assert "channel_binding" not in cb_cparams
    assert cb_cparams.get("ssl") == "require"

    # 3. Explicit postgresql+asyncpg format
    asyncpg_settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?sslmode=require",
        SYNC_DATABASE_URL=None,
    )
    assert asyncpg_settings.async_database_url == "postgresql+asyncpg://user:secret@ep-cool-frog.us-east-2.aws.neon.tech/neondb?ssl=require"

