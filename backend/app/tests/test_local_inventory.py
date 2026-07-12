import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.phone_number import AvailableInventory, PhoneNumber


@pytest.mark.asyncio
async def test_seed_and_list_local_inventory(client: AsyncClient, auth_headers: dict[str, str]):
    """Test seeding phone numbers into the local inventory pool via POST /api/v1/phone-numbers/inventory."""
    payload = {
        "phone_numbers": ["+18305550101", "+18305550102", "+918309827125"],
        "region": "Texas & Mumbai",
        "monthly_cost_usd": 2.50
    }
    res = await client.post("/phone-numbers/inventory", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert data[0]["phone_number"] == "+18305550101"
    assert data[0]["is_leased"] is False
    assert data[0]["monthly_cost_usd"] == 2.50

    # List inventory
    res_list = await client.get("/phone-numbers/inventory", headers=auth_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 3


@pytest.mark.asyncio
async def test_search_local_inventory_first(client: AsyncClient, auth_headers: dict[str, str]):
    """Test that GET /api/v1/phone-numbers/search returns numbers from the unleased local inventory pool."""
    # Seed a specific number first
    await client.post("/phone-numbers/inventory", json={
        "phone_numbers": ["+18309998877"],
        "region": "Austin, TX",
        "monthly_cost_usd": 3.00
    }, headers=auth_headers)

    res = await client.get("/phone-numbers/search?area_code=830999", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert any(item["phone_number"] == "+18309998877" and item["region"] == "Austin, TX" for item in data)


@pytest.mark.asyncio
async def test_buy_and_lease_from_local_inventory(client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession):
    """Test purchasing/leasing a number from local inventory, verifying balance deduction and pool state updates."""
    from app.models.organization import Organization
    # Top up org credits
    stmt = select(Organization).limit(1)
    res_org = await db_session.execute(stmt)
    org = res_org.scalar_one()
    org.balance_credits = 500.0
    await db_session.commit()

    # Seed inventory
    await client.post("/phone-numbers/inventory", json={
        "phone_numbers": ["+14155552671"],
        "region": "San Francisco, CA",
        "monthly_cost_usd": 2.00
    }, headers=auth_headers)

    # Buy number from local inventory
    res = await client.post("/phone-numbers/buy", json={
        "phone_number": "+14155552671",
        "label": "Local Pool Line"
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["phone_number"] == "+14155552671"
    assert data["label"] == "Local Pool Line"
    number_id = data["id"]

    # Verify inventory item is now marked leased
    inv_res = await db_session.execute(select(AvailableInventory).where(AvailableInventory.phone_number == "+14155552671"))
    inv_item = inv_res.scalar_one()
    assert inv_item.is_leased is True

    # Try buying again should fail because already leased
    res_duplicate = await client.post("/phone-numbers/buy", json={
        "phone_number": "+14155552671"
    }, headers=auth_headers)
    assert res_duplicate.status_code == 400
    assert "already leased" in res_duplicate.json()["detail"].lower()

    # Release the number
    res_del = await client.delete(f"/phone-numbers/{number_id}", headers=auth_headers)
    assert res_del.status_code == 200

    # Verify inventory item returned to unleased pool
    await db_session.refresh(inv_item)
    assert inv_item.is_leased is False
