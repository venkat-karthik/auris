import asyncio
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db, AsyncSessionLocal
from app.dependencies.auth import get_current_org, get_current_user
from app.models.organization import Organization
from app.models.knowledge_base import KnowledgeBaseDocument
from app.services.rag_service import ingest_document
from app.tasks.worker import upload_file_to_minio
from app.core.config import MINIO_BUCKET

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


class DocumentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    file_path: str
    agent_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    description: str | None = Form(None),
    agent_id: int | None = Form(None),
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document (PDF or TXT) to the knowledge base.
    Ingestion (chunking and embedding) is triggered as a background task.
    """
    file_name = file.filename
    if not file_name or not (file_name.endswith(".txt") or file_name.endswith(".pdf") or file_name.endswith(".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .txt, .pdf, and .docx files are supported."
        )

    file_data = await file.read()
    
    # 1. Save document to storage (MinIO or local fallback)
    try:
        storage_path = f"knowledge_base/{org.id}/{datetime.now().timestamp()}_{file_name}"
        stored_path = upload_file_to_minio(
            MINIO_BUCKET,
            storage_path,
            file_data,
            file.content_type or "text/plain"
        )
    except Exception as e:
        logger.error(f"Failed to upload document file to storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist document to object store"
        )

    # 2. Store document in Database
    doc = KnowledgeBaseDocument(
        org_id=org.id,
        agent_id=agent_id,
        name=file_name,
        description=description,
        file_path=stored_path
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    doc_id = doc.id

    # 3. Fire and forget ingestion processing in a background task
    async def process_ingestion_async():
        async with AsyncSessionLocal() as session:
            try:
                await ingest_document(session, doc_id, file_data, file_name)
                logger.info(f"Ingested document={doc_id} successfully")
            except Exception as ex:
                logger.error(f"Async ingestion failed for document={doc_id}: {ex}")

    asyncio.create_task(process_ingestion_async())

    return doc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all knowledge base documents for the organization."""
    result = await db.execute(
        select(KnowledgeBaseDocument)
        .where(KnowledgeBaseDocument.org_id == org.id)
        .order_by(KnowledgeBaseDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return docs


@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    doc_id: int,
    org: Organization = Depends(get_current_org),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and its associated chunks from the knowledge base."""
    result = await db.execute(
        select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.id == doc_id,
            KnowledgeBaseDocument.org_id == org.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()
    return {"message": "Document and chunks successfully deleted", "id": doc_id}
