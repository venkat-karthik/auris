import pytest
import httpx
from unittest.mock import patch
from fastapi import status
from app.core import config

@pytest.mark.anyio
async def test_search_available_numbers_mock_fallback(client, auth_headers):
    # Ensure Telnyx API key is mock/empty
    with patch.object(config, "TELNYX_API_KEY", "mock-key"):
        res = await client.get("/phone-numbers/search?area_code=830", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        assert all(n["phone_number"].startswith(("+91830", "+1830")) for n in data)

@pytest.mark.anyio
async def test_search_available_numbers_telnyx_success(client, auth_headers):
    # Mock httpx response from Telnyx
    mock_response = httpx.Response(
        status_code=200,
        json={
            "data": [
                {
                    "phone_number": "+18305550199",
                    "region_information": {
                        "locality": "Del Rio",
                        "state_province": "TX"
                    }
                }
            ]
        },
        request=httpx.Request("GET", "https://api.telnyx.com/v2/available_phone_numbers")
    )
    
    original_get = httpx.AsyncClient.get
    
    async def mock_get(self, url, *args, **kwargs):
        if "api.telnyx.com" in str(url):
            return mock_response
        return await original_get(self, url, *args, **kwargs)
    
    with patch.object(config, "TELNYX_API_KEY", "real-valid-key"), \
         patch("httpx.AsyncClient.get", new=mock_get):
        
        res = await client.get("/phone-numbers/search?area_code=830", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["phone_number"] == "+18305550199"
        assert "Del Rio" in data[0]["region"]

@pytest.mark.anyio
async def test_buy_phone_number_telnyx_success(client, auth_headers, db_session):
    # Add enough credits to organisation first
    from app.models.organization import Organization
    from app.models.phone_number import PhoneNumber
    from sqlalchemy import select
    
    # Get organization and update its credits to have enough balance
    stmt = select(Organization).limit(1)
    res = await db_session.execute(stmt)
    org = res.scalar_one()
    org.balance_credits = 500.0
    await db_session.commit()

    # Mock order response from Telnyx
    mock_order_response = httpx.Response(
        status_code=201,
        json={
            "data": {
                "id": "telnyx-real-order-uuid-123",
                "status": "pending"
            }
        },
        request=httpx.Request("POST", "https://api.telnyx.com/v2/number_orders")
    )
    
    original_post = httpx.AsyncClient.post
    
    async def mock_post(self, url, *args, **kwargs):
        if "api.telnyx.com" in str(url):
            return mock_order_response
        return await original_post(self, url, *args, **kwargs)
    
    with patch.object(config, "TELNYX_API_KEY", "real-valid-key"), \
         patch.object(config, "TELNYX_CONNECTION_ID", "conn-123"), \
         patch("httpx.AsyncClient.post", new=mock_post):
        
        payload = {"phone_number": "+18305550199", "label": "Office Line"}
        res = await client.post("/phone-numbers/buy", json=payload, headers=auth_headers)
        assert res.status_code == 200
        
        # Verify response
        data = res.json()
        assert data["phone_number"] == "+18305550199"
        assert data["label"] == "Office Line"
        
        # Verify credit reduction
        await db_session.refresh(org)
        assert org.balance_credits == 340.0 # 500 - 160
        
        # Verify db insert
        stmt = select(PhoneNumber).where(PhoneNumber.phone_number == "+18305550199")
        db_res = await db_session.execute(stmt)
        number_rec = db_res.scalar_one_or_none()
        assert number_rec is not None
        assert number_rec.telnyx_id == "telnyx-real-order-uuid-123"

        # Cleanup db
        await db_session.delete(number_rec)
        await db_session.commit()




