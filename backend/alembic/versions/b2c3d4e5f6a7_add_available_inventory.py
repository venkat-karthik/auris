"""Add available inventory table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-12 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'available_inventory',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('phone_number', sa.String(length=32), nullable=False),
        sa.Column('region', sa.String(length=64), nullable=True),
        sa.Column('is_leased', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('monthly_cost_usd', sa.Float(), nullable=False, server_default='2.0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_available_inventory_id'), 'available_inventory', ['id'], unique=False)
    op.create_index(op.f('ix_available_inventory_phone_number'), 'available_inventory', ['phone_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_available_inventory_phone_number'), table_name='available_inventory')
    op.drop_index(op.f('ix_available_inventory_id'), table_name='available_inventory')
    op.drop_table('available_inventory')
