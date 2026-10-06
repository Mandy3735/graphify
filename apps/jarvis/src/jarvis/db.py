from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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
