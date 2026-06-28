from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)  # MinIO or local path
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    org = relationship("Organization")
    agent = relationship("Agent")
    chunks = relationship("KnowledgeBaseChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeBaseChunk(Base):
    __tablename__ = "knowledge_base_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_base_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # 1536 dims for standard OpenAI embeddings
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    document = relationship("KnowledgeBaseDocument", back_populates="chunks")
