import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.lead import Lead
from app.seeds.seed_service import seed_apex_dental_studio
from app.services.lead.extractor import LeadExtractor
from app.services.lead.scoring import LeadScoringService


def test_lead_scoring_determinism():
    """Verify lead scoring function is 100% deterministic and reproducible."""
    msg_hot = "I want to book teeth whitening. My name is Ali and my email is ali@example.com."
    msg_warm = "How much does teeth whitening cost? I'm interested."
    msg_info = "What are your opening hours?"

    # Run each evaluation 5 times and assert identical scores
    res_hot = [LeadScoringService.evaluate(msg_hot) for _ in range(5)]
    res_warm = [LeadScoringService.evaluate(msg_warm) for _ in range(5)]
    res_info = [LeadScoringService.evaluate(msg_info) for _ in range(5)]

    assert all(r.score == res_hot[0].score and r.status == "HOT" for r in res_hot)
    assert all(r.score == res_warm[0].score and r.status == "WARM" for r in res_warm)
    assert all(r.is_lead is False and r.status is None for r in res_info)


@pytest.mark.asyncio
async def test_no_lead_on_hours_question(client: AsyncClient, db_session: AsyncSession):
    """Informational questions must not create a lead record."""
    await seed_apex_dental_studio(db_session)

    # Count existing leads before request
    initial_count = (await db_session.execute(select(Lead))).scalars().all()

    response = await client.post(
        "/api/v1/chat",
        json={"message": "What are your opening hours?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "lead" in data
    assert data["lead"]["created"] is False
    assert data["lead"]["status"] is None
    assert data["lead"]["score"] is None

    # Verify no new row in leads table
    final_count = (await db_session.execute(select(Lead))).scalars().all()
    assert len(final_count) == len(initial_count)


@pytest.mark.asyncio
async def test_warm_lead_pricing_interest(client: AsyncClient, db_session: AsyncSession):
    """Pricing inquiry with expressed interest creates a WARM lead."""
    await seed_apex_dental_studio(db_session)

    response = await client.post(
        "/api/v1/chat",
        json={"message": "How much does teeth whitening cost? I'm interested."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead"]["created"] is True
    assert data["lead"]["status"] == "WARM"
    assert 40 <= data["lead"]["score"] < 80


@pytest.mark.asyncio
async def test_hot_lead_booking_and_contact(client: AsyncClient, db_session: AsyncSession):
    """Booking intent with customer contact info creates a HOT lead with extracted fields."""
    biz, _ = await seed_apex_dental_studio(db_session)

    msg = "I want to book teeth whitening. My name is Ali and my email is ali@example.com."
    response = await client.post(
        "/api/v1/chat",
        json={"message": msg},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead"]["created"] is True
    assert data["lead"]["status"] == "HOT"
    assert data["lead"]["score"] >= 80

    # Verify lead was persisted with exact fields in database
    stmt = (
        select(Lead)
        .where(Lead.business_id == biz.id, Lead.email == "ali@example.com")
        .order_by(Lead.created_at.desc())
    )
    res = await db_session.execute(stmt)
    lead = res.scalars().first()
    assert lead is not None

    assert lead.name == "Ali"
    assert lead.email == "ali@example.com"
    assert lead.phone is None  # Unsupplied contact info remains null
    assert lead.status == "HOT"


@pytest.mark.asyncio
async def test_lead_missing_contact_info_remains_null(client: AsyncClient, db_session: AsyncSession):
    """Booking request without contact details captures intent but leaves contact fields null."""
    biz, _ = await seed_apex_dental_studio(db_session)

    unique_query = f"I want to book a cleaning for my appointment {uuid.uuid4().hex[:6]}."
    response = await client.post(
        "/api/v1/chat",
        json={"message": unique_query},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead"]["created"] is True
    assert data["lead"]["status"] == "HOT"

    # Query the created lead
    stmt = select(Lead).where(Lead.message == unique_query)
    lead = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lead is not None
    assert lead.name is None
    assert lead.email is None
    assert lead.phone is None
    assert lead.status == "HOT"


@pytest.mark.asyncio
async def test_lead_tenant_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify GET /api/v1/leads strictly enforces business scoping and tenant isolation."""
    # Create two isolated businesses
    biz_a = Business(name=f"Tenant Clinic A {uuid.uuid4().hex[:6]}")
    biz_b = Business(name=f"Tenant Clinic B {uuid.uuid4().hex[:6]}")
    db_session.add_all([biz_a, biz_b])
    await db_session.commit()
    await db_session.refresh(biz_a)
    await db_session.refresh(biz_b)

    # Add a lead for Business A
    lead_a = Lead(
        business_id=biz_a.id,
        name="Patient A",
        email="a@example.com",
        message="I want to book at clinic A",
        intent="booking",
        status="HOT",
        score=95,
    )
    # Add a lead for Business B
    lead_b = Lead(
        business_id=biz_b.id,
        name="Patient B",
        email="b@example.com",
        message="I want to book at clinic B",
        intent="booking",
        status="HOT",
        score=95,
    )
    db_session.add_all([lead_a, lead_b])
    await db_session.commit()

    # Request leads for Business A
    resp_a = await client.get(f"/api/v1/leads?business_id={biz_a.id}")
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert data_a["business_id"] == str(biz_a.id)
    assert data_a["total_leads"] == 1
    assert data_a["hot_leads"] == 1
    assert len(data_a["leads"]) == 1
    assert data_a["leads"][0]["name"] == "Patient A"
    # Verify no leaks from Business B
    assert not any(l["name"] == "Patient B" for l in data_a["leads"])

    # Request leads for Business B
    resp_b = await client.get(f"/api/v1/leads?business_id={biz_b.id}")
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["business_id"] == str(biz_b.id)
    assert len(data_b["leads"]) == 1
    assert data_b["leads"][0]["name"] == "Patient B"

    # Cleanup
    await db_session.delete(lead_a)
    await db_session.delete(lead_b)
    await db_session.delete(biz_a)
    await db_session.delete(biz_b)
    await db_session.commit()


@pytest.mark.asyncio
async def test_lead_api_invalid_business_id(client: AsyncClient):
    """Requesting leads for a non-existent business must return 404."""
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/leads?business_id={random_id}")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
