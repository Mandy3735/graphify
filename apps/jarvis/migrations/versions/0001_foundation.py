"""Immutable foundation schema, not generated from future model metadata."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("request", sa.JSON, nullable=False),
        sa.Column("messages", sa.JSON, nullable=False),
        sa.Column("pending", sa.JSON, nullable=True),
        sa.Column("result", sa.Text, nullable=False),
        sa.Column("error", sa.String(160), nullable=False),
        sa.Column("metadata_json", sa.JSON, nullable=False),
        sa.Column("tool_count", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "agent_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("summary", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("operation", sa.JSON, nullable=False),
        sa.Column("operation_hash", sa.String(64), nullable=False),
        sa.Column("nonce", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "nonce"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("event", sa.String(80), nullable=False),
        sa.Column("details", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table, columns in {
        "agent_runs": ["actor_id"],
        "agent_steps": ["run_id"],
        "approvals": ["run_id", "actor_id"],
        "audit_events": ["actor_id", "run_id"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION jarvis_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'JARVIS audit history is append-only'; END; $$;
        """)
        op.execute("""
            CREATE TRIGGER jarvis_audit_guard BEFORE UPDATE OR DELETE OR TRUNCATE
            ON audit_events FOR EACH STATEMENT EXECUTE FUNCTION jarvis_audit_immutable();
        """)


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("approvals")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION jarvis_audit_immutable()")
