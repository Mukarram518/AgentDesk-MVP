from typing import List, Union
from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "AgentDesk MVP"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "https://agent-desk-mvp.vercel.app",
    ]

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5434
    POSTGRES_DB: str = "agentdesk"
    
    # Custom DATABASE_URL if supplied, otherwise constructed from parts
    DATABASE_URL: Union[str, None] = None
    SYNC_DATABASE_URL: Union[str, None] = None

    @computed_field
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL)
            # Ensure asyncpg driver
            if url.drivername.startswith("postgresql") or url.drivername.startswith("postgres"):
                url = url.set(drivername="postgresql+asyncpg")

            # asyncpg accepts 'ssl' (e.g. ssl='require'), not 'sslmode'
            query = dict(url.query)
            if "sslmode" in query:
                ssl_mode = query.pop("sslmode")
                if "ssl" not in query:
                    query["ssl"] = ssl_mode
            query.pop("channel_binding", None)
            url = url.set(query=query)

            return url.render_as_string(hide_password=False)

        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL)
            if url.drivername.startswith("postgresql") or url.drivername.startswith("postgres"):
                url = url.set(drivername="postgresql+psycopg2")

            query = dict(url.query)
            if "ssl" in query and "sslmode" not in query:
                query["sslmode"] = query.pop("ssl")
            url = url.set(query=query)

            return url.render_as_string(hide_password=False)

        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Provider (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # Embeddings (Local Sentence Transformers or Hosted API)
    EMBEDDING_PROVIDER: str = "local"  # "local" or "api"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_API_URL: str = (
        "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
    )
    EMBEDDING_API_KEY: str = ""


settings = Settings()
