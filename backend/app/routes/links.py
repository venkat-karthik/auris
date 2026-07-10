"""
Auris - Link tracking and redirection router
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.dependencies.rate_limit import redis_client

router = APIRouter(prefix="/links", tags=["links"])


@router.get("/click/{token}")
async def link_click(token: str):
    """
    Endpoint for tracking when a customer clicks a WhatsApp link during a call.
    Publishes an event to Redis Pub/Sub so the running call pipeline reacts in real-time.
    """
    key = f"tracked_link:{token}"
    val = await redis_client.get(key)
    if not val:
        raise HTTPException(status_code=404, detail="Link invalid or expired")

    try:
        data = json.loads(val)
        call_run_id = data.get("call_run_id")
        original_url = data.get("original_url")

        if call_run_id and original_url:
            # Publish click event to Redis pub/sub channel for this call run
            channel = f"call:link_clicks:{call_run_id}"
            await redis_client.publish(
                channel,
                json.dumps({"event": "link_clicked", "url": original_url})
            )

            # Mark as clicked
            data["clicked"] = True
            await redis_client.set(key, json.dumps(data), ex=86400)

            return RedirectResponse(url=original_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process click redirect: {e}")

    raise HTTPException(status_code=400, detail="Invalid token data structure")
