import asyncio
import logging
from app.core.database import AsyncSessionLocal
from app.seeds.seed_service import seed_apex_dental_studio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("seed_runner")


async def main():
    logger.info("Starting Apex Dental Studio database seed...")
    async with AsyncSessionLocal() as session:
        business, stats = await seed_apex_dental_studio(session)
        print("\n" + "=" * 50)
        print(f"SEED COMPLETE: {business.name}")
        print(f"Business ID: {business.id}")
        print(f"Documents Ingested: {stats['documents_ingested']}")
        print(f"Total Vector Chunks: {stats['total_chunks']}")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
