import csv
import io
import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import TELNYX_API_KEY, BACKEND_URL, ENVIRONMENT, TELNYX_CONNECTION_ID, TELNYX_CALLER_ID
from app.models.campaign import CampaignContact, Campaign
from app.models.phone_number import PhoneNumber


def parse_csv_contacts(csv_content: bytes) -> list[dict]:
    """Parse contact entries from uploaded CSV data."""
    contacts = []
    try:
        content_str = csv_content.decode("utf-8-sig")
    except Exception:
        content_str = csv_content.decode("latin1", errors="ignore")
        
    f = io.StringIO(content_str)
    reader = csv.DictReader(f)
    
    # Clean field names (strip whitespace)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames] if reader.fieldnames else []
    
    phone_key = None
    for key in ["phone", "phone_number", "number", "tel", "telephone", "mobile", "contact"]:
        if key in reader.fieldnames:
            phone_key = key
            break
            
    name_key = None
    for key in ["name", "full_name", "contact_name", "first_name"]:
        if key in reader.fieldnames:
            name_key = key
            break

    if not phone_key:
        raise ValueError("CSV must contain a column for phone numbers (e.g. 'phone' or 'phone_number')")

    for row in reader:
        phone = row.get(phone_key, "").strip()
        if not phone:
            continue
        name = row.get(name_key, "").strip() if name_key else None
        contacts.append({"phone_number": phone, "name": name})
        
    return contacts


async def dial_number(db: AsyncSession, contact_id: int) -> bool:
    """Initiate outbound call via Telnyx Call Control API."""
    result = await db.execute(
        select(CampaignContact).where(CampaignContact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        logger.error(f"Contact {contact_id} not found")
        return False

    result = await db.execute(
        select(Campaign).where(Campaign.id == contact.campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        logger.error(f"Campaign not found for contact {contact_id}")
        return False

    # Telnyx Outbound Call Control API endpoint
    url = "https://api.telnyx.com/v2/calls"
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build webhook URL that Telnyx invokes when call is answered.
    # Our inbound telephony webhook receives the answered payload and connects a WebSocket.
    webhook_url = f"{BACKEND_URL}/api/v1/telephony/inbound/telnyx?org_id={campaign.org_id}&agent_id={campaign.agent_id}&call_type=outbound"
    
    phone_res = await db.execute(
        select(PhoneNumber).where(PhoneNumber.agent_id == campaign.agent_id, PhoneNumber.is_active == True)
    )
    phone_obj = phone_res.scalar_one_or_none()
    
    caller_id = phone_obj.phone_number if phone_obj else TELNYX_CALLER_ID
    connection_id = phone_obj.telnyx_id if (phone_obj and phone_obj.telnyx_id) else TELNYX_CONNECTION_ID

    payload = {
        "to": contact.phone_number,
        "from": caller_id,
        "webhook_url": webhook_url,
        "connection_id": connection_id
    }
    
    logger.info(f"Dialer: Initiating Telnyx dial-out to {contact.phone_number} for campaign={campaign.id} from={caller_id} connection={connection_id}")
    
    # If API keys are local or missing, simulate successful dial
    if not TELNYX_API_KEY or TELNYX_API_KEY.startswith("mock") or ENVIRONMENT in ("local", "test"):
        logger.warning("Telnyx API key not configured or in local/test environment. Simulating out-dial success.")
        return True

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=5.0)
            if 200 <= resp.status_code < 300:
                logger.info(f"Successfully triggered outbound call for contact {contact_id}")
                return True
            else:
                logger.error(f"Telnyx API error: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Connection to Telnyx outbound call control failed: {e}")
            return False
