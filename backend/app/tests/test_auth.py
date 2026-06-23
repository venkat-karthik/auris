import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.organization import Organization

@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword",
        "full_name": "New User",
        "org_name": "New Org"
    }
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] is not None
    assert data["org_id"] is not None

    # Check user in DB
    result = await db_session.execute(select(User).where(User.email == "newuser@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "New User"
    assert user.selected_org_id == data["org_id"]

@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient, test_user):
    payload = {
        "email": test_user.email,
        "password": "anotherpassword",
        "full_name": "Duplicate User",
        "org_name": "Duplicate Org"
    }
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    payload = {
        "email": test_user.email,
        "password": "password123"
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == test_user.id
    assert data["org_id"] == test_user.selected_org_id

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user):
    payload = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers, test_user):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id

@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401
