"""Add post call analysis columns and org invites

Revision ID: a1b2c3d4e5f6
Revises: 9dc82aa3e514
Create Date: 2026-06-30 18:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9dc82aa3e514'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── CallRun Additions ───────────────────────────────────────────────────────
    op.add_column('call_runs', sa.Column('summary', sa.String(), nullable=True))
    op.add_column('call_runs', sa.Column('sentiment', sa.String(), nullable=True))
    op.add_column('call_runs', sa.Column('key_topics', sa.JSON(), nullable=True))
    op.add_column('call_runs', sa.Column('task_completed', sa.Boolean(), nullable=True))
    op.add_column('call_runs', sa.Column('telephony_id', sa.String(), nullable=True))

    # ── OrgInvite Creation ──────────────────────────────────────────────────────
    op.create_table('org_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='member'),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_org_invites_id'), 'org_invites', ['id'], unique=False)
    op.create_index(op.f('ix_org_invites_token'), 'org_invites', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_org_invites_token'), table_name='org_invites')
    op.drop_index(op.f('ix_org_invites_id'), table_name='org_invites')
    op.drop_table('org_invites')

    op.drop_column('call_runs', 'telephony_id')
    op.drop_column('call_runs', 'task_completed')
    op.drop_column('call_runs', 'key_topics')
    op.drop_column('call_runs', 'sentiment')
    op.drop_column('call_runs', 'summary')
