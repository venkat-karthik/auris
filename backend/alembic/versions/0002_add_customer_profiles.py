"""Add customer profiles

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-24
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("customer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("last_call_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("org_id", "phone_number", name="uq_org_customer_phone")
    )
    op.create_index("ix_customer_profiles_org_id", "customer_profiles", ["org_id"])
    op.create_index("ix_customer_profiles_phone_number", "customer_profiles", ["phone_number"])

def downgrade() -> None:
    op.drop_table("customer_profiles")
