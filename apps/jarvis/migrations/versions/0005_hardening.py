"""Durable provider admission ledger and remote voice cleanup identifiers."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "provider_budget_days",
        sa.Column("day", sa.String(10), primary_key=True),
        sa.Column("charged_microusd", sa.Integer(), nullable=False),
    )
    op.create_table(
        "provider_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("day", sa.String(10), sa.ForeignKey("provider_budget_days.day"), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("reserved_microusd", sa.Integer(), nullable=False),
        sa.Column("charged_microusd", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("usage", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name in ["day", "actor_id"]:
        op.create_index(f"ix_provider_calls_{name}", "provider_calls", [name])
    op.create_table(
        "voice_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("provider_id", sa.String(128), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_voice_sessions_actor_id", "voice_sessions", ["actor_id"])


def downgrade():
    op.drop_table("voice_sessions")
    op.drop_table("provider_calls")
    op.drop_table("provider_budget_days")
