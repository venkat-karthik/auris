import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.models.campaign import Campaign, CampaignContact
from app.services.pipeline.transport.telnyx_transport import TelnyxTransport
from app.routes.calls import credit_monitor_loop
from app.tasks.worker import process_call_completion, dial_next_contacts

# Helper mock classes for WebSocket async iterator
class MockWebSocketIter:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)

class MockWebSocket:
    def __init__(self, items):
        self.items = items
    def iter_text(self):
        return MockWebSocketIter(self.items)


# 1. Test Resampling logic
@pytest.mark.asyncio
async def test_telnyx_transport_resampling():
    # 80 samples of 8kHz linear PCM = 160 bytes
    dummy_pcm_8k = b"\x00\x00" * 80
    
    # Convert dummy pcm to ulaw first so we can feed it to receive_ulaw
    ulaw_data = TelnyxTransport.pcm_to_ulaw(dummy_pcm_8k)
    
    # Mock WebSocket that yields ulaw
    mock_ws = MockWebSocket([ulaw_data])
    
    pcm_chunks = []
    async for chunk in TelnyxTransport.receive_ulaw(mock_ws):
        pcm_chunks.append(chunk)
        
    assert len(pcm_chunks) == 1
    # 8kHz to 16kHz resampling should double the number of samples/bytes (allow minor filter group delay delta)
    assert abs(len(pcm_chunks[0]) - len(dummy_pcm_8k) * 2) <= 10

    # Test send_pcm downsampling (160 samples of 16kHz PCM = 320 bytes)
    dummy_pcm_16k = b"\x00\x00" * 160
    mock_send_ws = AsyncMock()
    
    ulaw_out, state = await TelnyxTransport.send_pcm(mock_send_ws, dummy_pcm_16k)
    
    # Verification
    assert mock_send_ws.send_bytes.call_count == 1
    # 16kHz downsampled to 8kHz should halve the number of samples (width=2, 80 samples = 80 bytes of ulaw)
    assert len(ulaw_out) == 80


# 2. Test Real-time Credit Metering Loop
@pytest.mark.asyncio
async def test_credit_monitor_loop(db_session, test_org, test_user):
    # Setup agent
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Billing Agent",
        model_config={"cost_tier": "standard"}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    # Setup call run
    run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="webrtc",
        call_type="inbound",
        status="running",
        credits_used=0.0,
        cost_usd=0.0
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    mock_pipeline = MagicMock()
    mock_pipeline.push = AsyncMock()
    mock_ws = AsyncMock()

    # We patch asyncio.sleep to run only once and then raise CancelledError to exit loop
    original_sleep = asyncio.sleep
    sleep_count = 0
    async def mock_sleep(secs):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count > 1:
            raise asyncio.CancelledError()
        await original_sleep(0.001)

    # Use a fresh session for the query to ensure we bypass session cache/active transaction limits
    with patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            # Org has 100.0 credits initially
            await credit_monitor_loop(run.id, test_org.id, "standard", mock_pipeline, mock_ws)
        except asyncio.CancelledError:
            pass

    async with AsyncSessionLocal() as session:
        org_res = await session.execute(select(Organization).where(Organization.id == test_org.id))
        fresh_org = org_res.scalar_one()
        run_res = await session.execute(select(CallRun).where(CallRun.id == run.id))
        fresh_run = run_res.scalar_one()
    
    assert fresh_org.balance_credits < 100.0
    assert fresh_run.credits_used > 0.0
    assert fresh_run.cost_usd > 0.0
    
    # Test termination if credits are zero
    async with AsyncSessionLocal() as session:
        org_res = await session.execute(select(Organization).where(Organization.id == test_org.id))
        db_org = org_res.scalar_one()
        db_org.balance_credits = 0.0
        await session.commit()

    sleep_count = 0
    mock_pipeline.push.reset_mock()
    mock_ws.close.reset_mock()

    with patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            await credit_monitor_loop(run.id, test_org.id, "standard", mock_pipeline, mock_ws)
        except asyncio.CancelledError:
            pass

    # Assert that pipeline call end frame and websocket close were called
    assert mock_pipeline.push.call_count > 0
    assert mock_ws.close.call_count > 0


