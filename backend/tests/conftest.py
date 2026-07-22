"""
Auris - Pytest Configuration & Fixtures
Provides shared fixtures for all test suites including:
- Database setup (test database)
- AsyncClient for HTTP testing
- Model fixtures (Organization, User, Agent, etc.)
- Authentication helpers
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport
from jwt import encode

from app.main import app
from app.core.database import Base, get_db
from app.core import config
from app.models.user import User
from app.models.organization import Organization
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.campaign import Campaign


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_db_session):
    """Create AsyncClient with test database."""
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def org(test_db_session) -> Organization:
    """Create test organization."""
    import uuid
    org = Organization(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        balance_credits=1000.0
    )
    test_db_session.add(org)
    await test_db_session.commit()
    await test_db_session.refresh(org)
    return org


@pytest.fixture
async def user(test_db_session, org: Organization) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        selected_org_id=org.id
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def agent(test_db_session, org: Organization, user: User) -> Agent:
    """Create test agent."""
    agent = Agent(
        org_id=org.id,
        created_by=user.id,
        name="Test Agent",
        graph={},
        model_config={"model": "gpt-4"},
        context_variables={}
    )
    test_db_session.add(agent)
    await test_db_session.commit()
    await test_db_session.refresh(agent)
    return agent


@pytest.fixture
async def call_run(test_db_session, org: Organization, agent: Agent) -> CallRun:
    """Create test call run."""
    call = CallRun(
        org_id=org.id,
        agent_id=agent.id,
        caller_number="+1234567890",
        transport="webrtc",
        call_type="inbound",
        status="initialized"
    )
    test_db_session.add(call)
    await test_db_session.commit()
    await test_db_session.refresh(call)
    return call


@pytest.fixture
async def campaign(test_db_session, org: Organization, agent: Agent) -> Campaign:
    """Create test campaign."""
    campaign = Campaign(
        organization_id=org.id,
        agent_id=agent.id,
        name="Test Campaign",
        status="created"
    )
    test_db_session.add(campaign)
    await test_db_session.commit()
    await test_db_session.refresh(campaign)
    return campaign


def create_access_token(user_id: int, org_id: int, expires_delta: timedelta = None) -> str:
    """Create JWT access token for testing."""
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": str(user_id),
        "org_id": org_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token


@pytest.fixture
def jwt_token(user: User, org: Organization) -> str:
    """Create valid JWT token for testing."""
    return create_access_token(user.id, org.id)
