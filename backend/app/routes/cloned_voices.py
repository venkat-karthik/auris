import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org
from app.models.organization import Organization
from app.models.cloned_voice import ClonedVoice

router = APIRouter(prefix="/cloned-voices", tags=["Cloned Voices"])


class ClonedVoiceResponse(BaseModel):
    id: int
    name: str = ""
    voice_id: str
    status: str
    created_at: datetime


@router.get("", response_model=List[ClonedVoiceResponse])
async def list_cloned_voices(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Retrieve all active cloned voices trained for this organization."""
    query = select(ClonedVoice).where(ClonedVoice.org_id == org.id)
    result = await db.execute(query)
    items = result.scalars().all()
    return items


@router.post("/upload", response_model=ClonedVoiceResponse)
async def upload_voice_sample(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org)
):
    """Upload a microphone recording or audio file to clone a custom voice."""
    # Read audio bytes for validation
    audio_content = await file.read()
    if len(audio_content) < 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice sample too short. Please provide clear speech audio."
        )

    import httpx
    from app.core.config import ELEVENLABS_API_KEY

    if ELEVENLABS_API_KEY and not ELEVENLABS_API_KEY.startswith("mock"):
        try:
            files = {"files": (file.filename, audio_content, file.content_type)}
            data = {"name": name}
            headers = {"xi-api-key": ELEVENLABS_API_KEY}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.elevenlabs.io/v1/voices/add",
                    headers=headers,
                    files=files,
                    data=data
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"ElevenLabs API error: {resp.status_code} - {resp.text}"
                    )
                voice_id = resp.json()["voice_id"]
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with ElevenLabs: {str(e)}"
            )
    else:
        import uuid
        voice_id = f"voice_id_{uuid.uuid4().hex[:12]}"

    voice = ClonedVoice(
        org_id=org.id,
        name=name,
        voice_id=voice_id,
        status="ready"
    )
    db.add(voice)
    await db.commit()
    await db.refresh(voice)

    return voice