# 3. Test Post-Call Completion remaining credit deduction (prevent double spend)
@pytest.mark.asyncio
async def test_process_call_completion(db_session, test_org, test_user):
    # Setup agent
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Worker Agent",
        model_config={"cost_tier": "standard"}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    # Setup CallRun. Say 30 seconds call.
    # standard price_per_second = 0.0008 USD. 30 sec = 0.024 USD.
    # credits = 0.024 * 83 = 1.992 credits.
    # Suppose we already deducted 1.328 credits (20 seconds) in real-time.
    run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="webrtc",
        call_type="inbound",
        status="running",
        duration_seconds=30.0,
        credits_used=1.328,
        cost_usd=0.016
    )
    db_session.add(run)
    
    test_org.balance_credits = 10.0
    db_session.add(test_org)
    await db_session.commit()

    # Run the ARQ task completion worker
    await process_call_completion(None, run.id)

    # Refresh in fresh session to bypass cache
    async with AsyncSessionLocal() as session:
        org_res = await session.execute(select(Organization).where(Organization.id == test_org.id))
        fresh_org = org_res.scalar_one()
        run_res = await session.execute(select(CallRun).where(CallRun.id == run.id))
        fresh_run = run_res.scalar_one()

    # Total credits for 30s standard call = 30 * 0.0008 * 83 = 1.992.
    # Remaining to deduct: 1.992 - 1.328 = 0.664.
    # New balance should be 10.0 - 0.664 = 9.336 credits.
    assert abs(fresh_run.credits_used - 1.992) < 0.001
    assert abs(fresh_org.balance_credits - 9.336) < 0.001


# 4. Test Dialer Concurrency Throttling
@pytest.mark.asyncio
async def test_dialer_concurrency_throttling(db_session, test_org, test_user):
    # Setup agent
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Dialer Agent",
        model_config={"stt": {"provider": "deepgram"}}
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    # Setup campaign
    campaign = Campaign(
        org_id=test_org.id,
        agent_id=agent.id,
        name="Test Dialer Campaign",
        status="running"
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    # 1. Max limit is 5. Insert 5 "in_progress" contacts and 1 "pending".
    for i in range(5):
        contact_in_progress = CampaignContact(
            campaign_id=campaign.id,
            phone_number=f"+91999990000{i}",
            name=f"Progress User {i}",
            status="in_progress"
        )
        db_session.add(contact_in_progress)
        
    pending_contact = CampaignContact(
        campaign_id=campaign.id,
        phone_number="+918888800000",
        name="Pending User",
        status="pending"
    )
    db_session.add(pending_contact)
    await db_session.commit()

    # Call dial_next_contacts and mock redis
    mock_redis = MagicMock()
    mock_redis.enqueue_job = AsyncMock()
    ctx = {"redis": mock_redis}

    with patch("app.services.dialer_service.dial_number", return_value=True) as mock_dial:
        await dial_next_contacts(ctx, campaign.id)

        # The dialer should defer/schedule again without dialing the pending contact
        assert mock_dial.call_count == 0
        assert mock_redis.enqueue_job.call_count == 1
        mock_redis.enqueue_job.assert_called_with("dial_next_contacts", campaign.id, _defer_by=5)

        # 2. Concurrency falls below limit. Mark one contact as completed.
        # So we have 4 "in_progress" and 1 "pending".
        # It should successfully trigger dial_number on the pending contact.
        async with AsyncSessionLocal() as session:
            res_contacts = await session.execute(
                select(CampaignContact).where(CampaignContact.phone_number == "+919999900000")
            )
            completed_contact = res_contacts.scalar_one_or_none()
            completed_contact.status = "completed"
            await session.commit()

        mock_redis.enqueue_job.reset_mock()
        mock_dial.reset_mock()

        await dial_next_contacts(ctx, campaign.id)

        # Verify that the pending contact was dialed
        assert mock_dial.call_count == 1
        # Check that it enqueues next loop check
        assert mock_redis.enqueue_job.call_count == 1
