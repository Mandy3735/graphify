from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(UTC)


def identifier() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    state: Mapped[str] = mapped_column(String(32), default="RECEIVED")
    mode: Mapped[str] = mapped_column(String(32))
    request: Mapped[dict[str, Any]] = mapped_column(JSON)
    messages: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    pending: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(String(160), default="")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tool_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentStep(Base):
    __tablename__ = "agent_steps"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    state: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ApprovalRequest(Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("run_id", "nonce"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    operation: Mapped[dict[str, Any]] = mapped_column(JSON)
    operation_hash: Mapped[str] = mapped_column(String(64))
    nonce: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MemoryItem(Base):
    __tablename__ = "memory_items"
    __table_args__ = (
        Index("ix_memory_scope", "owner_id", "namespace", "visibility", "created_at"),
        Index("ix_memory_lineage", "owner_id", "lineage_id"),
        CheckConstraint("revision >= 1 AND revision <= 32", name="ck_memory_revision"),
        CheckConstraint(
            "memory_class IN ('WORKING','EPISODIC','SEMANTIC','CANONICAL','PREFERENCE')",
            name="ck_memory_class",
        ),
        CheckConstraint(
            "visibility IN ('PRIVATE','PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET',"
            "'INFERRED','RUMOR','RETIRED')",
            name="ck_memory_visibility",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    owner_id: Mapped[str] = mapped_column(String(36))
    lineage_id: Mapped[str] = mapped_column(String(36))
    memory_class: Mapped[str] = mapped_column(String(16))
    namespace: Mapped[str] = mapped_column(String(100))
    visibility: Mapped[str] = mapped_column(String(16))
    mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    structured_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    revision: Mapped[int] = mapped_column(default=1)
    supersedes_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    embedding_json: Mapped[list[float]] = mapped_column(JSON, default=list)
    embedding_key: Mapped[str] = mapped_column(String(200), default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MemorySource(Base):
    __tablename__ = "memory_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    memory_id: Mapped[str] = mapped_column(
        ForeignKey("memory_items.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(24))
    locator: Mapped[str] = mapped_column(String(300))
    quote: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MemoryProposal(Base):
    __tablename__ = "memory_proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    memory_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LearningObjective(Base):
    __tablename__ = "learning_objectives"
    __table_args__ = (
        Index("ix_learning_objective_owner_status", "owner_id", "status", "updated_at"),
        CheckConstraint(
            "status IN ('ACTIVE','MASTERED','ARCHIVED')", name="ck_learning_objective_status"
        ),
        CheckConstraint(
            "mastery_required_quizzes >= 1 AND mastery_required_quizzes <= 10",
            name="ck_learning_objective_required_quizzes",
        ),
        CheckConstraint(
            "mastery_min_score >= 50 AND mastery_min_score <= 100",
            name="ck_learning_objective_min_score",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    mastery_required_quizzes: Mapped[int] = mapped_column(Integer, default=2)
    mastery_min_score: Mapped[int] = mapped_column(Integer, default=80)
    mastery_evidence_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LearningSource(Base):
    __tablename__ = "learning_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    objective_id: Mapped[str] = mapped_column(
        ForeignKey("learning_objectives.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(24))
    locator: Mapped[str] = mapped_column(String(300))
    quote: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TutorLesson(Base):
    __tablename__ = "tutor_lessons"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('EXPLANATION','WORKED_EXAMPLE','SOCRATIC')", name="ck_tutor_lesson_kind"
        ),
        CheckConstraint("origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_tutor_lesson_origin"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    objective_id: Mapped[str] = mapped_column(
        ForeignKey("learning_objectives.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    source_ids: Mapped[list[str]] = mapped_column(JSON)
    origin: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TutorQuiz(Base):
    __tablename__ = "tutor_quizzes"
    __table_args__ = (
        CheckConstraint("origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_tutor_quiz_origin"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    objective_id: Mapped[str] = mapped_column(
        ForeignKey("learning_objectives.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    answer_hashes: Mapped[list[str]] = mapped_column(JSON)
    source_ids: Mapped[list[str]] = mapped_column(JSON)
    origin: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TutorAttempt(Base):
    __tablename__ = "tutor_attempts"
    __table_args__ = (
        UniqueConstraint("owner_id", "quiz_id", "submission_id"),
        CheckConstraint("origin = 'HUMAN_API'", name="ck_tutor_attempt_origin"),
        CheckConstraint("score IN (0,100)", name="ck_tutor_attempt_score"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("tutor_quizzes.id"), index=True)
    objective_id: Mapped[str] = mapped_column(ForeignKey("learning_objectives.id"), index=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    submission_id: Mapped[str] = mapped_column(String(80))
    answer_hash: Mapped[str] = mapped_column(String(64))
    correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[int] = mapped_column(Integer)
    evaluator: Mapped[str] = mapped_column(String(32), default="DETERMINISTIC_V1")
    origin: Mapped[str] = mapped_column(String(16), default="HUMAN_API")
    attempt_number: Mapped[int] = mapped_column(Integer)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MasteryEvidence(Base):
    __tablename__ = "mastery_evidence"
    __table_args__ = (UniqueConstraint("objective_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    objective_id: Mapped[str] = mapped_column(ForeignKey("learning_objectives.id"), index=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    attempt_ids: Mapped[list[str]] = mapped_column(JSON)
    distinct_quizzes: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)
    evaluator: Mapped[str] = mapped_column(String(32), default="DETERMINISTIC_V1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ReviewTask(Base):
    __tablename__ = "review_tasks"
    __table_args__ = (
        UniqueConstraint("objective_id", "sequence"),
        CheckConstraint("status IN ('SCHEDULED','COMPLETED')", name="ck_review_task_status"),
        CheckConstraint("sequence >= 1", name="ck_review_task_sequence"),
        CheckConstraint("interval_days >= 1", name="ck_review_task_interval"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    objective_id: Mapped[str] = mapped_column(ForeignKey("learning_objectives.id"), index=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    interval_days: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(16), default="SCHEDULED")
    evidence_attempt_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="ck_campaign_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200))
    game_system: Mapped[str] = mapped_column(String(80))
    rules_plugin: Mapped[str] = mapped_column(String(80), default="basic")
    roll_policy: Mapped[str] = mapped_column(String(80), default="personal_play")
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignMember(Base):
    __tablename__ = "campaign_members"
    __table_args__ = (
        UniqueConstraint("campaign_id", "actor_id"),
        CheckConstraint("role IN ('GM','PLAYER')", name="ck_campaign_member_role"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignEntry(Base):
    __tablename__ = "campaign_entries"
    __table_args__ = (
        Index("ix_campaign_entry_visibility", "campaign_id", "visibility", "created_at"),
        CheckConstraint(
            "kind IN ('LOCATION','PC','NPC','LORE','FACTION','ITEM','HOOK','STATE')",
            name="ck_campaign_entry_kind",
        ),
        CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET',"
            "'INFERRED','RUMOR','RETIRED')",
            name="ck_campaign_entry_visibility",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[str] = mapped_column(String(36))
    kind: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    data_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    visibility: Mapped[str] = mapped_column(String(20))
    player_actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    source_proposal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignSession(Base):
    __tablename__ = "campaign_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PLANNED','ACTIVE','CLOSED')", name="ck_campaign_session_status"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[str] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    active_location_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignTranscript(Base):
    __tablename__ = "campaign_transcripts"
    __table_args__ = (
        Index("ix_campaign_transcript_scope", "campaign_id", "session_id", "created_at"),
        CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET')",
            name="ck_campaign_transcript_visibility",
        ),
        CheckConstraint("origin = 'HUMAN_API'", name="ck_campaign_transcript_origin"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("campaign_sessions.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    speaker: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(20))
    player_actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="HUMAN_API")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RollDelegation(Base):
    __tablename__ = "roll_delegations"
    __table_args__ = (
        UniqueConstraint("campaign_id", "actor_id", "nonce"),
        CheckConstraint(
            "status IN ('ACTIVE','CONSUMED','REVOKED')", name="ck_roll_delegation_status"
        ),
        CheckConstraint("uses <= max_uses", name="ck_roll_delegation_uses"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    subject_entry_id: Mapped[str] = mapped_column(ForeignKey("campaign_entries.id"), index=True)
    nonce: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DiceRoll(Base):
    __tablename__ = "dice_rolls"
    __table_args__ = (
        UniqueConstraint("campaign_id", "requested_by", "request_id"),
        CheckConstraint("status IN ('AWAITING_HUMAN','ROLLED')", name="ck_dice_roll_status"),
        CheckConstraint(
            "authority IN ('HUMAN','JARVIS_NPC','JARVIS_DELEGATED')",
            name="ck_dice_roll_authority",
        ),
        CheckConstraint(
            "visibility IN ('PUBLIC','PARTY','PLAYER_PRIVATE','GM_SECRET','INFERRED','RUMOR')",
            name="ck_dice_roll_visibility",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    requested_by: Mapped[str] = mapped_column(String(36), index=True)
    request_id: Mapped[str] = mapped_column(String(80))
    subject_entry_id: Mapped[str] = mapped_column(ForeignKey("campaign_entries.id"), index=True)
    expression: Mapped[str] = mapped_column(String(32))
    purpose: Mapped[str] = mapped_column(String(200))
    authority: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(20))
    rolls: Mapped[list[int]] = mapped_column(JSON, default=list)
    kept: Mapped[list[int]] = mapped_column(JSON, default=list)
    discarded: Mapped[list[int]] = mapped_column(JSON, default=list)
    modifier: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance: Mapped[str] = mapped_column(String(32))
    visibility: Mapped[str] = mapped_column(String(20))
    entropy_ref: Mapped[str] = mapped_column(String(64), default="")
    delegation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignEventProposal(Base):
    __tablename__ = "campaign_event_proposals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','APPROVED','REJECTED')",
            name="ck_campaign_proposal_status",
        ),
        CheckConstraint("origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_campaign_proposal_origin"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    proposed_by: Mapped[str] = mapped_column(String(36), index=True)
    summary: Mapped[str] = mapped_column(String(500))
    changes: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    origin: Mapped[str] = mapped_column(String(16))
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignEvent(Base):
    __tablename__ = "campaign_events"
    __table_args__ = (UniqueConstraint("proposal_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("campaign_event_proposals.id"), index=True)
    approved_by: Mapped[str] = mapped_column(String(36))
    summary: Mapped[str] = mapped_column(String(500))
    applied_changes: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, pool_pre_ping=True)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def dispose(self) -> None:
        await self.engine.dispose()


def audit(
    session: AsyncSession,
    actor_id: str,
    event: str,
    details: dict[str, Any],
    run_id: str | None = None,
) -> None:
    session.add(AuditEvent(actor_id=actor_id, run_id=run_id, event=event, details=details))
