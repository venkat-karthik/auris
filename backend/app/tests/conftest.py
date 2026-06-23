import os
import sys

# Pre-set environment variables so they are loaded during app configuration
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["JWT_SECRET"] = "super-secret-test-key-which-is-long-enough-to-be-secure-12345"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_123"
os.environ["RAZORPAY_KEY_SECRET"] = "rzp_test_secret"
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "rzp_webhook_secret"

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Import our FastAPI app and db dependencies
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.organization import Organization, OrgMember
from app.models.agent import Agent
from app.models.billing import CreditTransaction
from app.core.security import hash_password, create_access_token

# Create async engine for memory SQLite DB
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@pytest.fixture(autouse=True)
async def override_get_db(db_session):
    # Override app get_db dependency
    async def _override_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def test_org(db_session) -> Organization:
    org = Organization(name="Test Org", slug="test-org", balance_credits=100.0)
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org

@pytest.fixture
async def test_user(db_session, test_org) -> User:
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        selected_org_id=test_org.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Make them org member
    member = OrgMember(org_id=test_org.id, user_id=user.id, role="owner")
    db_session.add(member)
    await db_session.commit()
    
    return user

@pytest.fixture
async def auth_headers(test_user, test_org) -> dict[str, str]:
    token = create_access_token(user_id=test_user.id, org_id=test_org.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver/api/v1"
    ) as client:
        yield client
