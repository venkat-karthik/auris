"""
Tests for Prometheus metrics endpoints and monitor tracking updates.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.monitor_tracker import MonitorTracker
from app.services.metrics import AURIS_ACTIVE_CALLS, AURIS_TOTAL_CALLS_INITIATED, AURIS_TOTAL_CALLS_ENDED


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        # Test root /metrics endpoint
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        content = resp.text
        assert "auris_active_calls" in content
        assert "auris_active_listeners" in content
        assert "auris_total_calls_initiated_total" in content or "auris_total_calls_initiated" in content

        # Test prefixed /api/v1/metrics endpoint
        resp2 = await client.get("/api/v1/metrics")
        assert resp2.status_code == 200
        assert "auris_active_calls" in resp2.text


@pytest.mark.asyncio
async def test_monitor_tracker_metrics_sync():
    # Register a test call and verify Prometheus gauge updates
    MonitorTracker.register_call(
        run_id=99999,
        agent_id=1,
        agent_name="Test Agent",
        transport="webrtc",
        call_type="inbound",
        caller_number="+1234567890",
        called_number="+0987654321"
    )
    assert 99999 in MonitorTracker.active_calls
    assert AURIS_ACTIVE_CALLS._value.get() >= 1

    # End the test call and verify Prometheus updates
    MonitorTracker.end_call(run_id=99999)
    assert 99999 not in MonitorTracker.active_calls
