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

    # In production, we'd dispatch to elevenlabs client:
    # client.clone_voice(name, file_content)
    # For now, we mock the generated ElevenLabs voice ID
    mock_voice_id = f"voice_id_{uuid.uuid4().hex[:12]}"

    voice = ClonedVoice(
        org_id=org.id,
        name=name,
        voice_id=mock_voice_id,
        status="ready"
    )
    db.add(voice)
    await db.commit()
    await db.refresh(voice)

    return voice
