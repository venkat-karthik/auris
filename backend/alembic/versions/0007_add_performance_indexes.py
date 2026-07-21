"""Add performance indexes for high-traffic queries

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-21

Composite indexes to optimize:
- Call listing by org, status, date (frequent filter combo in analytics)
- Campaign contacts by campaign and status (bulk status updates)
- Agents by org (list_agents endpoint)
"""
from typing import Union
from sqlalchemy import text
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index for call_runs: org_id + status + created_at (analytics queries)
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_call_runs_org_status_date 
            ON call_runs (org_id, status, created_at DESC);
            """
        )
    )
    
    # Index for agents: org_id (list agents endpoint)
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_agents_org_id 
            ON agents (org_id, is_active);
            """
        )
    )
    
    # Index for call_runs: agent_id (get calls by agent)
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_call_runs_agent_id 
            ON call_runs (agent_id, status);
            """
        )
    )


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS ix_call_runs_org_status_date;"))
    op.execute(text("DROP INDEX IF EXISTS ix_agents_org_id;"))
    op.execute(text("DROP INDEX IF EXISTS ix_call_runs_agent_id;"))

