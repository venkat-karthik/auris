"""Add user verification

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-28
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("verification_code", sa.String(length=6), nullable=True))
    op.add_column("users", sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "verification_expires_at")
    op.drop_column("users", "verification_code")
    op.drop_column("users", "is_verified")
