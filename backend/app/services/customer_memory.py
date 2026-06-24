"""
Auris - Customer Memory Services
Handles profile lookup injection and post-call transcript summarization/upsert.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from loguru import logger
from datetime import UTC, datetime
from openai import AsyncOpenAI

from app.models.customer_profile import CustomerProfile
from app.core.config import OPENAI_API_KEY

async def lookup_customer(db: AsyncSession, org_id: int, phone_number: str) -> str | None:
    """
    Look up customer profile by org_id and phone_number.
    Returns a prompt injection string or None.
    """
    if not phone_number:
        return None
    
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.org_id == org_id,
            CustomerProfile.phone_number == phone_number
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return None
        
    prompt_chunk = (
        f"\n\n[Customer Memory - Returning Caller Info]\n"
        f"This customer is a repeat caller.\n"
        f"Name: {profile.name or 'Unknown'}\n"
        f"Interaction Summary: {profile.summary or 'None'}\n"
        f"Preferences: {json.dumps(profile.preferences)}\n"
        f"Call count: {profile.call_count}\n"
    )
    return prompt_chunk

async def generate_customer_update(transcript: str) -> dict:
    """
    Use LLM to generate customer updates from raw transcript.
    Returns a dict with: name, summary, preferences.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, skipping customer memory LLM extraction")
        return {"name": None, "summary": "Call completed.", "preferences": {}}
        
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "You are an analysis bot. Review the conversation transcript between the voice agent and customer.\n"
        "Extract:\n"
        "1. The customer's name (if mentioned/confirmed, otherwise null)\n"
        "2. A brief 2-line summary of the interaction (concise, informative)\n"
        "3. Any customer preferences or custom key/value traits mentioned (as JSON object)\n\n"
        "Return ONLY a raw JSON object with keys: 'name', 'summary', 'preferences'. Do not include markdown code block formatting."
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            temperature=0.3,
            max_tokens=250
        )
        content = response.choices[0].message.content or "{}"
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json"):
                content = "\n".join(lines[1:-1])
            elif lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
        data = json.loads(content)
        return {
            "name": data.get("name"),
            "summary": data.get("summary") or "Call completed.",
            "preferences": data.get("preferences") or {}
        }
    except Exception as e:
        logger.error(f"Failed to generate customer LLM summary: {e}")
        return {"name": None, "summary": "Interaction recorded.", "preferences": {}}

async def upsert_customer(
    db: AsyncSession,
    org_id: int,
    phone_number: str,
    duration_seconds: float,
    transcript: str
):
    """
    Upsert customer profile based on call duration and transcript.
    """
    if not phone_number:
        return
        
    # Query existing profile
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.org_id == org_id,
            CustomerProfile.phone_number == phone_number
        )
    )
    profile = result.scalar_one_or_none()
    
    # Spam guard: only update/create if duration_seconds > 60 or they have call count > 1
    if not profile and duration_seconds < 60:
        logger.info(f"Skipping customer profile creation for {phone_number} (spam guard: duration {duration_seconds:.1f}s < 60s)")
        return
        
    # Analyze transcript
    extraction = await generate_customer_update(transcript)
    
    if profile:
        profile.call_count += 1
        profile.last_call_at = datetime.now(UTC)
        if extraction["name"]:
            profile.name = extraction["name"]
        profile.summary = extraction["summary"]
        prev_prefs = profile.preferences or {}
        profile.preferences = {**prev_prefs, **extraction["preferences"]}
        db.add(profile)
    else:
        profile = CustomerProfile(
            org_id=org_id,
            phone_number=phone_number,
            name=extraction["name"],
            call_count=1,
            summary=extraction["summary"],
            preferences=extraction["preferences"],
            last_call_at=datetime.now(UTC)
        )
        db.add(profile)
        
    await db.commit()
