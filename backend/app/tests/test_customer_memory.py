import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.customer_profile import CustomerProfile
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.models.organization import Organization
from app.services.customer_memory import lookup_customer, upsert_customer
from app.tasks.worker import process_call_completion, update_customer_profile

class MockSessionContext:
    def __init__(self, session):
        self.session = session
    async def __aenter__(self):
        return self.session
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass



@pytest.mark.asyncio
async def test_lookup_customer_not_found(db_session: AsyncSession):
    # Lookup non-existent number
    prompt = await lookup_customer(db_session, org_id=1, phone_number="+919999999999")
    assert prompt is None


@pytest.mark.asyncio
async def test_lookup_customer_found(db_session: AsyncSession, test_org):
    # Setup customer profile
    profile = CustomerProfile(
        org_id=test_org.id,
        phone_number="+918888888888",
        name="Karthik",
        call_count=3,
        summary="Repeat business call.",
        preferences={"topic": "pricing"}
    )
    db_session.add(profile)
    await db_session.commit()

    prompt = await lookup_customer(db_session, test_org.id, "+918888888888")
    assert prompt is not None
    assert "Karthik" in prompt
    assert "Repeat business call." in prompt
    assert "topic" in prompt
    assert "3" in prompt


@pytest.mark.asyncio
async def test_upsert_customer_spam_guard_triggered(db_session: AsyncSession, test_org):
    # Call duration is under 60 seconds, should not create a new profile (spam guard)
    await upsert_customer(
        db=db_session,
        org_id=test_org.id,
        phone_number="+917777777777",
        duration_seconds=45.0,
        transcript="User: Hello. Agent: Hi."
    )

    result = await db_session.execute(
        select(CustomerProfile).where(
            CustomerProfile.org_id == test_org.id,
            CustomerProfile.phone_number == "+917777777777"
        )
    )
    profile = result.scalar_one_or_none()
    assert profile is None


@pytest.mark.asyncio
async def test_upsert_customer_creates_profile(db_session: AsyncSession, test_org):
    # Mock LLM response
    mock_llm_response = {
        "name": "Rajesh",
        "summary": "Wanted to check standard prices.",
        "preferences": {"tier": "standard"}
    }
    
    with patch("app.services.customer_memory.generate_customer_update", return_value=mock_llm_response):
        # Call duration is over 60 seconds, should create a new profile
        await upsert_customer(
            db=db_session,
            org_id=test_org.id,
            phone_number="+916666666666",
            duration_seconds=75.0,
            transcript="User: My name is Rajesh. I'm checking pricing. Agent: Sure."
        )

        result = await db_session.execute(
            select(CustomerProfile).where(
                CustomerProfile.org_id == test_org.id,
                CustomerProfile.phone_number == "+916666666666"
            )
        )
        profile = result.scalar_one_or_none()
        assert profile is not None
        assert profile.name == "Rajesh"
        assert profile.call_count == 1
        assert profile.summary == "Wanted to check standard prices."
        assert profile.preferences["tier"] == "standard"


@pytest.mark.asyncio
async def test_upsert_customer_updates_existing_repeat_caller(db_session: AsyncSession, test_org):
    # Setup existing profile
    profile = CustomerProfile(
        org_id=test_org.id,
        phone_number="+915555555555",
        name="Original Name",
        call_count=1,
        summary="Original summary.",
        preferences={"original_key": "val"}
    )
    db_session.add(profile)
    await db_session.commit()

    # Mock LLM response
    mock_llm_response = {
        "name": "Updated Name",
        "summary": "New interaction info.",
        "preferences": {"new_key": "new_val"}
    }
    
    with patch("app.services.customer_memory.generate_customer_update", return_value=mock_llm_response):
        # Call duration under 60 seconds, but since repeat caller exists, it should update it!
        await upsert_customer(
            db=db_session,
            org_id=test_org.id,
            phone_number="+915555555555",
            duration_seconds=30.0,
            transcript="User: I have returned."
        )

        # Refresh
        result = await db_session.execute(
            select(CustomerProfile).where(
                CustomerProfile.org_id == test_org.id,
                CustomerProfile.phone_number == "+915555555555"
            )
        )
        profile = result.scalar_one_or_none()
        assert profile is not None
        assert profile.name == "Updated Name"
        assert profile.call_count == 2
        assert profile.summary == "New interaction info."
        # Preferences should be merged
        assert profile.preferences["original_key"] == "val"
        assert profile.preferences["new_key"] == "new_val"


@pytest.mark.asyncio
async def test_process_call_completion_task(db_session: AsyncSession, test_org, test_user):
    # Setup Agent
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Test Agent",
        model_config={"cost_tier": "premium"}  # premium pricing: 0.0016 / sec
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    # Setup CallRun
    run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="telnyx",
        call_type="inbound",
        status="running",
        duration_seconds=100.0  # 100 seconds
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    # Org balance initially 100.0
    assert test_org.balance_credits == 100.0

    # Mock DB context in task
    with patch("app.tasks.worker.AsyncSessionLocal", return_value=MockSessionContext(db_session)):
        await process_call_completion(None, run.id)

    # Refresh
    await db_session.refresh(run)
    await db_session.refresh(test_org)

    # Expected: cost_usd = 100 * 0.0016 = 0.16
    # credits_used = 0.16 * 83 = 13.28
    assert run.cost_usd == 0.16
    assert abs(run.credits_used - 13.28) < 0.01
    # New balance should be 100.0 - 13.28 = 86.72
    assert abs(test_org.balance_credits - 86.72) < 0.01


@pytest.mark.asyncio
async def test_update_customer_profile_task(db_session: AsyncSession, test_org, test_user):
    # Setup Agent
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Test Agent",
        model_config={"cost_tier": "standard"}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    # Setup CallRun
    run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="telnyx",
        call_type="inbound",
        status="completed",
        caller_number="+914444444444",
        duration_seconds=120.0,
        transcript_path="mock_bucket/transcripts/run_123.txt"
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    # Mock download file and upsert
    mock_transcript = b"User: Rajesh here. Agent: Hi."
    mock_llm_response = {
        "name": "Rajesh Kumar",
        "summary": "Checking in.",
        "preferences": {"lang": "Hindi"}
    }

    with (
        patch("app.tasks.worker.AsyncSessionLocal", return_value=MockSessionContext(db_session)),
        patch("app.tasks.worker.download_file_from_minio", return_value=mock_transcript),
        patch("app.services.customer_memory.generate_customer_update", return_value=mock_llm_response)
    ):
        await update_customer_profile(None, run.id)

    # Verify profile created
    result = await db_session.execute(
        select(CustomerProfile).where(
            CustomerProfile.org_id == test_org.id,
            CustomerProfile.phone_number == "+914444444444"
        )
    )
    profile = result.scalar_one_or_none()
    assert profile is not None
    assert profile.name == "Rajesh Kumar"
    assert profile.summary == "Checking in."
    assert profile.preferences["lang"] == "Hindi"
