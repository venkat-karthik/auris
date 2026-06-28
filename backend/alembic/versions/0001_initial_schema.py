"""Initial Auris schema

Revision ID: 0001
Revises:
Create Date: 2026-06-24
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("selected_org_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # organizations
    op.create_table("organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("balance_credits", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("price_per_second_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # FK: users.selected_org_id → organizations.id
    op.create_foreign_key("fk_users_selected_org", "users", "organizations",
                           ["selected_org_id"], ["id"])

    # org_members
    op.create_table("org_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="'member'"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # api_keys
    op.create_table("api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # agents
    op.create_table("agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("graph", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("model_config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("context_variables", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # call_runs
    op.create_table("call_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("transport", sa.String(), nullable=False),
        sa.Column("call_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="'initialized'"),
        sa.Column("caller_number", sa.String(), nullable=True),
        sa.Column("called_number", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("recording_path", sa.String(), nullable=True),
        sa.Column("transcript_path", sa.String(), nullable=True),
        sa.Column("initial_context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("gathered_context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("credits_used", sa.Float(), nullable=True),
        sa.Column("usage_stats", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("disposition", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
    )
    op.create_index("ix_call_runs_org_id", "call_runs", ["org_id"])
    op.create_index("ix_call_runs_agent_id", "call_runs", ["agent_id"])

    # credit_transactions
    op.create_table("credit_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("razorpay_order_id", sa.String(64), nullable=False),
        sa.Column("razorpay_payment_id", sa.String(64), nullable=True),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("credits_added", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="'pending'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_credit_transactions_order_id", "credit_transactions",
                    ["razorpay_order_id"], unique=True)


def downgrade() -> None:
    op.drop_table("credit_transactions")
    op.drop_table("call_runs")
    op.drop_table("agents")
    op.drop_table("api_keys")
    op.drop_table("org_members")
    op.drop_constraint("fk_users_selected_org", "users", type_="foreignkey")
    op.drop_table("organizations")
    op.drop_table("users")
