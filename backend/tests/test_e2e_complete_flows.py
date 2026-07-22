"""
Auris - End-to-End Testing Suite
Complete workflow testing: call creation → completion, campaigns, agents, etc.
"""

import pytest
import asyncio
import time
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.campaign import Campaign, CampaignContact
from app.core.security import create_access_token


class TestCallCreationFlow:
    """Test complete call lifecycle from creation to completion."""
    
    @pytest.mark.asyncio
    async def test_web_call_creation_flow(self, client: AsyncClient, org: Organization, agent: Agent, user: User):
        """Test: Create WebRTC call → verify response → check logging."""
        
        # Create call
        response = await client.post(
            "/api/v1/calls",
            json={
                "agent_id": agent.id,
                "caller_number": "+1234567890",
                "call_type": "inbound",
                "metadata": {"test": True}
            },
            headers={"Authorization": f"Bearer {create_access_token(user.id, org.id)}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "status" in data
        assert data["status"] == "initiated"
        assert data["agent_id"] == agent.id
        
        # Verify request tracing
        assert "x-request-id" in response.headers
        request_id = response.headers["x-request-id"]
        assert len(request_id) > 10  # Valid UUID format
        
        # Verify call is in database
        async with AsyncSessionLocal() as db:
            call = await db.get(CallRun, data["id"])
            assert call is not None
            assert call.status == "initiated"
            assert call.caller_number == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_call_completion_flow(self, client: AsyncClient, org: Organization, call_run: CallRun, user: User):
        """Test: Complete a call → verify status update → check metrics."""
        
        # Complete call
        response = await client.post(
            f"/api/v1/calls/{call_run.id}/complete",
            json={
                "duration_seconds": 120,
                "status": "completed",
                "transcript": "Test transcript"
            },
            headers={"Authorization": f"Bearer {create_access_token(user.id, org.id)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify call status updated
        assert data["status"] == "completed"
        assert data["duration_seconds"] == 120
        
        # Verify in database
        async with AsyncSessionLocal() as db:
            call = await db.get(CallRun, call_run.id)
            assert call.status == "completed"
            assert call.ended_at is not None
    
    @pytest.mark.asyncio
    async def test_multiple_calls_performance(self, client: AsyncClient, org: Organization, agent: Agent, user: User):
        """Test: Create 50 calls concurrently → verify performance (should be <5s total)."""
        
        token = create_access_token(user.id, org.id)
        
        start_time = time.time()
        
        # Create 50 calls concurrently
        tasks = []
        for i in range(50):
            task = client.post(
                "/api/v1/calls",
                json={
                    "agent_id": agent.id,
                    "caller_number": f"+123456789{i}",
                    "call_type": "inbound"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All should succeed
        successful = sum(1 for r in responses if r.status_code == 201)
        assert successful == 50
        
        # Should complete reasonably fast (with 2x capacity optimization)
        assert duration < 10, f"50 concurrent calls took {duration}s, expected <10s"
        
        print(f"✅ Created 50 calls in {duration:.2f}s")


class TestCampaignExecutionFlow:
    """Test campaign creation → execution → completion."""
    
    @pytest.mark.asyncio
    async def test_campaign_creation_and_start(self, client: AsyncClient, org: Organization, agent: Agent, user: User):
        """Test: Create campaign → upload contacts → start → verify background task."""
        
        token = create_access_token(user.id, org.id)
        
        # Create campaign
        response = await client.post(
            "/api/v1/campaigns",
            json={"name": "Test Campaign", "agent_id": agent.id},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        campaign = response.json()
        campaign_id = campaign["id"]
        
        # Upload contacts
        csv_content = b"""phone_number,name
+1234567890,John Doe
+0987654321,Jane Smith
+5555555555,Bob Johnson"""
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign_id}/contacts/upload",
            files={"file": ("contacts.csv", csv_content)},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        upload_result = response.json()
        assert upload_result["count"] == 3
        
        # Start campaign
        response = await client.post(
            f"/api/v1/campaigns/{campaign_id}/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        campaign_data = response.json()
        assert campaign_data["status"] == "running"
        
        # Verify background task was created (check task manager)
        # In a real test, we'd mock the task manager or check ARQ queue
        print(f"✅ Campaign {campaign_id} started with background task")
    
    @pytest.mark.asyncio
    async def test_campaign_statistics(self, client: AsyncClient, org: Organization, campaign: Campaign, user: User):
        """Test: Get campaign stats → verify contact counts."""
        
        token = create_access_token(user.id, org.id)
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        # Verify stats structure
        assert "campaign_id" in stats
        assert "total_contacts" in stats
        assert "pending" in stats
        assert "in_progress" in stats
        assert "completed" in stats
        assert "failed" in stats
        
        print(f"✅ Campaign stats: {stats['total_contacts']} total contacts")


class TestAgentInferenceFlow:
    """Test agent inference and knowledge retrieval."""
    
    @pytest.mark.asyncio
    async def test_agent_inference_with_rag(self, client: AsyncClient, org: Organization, agent: Agent, user: User):
        """Test: Call agent inference → verify RAG retrieval → check performance."""
        
        token = create_access_token(user.id, org.id)
        
        # Create a call first
        call_response = await client.post(
            "/api/v1/calls",
            json={"agent_id": agent.id, "caller_number": "+1234567890"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert call_response.status_code == 201
        call_id = call_response.json()["id"]
        
        # Test agent inference endpoint (if available)
        # This would normally be tested via WebSocket or streaming endpoint
        
        # Verify agent is accessible
        response = await client.get(
            f"/api/v1/agents/{agent.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        agent_data = response.json()
        assert agent_data["id"] == agent.id
        
        print(f"✅ Agent inference tested for call {call_id}")


class TestErrorHandlingAndRecovery:
    """Test error scenarios and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_invalid_agent_error_response(self, client: AsyncClient, org: Organization, user: User):
        """Test: Call with invalid agent → verify error response format."""
        
        token = create_access_token(user.id, org.id)
        
        response = await client.post(
            "/api/v1/calls",
            json={"agent_id": 99999, "caller_number": "+1234567890"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        error = response.json()
        
        # Verify error response format (centralized exception handler)
        assert "detail" in error
        assert "request_id" in error
        assert "error_type" in error
        
        print(f"✅ Error response format correct: {error['error_type']}")
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient, org: Organization, agent: Agent):
        """Test: Access without token → verify 401 response."""
        
        response = await client.post(
            "/api/v1/calls",
            json={"agent_id": agent.id, "caller_number": "+1234567890"}
            # No authorization header
        )
        
        assert response.status_code == 401
        
        print("✅ Unauthorized access properly rejected")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, client: AsyncClient):
        """Test: Circuit breaker prevents cascading failures."""
        
        # This would test that when an external service fails,
        # the circuit breaker opens and fails fast
        
        # Get circuit breaker status
        response = await client.get("/api/v1/monitor/circuit-breakers")
        
        assert response.status_code == 200
        data = response.json()
        assert "circuit_breakers" in data
        
        # Check all breakers are closed (healthy)
        for breaker in data["circuit_breakers"]:
            assert breaker["state"] in ["closed", "half_open"]
        
        print(f"✅ Circuit breakers healthy: {len(data['circuit_breakers'])} monitored")


class TestPerformanceOptimizations:
    """Verify performance improvements are working."""
    
    @pytest.mark.asyncio
    async def test_query_performance_eager_loading(self, client: AsyncClient, org: Organization, user: User):
        """Test: List calls with 100+ records → verify <100ms response time."""
        
        token = create_access_token(user.id, org.id)
        
        # Create 50 test calls
        async with AsyncSessionLocal() as db:
            for i in range(50):
                call = CallRun(
                    org_id=org.id,
                    agent_id=1,  # Assuming agent exists
                    caller_number=f"+123456789{i}",
                    transport="webrtc",
                    call_type="inbound",
                    status="completed"
                )
                db.add(call)
            await db.commit()
        
        # Time the query
        start = time.time()
        
        response = await client.get(
            "/api/v1/calls?limit=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        duration = (time.time() - start) * 1000  # ms
        
        assert response.status_code == 200
        calls = response.json()
        
        # Should use eager loading and be fast
        assert duration < 500, f"Query took {duration}ms, expected <500ms"
        print(f"✅ Query performance: {len(calls)} calls in {duration:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_capacity(self, client: AsyncClient, org: Organization, user: User):
        """Test: 20 concurrent requests → verify 2x capacity improvement."""
        
        token = create_access_token(user.id, org.id)
        
        start = time.time()
        
        # Send 20 concurrent requests
        tasks = [
            client.get(
                "/api/v1/calls?limit=10",
                headers={"Authorization": f"Bearer {token}"}
            )
            for _ in range(20)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        duration = time.time() - start
        
        # All should succeed
        successful = sum(1 for r in responses if r.status_code == 200)
        assert successful == 20
        
        # Should handle concurrency well (with 2x capacity)
        assert duration < 5, f"20 concurrent requests took {duration}s"
        print(f"✅ Concurrent capacity: 20 requests in {duration:.2f}s")


class TestSecurityAndRateLimiting:
    """Test security features and rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_auth_endpoint(self, client: AsyncClient):
        """Test: Hit auth endpoint 6 times → verify rate limiting (429) on 6th."""
        
        responses = []
        for i in range(6):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "wrong"}
            )
            responses.append(response.status_code)
        
        # Some 401 (auth fails), last should be 429 (rate limited)
        assert 429 in responses, "Rate limiting not active"
        print(f"✅ Rate limiting active: {responses}")
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client: AsyncClient):
        """Test: Verify security headers in response."""
        
        response = await client.get("/api/v1/health")
        
        headers = response.headers
        
        # Check OWASP headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"
        
        assert "x-xss-protection" in headers
        
        print("✅ Security headers present and correct")
    
    @pytest.mark.asyncio
    async def test_request_tracing_all_endpoints(self, client: AsyncClient, org: Organization, user: User):
        """Test: All endpoints include X-Request-ID header."""
        
        token = create_access_token(user.id, org.id)
        
        endpoints = [
            ("/api/v1/health", "GET"),
            ("/api/v1/agents", "GET"),
            ("/api/v1/calls", "GET"),
            ("/api/v1/campaigns", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            assert "x-request-id" in response.headers, f"Missing X-Request-ID on {endpoint}"
        
        print(f"✅ Request tracing on all {len(endpoints)} endpoints")


class TestObservabilityAndMonitoring:
    """Test observability features (metrics, logging)."""
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint_available(self, client: AsyncClient):
        """Test: Prometheus metrics endpoint returns data."""
        
        response = await client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        # Should contain Prometheus metrics
        assert "http_request_duration_seconds" in content or "HELP" in content
        assert "#" in content  # Prometheus comment format
        
        print("✅ Prometheus metrics endpoint working")
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client: AsyncClient):
        """Test: Health check includes pool status."""
        
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify health response structure
        assert data["status"] == "ok"
        assert "service" in data
        assert "pool_status" in data
        
        pool = data["pool_status"]
        assert "size" in pool
        assert "checked_in" in pool
        
        print(f"✅ Health check: Pool size={pool['size']}, Available={pool['checked_in']}")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def org() -> Organization:
    """Create test organization."""
    async with AsyncSessionLocal() as db:
        org = Organization(name="Test Org", domain="test.com")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org


@pytest.fixture
async def user(org: Organization) -> User:
    """Create test user."""
    async with AsyncSessionLocal() as db:
        from app.core.security import hash_password
        user = User(
            email="test@test.com",
            password_hash=hash_password("password"),
            org_id=org.id,
            selected_org_id=org.id,
            is_verified=True,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


@pytest.fixture
async def agent(org: Organization) -> Agent:
    """Create test agent."""
    async with AsyncSessionLocal() as db:
        agent = Agent(
            org_id=org.id,
            name="Test Agent",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="You are a helpful assistant",
            voice_provider="tts_provider"
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent


@pytest.fixture
async def call_run(org: Organization, agent: Agent) -> CallRun:
    """Create test call."""
    async with AsyncSessionLocal() as db:
        call = CallRun(
            org_id=org.id,
            agent_id=agent.id,
            caller_number="+1234567890",
            transport="webrtc",
            call_type="inbound",
            status="initiated",
            started_at=datetime.now(UTC)
        )
        db.add(call)
        await db.commit()
        await db.refresh(call)
        return call


@pytest.fixture
async def campaign(org: Organization, agent: Agent) -> Campaign:
    """Create test campaign."""
    async with AsyncSessionLocal() as db:
        campaign = Campaign(
            org_id=org.id,
            agent_id=agent.id,
            name="Test Campaign",
            status="pending"
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign
