"""Add HNSW index on knowledge_base_chunks.embedding

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-12 12:05:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add HNSW index on knowledge_base_chunks.embedding using cosine distance
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_base_chunks_embedding_hnsw "
        "ON knowledge_base_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_base_chunks_embedding_hnsw;")
