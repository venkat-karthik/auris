import pytest
from httpx import AsyncClient
from app.main import app
from app.models.organization import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_list_and_create_organizations(client: AsyncClient, auth_headers: dict, test_user: User):
    # Test list organizations
    response = await client.get("/organizations", headers=auth_headers)
    assert response.status_code == 200
    orgs = response.json()
    assert isinstance(orgs, list)
    assert len(orgs) >= 1

    # Test create organization
    create_payload = {"name": "Test Verified Org", "slug": "test-verified-org"}
    create_res = await client.post("/organizations", headers=auth_headers, json=create_payload)
    assert create_res.status_code == 201
    new_org = create_res.json()
    assert new_org["name"] == "Test Verified Org"
    assert new_org["slug"] == "test-verified-org"

    # Test select organization
    select_res = await client.post(f"/organizations/{new_org['id']}/select", headers=auth_headers)
    assert select_res.status_code == 200
    token_data = select_res.json()
    assert "access_token" in token_data
    assert token_data["org_id"] == new_org["id"]


@pytest.mark.asyncio
async def test_list_and_get_customers(client: AsyncClient, auth_headers: dict):
    # Test list customers
    response = await client.get("/customers", headers=auth_headers)
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)


@pytest.mark.asyncio
async def test_billing_aliases(client: AsyncClient, auth_headers: dict):
    # Test transactions alias
    res = await client.get("/billing/transactions", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_whatsapp_aliases(client: AsyncClient, auth_headers: dict):
    # Test templates alias
    res = await client.get("/whatsapp/templates", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 2

