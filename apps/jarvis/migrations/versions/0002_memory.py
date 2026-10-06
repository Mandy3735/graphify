"""Personal memory is independent of code graphs and run transcripts."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "memory_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("lineage_id", sa.String(36), nullable=False),
        sa.Column("memory_class", sa.String(16), nullable=False),
        sa.Column("namespace", sa.String(100), nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("mode", sa.String(32), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("structured_data", sa.JSON, nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("supersedes_id", sa.String(36), nullable=True),
        sa.Column("superseded_by", sa.String(36), nullable=True),
        sa.Column("embedding_json", sa.JSON, nullable=False),
        sa.Column("embedding_key", sa.String(200), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision >= 1 AND revision <= 32", name="ck_memory_revision"),
        sa.CheckConstraint(
            "memory_class IN ('WORKING','EPISODIC','SEMANTIC','CANONICAL','PREFERENCE')",
            name="ck_memory_class",
        ),
        sa.CheckConstraint(
            "visibility IN ('PRIVATE','PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET',"
            "'INFERRED','RUMOR','RETIRED')",
            name="ck_memory_visibility",
        ),
    )
    op.create_index(
        "ix_memory_scope", "memory_items", ["owner_id", "namespace", "visibility", "created_at"]
    )
    op.create_index("ix_memory_lineage", "memory_items", ["owner_id", "lineage_id"])
    op.create_table(
        "memory_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "memory_id",
            sa.String(36),
            sa.ForeignKey("memory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("locator", sa.String(300), nullable=False),
        sa.Column("quote", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_sources_memory_id", "memory_sources", ["memory_id"])
    op.create_table(
        "memory_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("memory_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_proposals_owner_id", "memory_proposals", ["owner_id"])


def downgrade():
    op.drop_table("memory_proposals")
    op.drop_table("memory_sources")
    op.drop_table("memory_items")
