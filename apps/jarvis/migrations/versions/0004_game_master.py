"""Canonical Game Master campaigns, visibility, rolls and events."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("game_system", sa.String(80), nullable=False),
        sa.Column("rules_plugin", sa.String(80), nullable=False),
        sa.Column("roll_policy", sa.String(80), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="ck_campaign_status"),
    )
    op.create_index("ix_campaigns_owner_id", "campaigns", ["owner_id"])
    op.create_table(
        "campaign_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_id", "actor_id"),
        sa.CheckConstraint("role IN ('GM','PLAYER')", name="ck_campaign_member_role"),
    )
    op.create_index("ix_campaign_members_campaign_id", "campaign_members", ["campaign_id"])
    op.create_index("ix_campaign_members_actor_id", "campaign_members", ["actor_id"])
    op.create_table(
        "campaign_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("data_json", sa.JSON, nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("player_actor_id", sa.String(36), nullable=True),
        sa.Column("source_proposal_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('LOCATION','PC','NPC','LORE','FACTION','ITEM','HOOK','STATE')",
            name="ck_campaign_entry_kind",
        ),
        sa.CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET',"
            "'INFERRED','RUMOR','RETIRED')",
            name="ck_campaign_entry_visibility",
        ),
    )
    for column in ["campaign_id", "player_actor_id"]:
        op.create_index(f"ix_campaign_entries_{column}", "campaign_entries", [column])
    op.create_index(
        "ix_campaign_entry_visibility",
        "campaign_entries",
        ["campaign_id", "visibility", "created_at"],
    )
    op.create_table(
        "campaign_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("active_location_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('PLANNED','ACTIVE','CLOSED')", name="ck_campaign_session_status"
        ),
    )
    op.create_index("ix_campaign_sessions_campaign_id", "campaign_sessions", ["campaign_id"])
    op.create_table(
        "campaign_transcripts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("campaign_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("speaker", sa.String(120), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("player_actor_id", sa.String(36), nullable=True),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET')",
            name="ck_campaign_transcript_visibility",
        ),
        sa.CheckConstraint("origin = 'HUMAN_API'", name="ck_campaign_transcript_origin"),
    )
    for column in ["campaign_id", "session_id", "actor_id"]:
        op.create_index(f"ix_campaign_transcripts_{column}", "campaign_transcripts", [column])
    op.create_index(
        "ix_campaign_transcript_scope",
        "campaign_transcripts",
        ["campaign_id", "session_id", "created_at"],
    )
    op.create_table(
        "roll_delegations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column(
            "subject_entry_id",
            sa.String(36),
            sa.ForeignKey("campaign_entries.id"),
            nullable=False,
        ),
        sa.Column("nonce", sa.String(80), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("max_uses", sa.Integer, nullable=False),
        sa.Column("uses", sa.Integer, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_id", "actor_id", "nonce"),
        sa.CheckConstraint(
            "status IN ('ACTIVE','CONSUMED','REVOKED')", name="ck_roll_delegation_status"
        ),
        sa.CheckConstraint("uses <= max_uses", name="ck_roll_delegation_uses"),
    )
    for column in ["campaign_id", "actor_id", "subject_entry_id", "expires_at"]:
        op.create_index(f"ix_roll_delegations_{column}", "roll_delegations", [column])
    op.create_table(
        "dice_rolls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("requested_by", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
        sa.Column(
            "subject_entry_id",
            sa.String(36),
            sa.ForeignKey("campaign_entries.id"),
            nullable=False,
        ),
        sa.Column("expression", sa.String(32), nullable=False),
        sa.Column("purpose", sa.String(200), nullable=False),
        sa.Column("authority", sa.String(24), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rolls", sa.JSON, nullable=False),
        sa.Column("kept", sa.JSON, nullable=False),
        sa.Column("discarded", sa.JSON, nullable=False),
        sa.Column("modifier", sa.Integer, nullable=False),
        sa.Column("total", sa.Integer, nullable=True),
        sa.Column("provenance", sa.String(32), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("entropy_ref", sa.String(64), nullable=False),
        sa.Column("delegation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("campaign_id", "requested_by", "request_id"),
        sa.CheckConstraint("status IN ('AWAITING_HUMAN','ROLLED')", name="ck_dice_roll_status"),
        sa.CheckConstraint(
            "authority IN ('HUMAN','JARVIS_NPC','JARVIS_DELEGATED')",
            name="ck_dice_roll_authority",
        ),
        sa.CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET','INFERRED','RUMOR')",
            name="ck_dice_roll_visibility",
        ),
    )
    for column in ["campaign_id", "session_id", "requested_by", "subject_entry_id"]:
        op.create_index(f"ix_dice_rolls_{column}", "dice_rolls", [column])
    op.create_table(
        "campaign_event_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("proposed_by", sa.String(36), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("changes", sa.JSON, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING','APPROVED','REJECTED')", name="ck_campaign_proposal_status"
        ),
        sa.CheckConstraint(
            "origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_campaign_proposal_origin"
        ),
    )
    for column in ["campaign_id", "session_id", "proposed_by"]:
        op.create_index(
            f"ix_campaign_event_proposals_{column}", "campaign_event_proposals", [column]
        )
    op.create_table(
        "campaign_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column(
            "proposal_id",
            sa.String(36),
            sa.ForeignKey("campaign_event_proposals.id"),
            nullable=False,
        ),
        sa.Column("approved_by", sa.String(36), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("applied_changes", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("proposal_id"),
    )
    for column in ["campaign_id", "session_id", "proposal_id"]:
        op.create_index(f"ix_campaign_events_{column}", "campaign_events", [column])


def downgrade():
    op.drop_table("campaign_events")
    op.drop_table("campaign_event_proposals")
    op.drop_table("dice_rolls")
    op.drop_table("roll_delegations")
    op.drop_table("campaign_transcripts")
    op.drop_table("campaign_sessions")
    op.drop_table("campaign_entries")
    op.drop_table("campaign_members")
    op.drop_table("campaigns")
