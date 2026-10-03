import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """Check connectivity to PostgreSQL and whether pgvector extension is available."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            pg_version = result.scalar()
            
            # Check for pgvector extension
            ext_result = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            )
            vector_version = ext_result.scalar()
            
            return {
                "connected": True,
                "pg_version": pg_version,
                "pgvector_available": bool(vector_version),
                "pgvector_version": vector_version,
            }
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return {
            "connected": False,
            "error": str(e),
            "pgvector_available": False,
            "pgvector_version": None,
        }


async def check_redis_connection() -> bool:
    """Check connectivity to Redis via asynchronous TCP ping."""
    import asyncio
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(settings.REDIS_HOST, settings.REDIS_PORT),
            timeout=1.0,
        )
        writer.write(b"PING\r\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.read(100), timeout=1.0)
        writer.close()
        await writer.wait_closed()
        return response.startswith(b"+PONG")
    except Exception as e:
        logger.debug(f"Redis check failed: {e}")
        return False
