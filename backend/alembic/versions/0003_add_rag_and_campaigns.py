"""Add RAG and campaigns tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-28
"""
from typing import Union
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ensure pgvector extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create knowledge_base_documents table
    op.create_table(
        "knowledge_base_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_knowledge_base_documents_org_id", "knowledge_base_documents", ["org_id"])
    op.create_index("ix_knowledge_base_documents_agent_id", "knowledge_base_documents", ["agent_id"])

    # 3. Create knowledge_base_chunks table
    op.create_table(
        "knowledge_base_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_base_documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_base_chunks_document_id", "knowledge_base_chunks", ["document_id"])

    # 4. Create campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_campaigns_org_id", "campaigns", ["org_id"])
    op.create_index("ix_campaigns_agent_id", "campaigns", ["agent_id"])

    # 5. Create campaign_contacts table
    op.create_table(
        "campaign_contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("call_run_id", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["call_run_id"], ["call_runs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_campaign_contacts_campaign_id", "campaign_contacts", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("campaign_contacts")
    op.drop_table("campaigns")
    op.drop_table("knowledge_base_chunks")
    op.drop_table("knowledge_base_documents")
