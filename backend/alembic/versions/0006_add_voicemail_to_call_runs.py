"""Add voicemail to call runs

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-28
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("call_runs", sa.Column("voicemail", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("call_runs", "voicemail")
