import json
import urllib.request
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal
from app.models.lead import Lead
from sqlalchemy import select


API_URL = "http://127.0.0.1:8000/api/v1/chat"

test_queries = [
    "How much does teeth whitening cost and what does it include?",
    "What are your opening hours?",
    "I want to book teeth whitening. My name is Ali and my email is ali@example.com.",
    "Do you perform brain surgery?",
]

print("=" * 70)
print("AgentDesk-MVP Final End-to-End Verification")
print("Target Endpoint: POST /api/v1/chat")
print("=" * 70)

for idx, q in enumerate(test_queries, 1):
    print("\n" + "=" * 70)
    print(f"TEST {idx}: \"{q}\"")
    print("-" * 70)
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"message": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("ACTUAL ANSWER:")
        print(data["answer"])
        print("\nSOURCES RETURNED:")
        sources = data.get("sources", [])
        if sources:
            for s in sources:
                print(f"  * {s['document_title']} (score: {s.get('score', 'N/A')})")
        else:
            print("  [None - Filtered / Out of Knowledge Base]")
        
        lead_info = data.get("lead", {})
        print("\nLEAD CAPTURE RESULT:")
        print(f"  created : {lead_info.get('created')}")
        print(f"  status  : {lead_info.get('status')}")
        print(f"  score   : {lead_info.get('score')}")

# Verify Lead persistence in PostgreSQL for Ali
async def verify_db_lead():
    print("\n" + "=" * 70)
    print("VERIFYING LEAD PERSISTENCE IN POSTGRESQL DATABASE")
    print("-" * 70)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Lead)
            .where(Lead.email == "ali@example.com")
            .order_by(Lead.created_at.desc())
        )
        res = await session.execute(stmt)
        lead = res.scalars().first()
        if lead:
            print("FOUND LEAD IN DATABASE:")
            print(f"  id          : {lead.id}")
            print(f"  business_id : {lead.business_id}")
            print(f"  name        : {lead.name}")
            print(f"  email       : {lead.email}")
            print(f"  phone       : {lead.phone}")
            print(f"  intent      : {lead.intent}")
            print(f"  status      : {lead.status}")
            print(f"  score       : {lead.score}")
            print(f"  created_at  : {lead.created_at}")
        else:
            print("ERROR: Lead for ali@example.com was not found in PostgreSQL!")

asyncio.run(verify_db_lead())
print("\n" + "=" * 70)
print("FINAL END-TO-END VERIFICATION RUN COMPLETE")
print("=" * 70)
