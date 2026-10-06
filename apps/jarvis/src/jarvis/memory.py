"""Owner and visibility predicates are applied in SQL before reading any content."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, timedelta
from typing import Any

from sqlalchemy import String, bindparam, delete, literal_column, or_, select, text, update
from sqlalchemy.exc import DBAPIError

from jarvis.config import Settings
from jarvis.db import Database, MemoryItem, MemoryProposal, MemorySource, audit, identifier, now
from jarvis.domain import ChatRequest, Mode
from jarvis.embeddings import EmbeddingProvider, checked_vector, terms
from jarvis.memory_schema import (
    EDITABLE,
    MemoryClass,
    MemoryCorrection,
    MemoryCreate,
    SourceInput,
    SourceKind,
    Visibility,
)
from jarvis.policy import Actor


class MemoryDenied(PermissionError):
    pass


class MemoryConflict(ValueError):
    pass


@dataclass(frozen=True)
class MemoryScope:
    actor: Actor
    mode: Mode
    namespaces: tuple[str, ...] = ("personal",)

    @property
    def gm_allowed(self) -> bool:
        return self.mode == Mode.GAME_MASTER and "memory.gm_secret" in self.actor.capabilities

    def require(self, capability: str) -> None:
        if capability not in self.actor.capabilities:
            raise MemoryDenied("Memory capability denied")


def request_scope(actor: Actor, request: ChatRequest) -> MemoryScope:
    namespaces = ["personal"]
    for kind, value in [
        ("project", request.project_id),
        ("campaign", request.campaign_id),
        ("session", request.session_id),
    ]:
        if value:
            namespaces.append(f"{kind}:{value}")
    return MemoryScope(actor, request.mode, tuple(namespaces))


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class MemoryService:
    def __init__(self, db: Database, settings: Settings, embeddings: EmbeddingProvider):
        self.db, self.settings, self.embeddings = db, settings, embeddings

    async def check_backend(self) -> None:
        # Refuse a healthy-looking startup against the older foundation-only schema.
        try:
            async with self.db.sessions() as session:
                for table in (MemoryItem, MemorySource, MemoryProposal):
                    await session.execute(select(table.id).limit(0))
        except DBAPIError:
            raise MemoryConflict("Apply JARVIS memory migration 0002 before startup") from None
        if not self.settings.memory_pgvector:
            return
        if self.db.engine.dialect.name != "postgresql":
            raise MemoryConflict("pgvector requires PostgreSQL")
        async with self.db.sessions() as session:
            exists = await session.scalar(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")
            )
        if not exists:
            raise MemoryConflict("pgvector is enabled but its extension is not installed")

    def predicates(self, scope: MemoryScope, *, active: bool = True):
        permitted = [v.value for v in Visibility if scope.gm_allowed or v != Visibility.GM_SECRET]
        filters = [
            MemoryItem.owner_id == scope.actor.id,
            MemoryItem.namespace.in_(scope.namespaces),
            MemoryItem.visibility.in_(permitted),
            or_(MemoryItem.mode.is_(None), MemoryItem.mode == scope.mode.value),
        ]
        if active:
            filters.extend(
                [
                    MemoryItem.deleted_at.is_(None),
                    MemoryItem.superseded_by.is_(None),
                    MemoryItem.visibility != Visibility.RETIRED.value,
                    or_(MemoryItem.expires_at.is_(None), MemoryItem.expires_at > now()),
                ]
            )
        return filters

    async def _item(self, session, scope: MemoryScope, item_id: str, *, active=False):
        item = await session.scalar(
            select(MemoryItem).where(
                MemoryItem.id == item_id, *self.predicates(scope, active=active)
            )
        )
        if item is None:
            raise KeyError("Memory not found")
        return item

    async def _views(self, session, items: list[MemoryItem]) -> list[dict[str, Any]]:
        if not items:
            return []
        sources = (
            await session.scalars(
                select(MemorySource)
                .where(MemorySource.memory_id.in_([m.id for m in items]))
                .order_by(MemorySource.recorded_at, MemorySource.id)
            )
        ).all()
        grouped: dict[str, list] = {}
        for source in sources:
            grouped.setdefault(source.memory_id, []).append(
                {
                    "id": source.id,
                    "kind": source.kind,
                    "locator": source.locator,
                    "quote": source.quote,
                    "content_hash": source.content_hash,
                    "recorded_at": utc(source.recorded_at).isoformat(),
                    "trust": "UNTRUSTED_SOURCE_ASSERTION",
                }
            )
        output = []
        for item in items:
            eligible = item.memory_class in EDITABLE and item.deleted_at is None
            active = (
                item.deleted_at is None
                and item.superseded_by is None
                and item.visibility != Visibility.RETIRED
                and (item.expires_at is None or utc(item.expires_at) > now())
            )
            output.append(
                {
                    "id": item.id,
                    "memory_class": item.memory_class,
                    "namespace": item.namespace,
                    "visibility": item.visibility,
                    "mode": item.mode,
                    "content": item.content,
                    "structured_data": item.structured_data,
                    "sources": grouped.get(item.id, []),
                    "lineage_id": item.lineage_id,
                    "revision": item.revision,
                    "supersedes_id": item.supersedes_id,
                    "superseded_by": item.superseded_by,
                    "active": active,
                    "editable": eligible and active and item.revision < 32,
                    "deletable": eligible,
                    "expires_at": utc(item.expires_at).isoformat() if item.expires_at else None,
                    "deleted_at": utc(item.deleted_at).isoformat() if item.deleted_at else None,
                    "created_at": utc(item.created_at).isoformat(),
                    "trust": "UNTRUSTED_DATA",
                }
            )
        return output

    async def inspect(self, scope: MemoryScope, item_id: str) -> dict:
        scope.require("memory.read")
        async with self.db.sessions() as session:
            return (await self._views(session, [await self._item(session, scope, item_id)]))[0]

    async def list_items(
        self, scope: MemoryScope, *, limit=50, after: str = "", include_history=False
    ) -> dict:
        scope.require("memory.read")
        limit = max(1, min(limit, 100))
        async with self.db.sessions() as session:
            items = list(
                await session.scalars(
                    select(MemoryItem)
                    .where(
                        *self.predicates(scope, active=not include_history), MemoryItem.id > after
                    )
                    .order_by(MemoryItem.id)
                    .limit(limit + 1)
                )
            )
            return {
                "items": await self._views(session, items[:limit]),
                "next_cursor": items[limit - 1].id if len(items) > limit else None,
            }

    def _authorize_write(self, scope: MemoryScope, body: MemoryCreate) -> None:
        scope.require("memory.write")
        if body.namespace not in scope.namespaces:
            raise MemoryDenied("Memory namespace denied")
        if body.visibility == Visibility.GM_SECRET and not scope.gm_allowed:
            raise MemoryDenied("GM secret capability and mode required")
        if body.memory_class == MemoryClass.CANONICAL:
            scope.require("memory.canonical_write")
        if body.expires_at is not None and utc(body.expires_at) <= now():
            raise MemoryConflict("New memory must not already be expired")

    async def _insert(
        self,
        session,
        scope: MemoryScope,
        body: MemoryCreate,
        *,
        lineage=None,
        revision=1,
        supersedes=None,
        expires=None,
    ) -> MemoryItem:
        self._authorize_write(scope, body)
        item_id = identifier()
        expiry = expires or body.expires_at
        if body.memory_class == MemoryClass.WORKING:
            maximum = now() + timedelta(seconds=self.settings.working_memory_ttl)
            expiry = min(utc(expiry), maximum) if expiry else maximum
        item = MemoryItem(
            id=item_id,
            owner_id=scope.actor.id,
            lineage_id=lineage or item_id,
            memory_class=body.memory_class.value,
            namespace=body.namespace,
            visibility=body.visibility.value,
            mode=body.mode.value if body.mode else None,
            content=body.content,
            structured_data=body.structured_data,
            revision=revision,
            supersedes_id=supersedes,
            expires_at=expiry,
            embedding_json=checked_vector(
                await self.embeddings.embed(body.content + " " + json.dumps(body.structured_data)),
                self.embeddings.dimensions,
            ),
            embedding_key=self.embeddings.key,
        )
        session.add(item)
        await session.flush()
        for source in body.sources:
            session.add(
                MemorySource(
                    memory_id=item.id,
                    kind=source.kind.value,
                    locator=source.locator,
                    quote=source.quote,
                    content_hash=hashlib.sha256(
                        (source.quote or body.content).encode()
                    ).hexdigest(),
                )
            )
        audit(
            session, scope.actor.id, "memory.created", {"id": item.id, "class": item.memory_class}
        )
        await session.flush()
        return item

    async def create(self, scope: MemoryScope, body: MemoryCreate) -> dict:
        async with self.db.sessions.begin() as session:
            return (await self._views(session, [await self._insert(session, scope, body)]))[0]

    async def _lock_lineage(self, session, scope, item):
        # All lineage mutations take the same root lock before inspecting current state.
        await session.scalar(
            select(MemoryItem)
            .where(MemoryItem.id == item.lineage_id, MemoryItem.owner_id == scope.actor.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    async def correct(self, scope: MemoryScope, item_id: str, change: MemoryCorrection) -> dict:
        scope.require("memory.write")
        async with self.db.sessions.begin() as session:
            item = await self._item(session, scope, item_id)
            await self._lock_lineage(session, scope, item)
            await session.refresh(item)
            if (
                item.memory_class not in EDITABLE
                or item.deleted_at is not None
                or item.superseded_by is not None
                or item.revision != change.expected_revision
                or item.revision >= 32
                or item.visibility == Visibility.RETIRED
                or (item.expires_at and utc(item.expires_at) <= now())
            ):
                raise MemoryConflict("Memory is protected, inactive or its revision changed")
            body = MemoryCreate(
                memory_class=MemoryClass(item.memory_class),
                namespace=item.namespace,
                visibility=Visibility(item.visibility),
                mode=item.mode,
                content=change.content,
                structured_data=change.structured_data,
                sources=change.sources,
                expires_at=utc(item.expires_at) if item.expires_at else None,
            )
            replacement = await self._insert(
                session,
                scope,
                body,
                lineage=item.lineage_id,
                revision=item.revision + 1,
                supersedes=item.id,
                expires=item.expires_at,
            )
            claimed = await session.scalar(
                update(MemoryItem)
                .where(
                    MemoryItem.id == item.id,
                    MemoryItem.deleted_at.is_(None),
                    MemoryItem.superseded_by.is_(None),
                    MemoryItem.revision == change.expected_revision,
                )
                .values(superseded_by=replacement.id)
                .returning(MemoryItem.id)
            )
            if claimed is None:
                raise MemoryConflict("Memory revision changed")
            audit(
                session,
                scope.actor.id,
                "memory.corrected",
                {"old_id": item.id, "id": replacement.id},
            )
            return (await self._views(session, [replacement]))[0]

    async def delete(self, scope: MemoryScope, item_id: str) -> None:
        scope.require("memory.write")
        async with self.db.sessions.begin() as session:
            item = await self._item(session, scope, item_id)
            await self._lock_lineage(session, scope, item)
            await session.refresh(item)
            if item.memory_class not in EDITABLE:
                raise MemoryConflict("Protected memory requires its domain retention workflow")
            ids = list(
                await session.scalars(
                    select(MemoryItem.id).where(
                        MemoryItem.owner_id == scope.actor.id,
                        MemoryItem.lineage_id == item.lineage_id,
                    )
                )
            )
            await session.execute(
                update(MemoryItem)
                .where(MemoryItem.id.in_(ids))
                .values(
                    content="",
                    structured_data={},
                    embedding_json=[],
                    embedding_key="",
                    deleted_at=now(),
                )
            )
            await session.execute(delete(MemorySource).where(MemorySource.memory_id.in_(ids)))
            await session.execute(
                update(MemoryProposal)
                .where(
                    MemoryProposal.owner_id == scope.actor.id,
                    MemoryProposal.memory_id.in_(ids),
                )
                .values(payload={})
            )
            audit(
                session,
                scope.actor.id,
                "memory.deleted",
                {"lineage_id": item.lineage_id, "ids": ids},
            )

    async def live_views(self, scope: MemoryScope, ids: list[str]) -> list[dict]:
        scope.require("memory.read")
        async with self.db.sessions() as session:
            rows = list(
                await session.scalars(
                    select(MemoryItem).where(
                        *self.predicates(scope),
                        MemoryItem.id.in_(ids[:50]),
                    )
                )
            )
            return await self._views(session, rows)

    async def search(
        self, scope: MemoryScope, question: str, *, limit=10, for_context=False
    ) -> list[dict]:
        scope.require("memory.read")
        # No embedding provider sees content until these SQL authorization predicates pass.
        async with self.db.sessions() as session:
            candidates = list(
                await session.scalars(
                    select(MemoryItem)
                    .where(*self.predicates(scope))
                    .order_by(MemoryItem.created_at.desc(), MemoryItem.id)
                    .limit(self.settings.memory_candidates)
                )
            )
            if not candidates:
                return []
            query = checked_vector(
                await self.embeddings.embed(question), self.embeddings.dimensions
            )
            similarities: dict[str, float] = {}
            matching = [m.id for m in candidates if m.embedding_key == self.embeddings.key]
            if self.settings.memory_pgvector and matching:
                distance = literal_column(
                    "CAST(CAST(memory_items.embedding_json AS TEXT) AS vector)"
                ).op("<=>")(
                    text("CAST(:query_vector AS vector)").bindparams(
                        bindparam("query_vector", type_=String())
                    )
                )
                rows = await session.execute(
                    select(MemoryItem.id, distance.label("distance")).where(
                        *self.predicates(scope), MemoryItem.id.in_(matching)
                    ),
                    {"query_vector": json.dumps(query)},
                )
                similarities = {row.id: max(0.0, 1.0 - float(row.distance)) for row in rows}
            else:
                for item in candidates:
                    if item.embedding_key == self.embeddings.key:
                        vector = checked_vector(item.embedding_json, self.embeddings.dimensions)
                        similarities[item.id] = max(
                            0.0, sum(a * b for a, b in zip(query, vector, strict=True))
                        )
            requested = terms(question)
            ranked = []
            for item in candidates:
                matched = sorted(
                    requested & terms(item.content + " " + json.dumps(item.structured_data))
                )
                semantic = similarities.get(item.id, 0.0)
                reasons = []
                score = semantic * 0.5 + len(matched) / max(1, len(requested))
                if matched:
                    reasons.append({"kind": "matched_terms", "terms": matched[:12]})
                if semantic >= 0.2:
                    reasons.append(
                        {
                            "kind": "embedding_similarity",
                            "value": round(semantic, 4),
                            "provider": self.embeddings.key,
                        }
                    )
                if for_context:
                    if item.memory_class == MemoryClass.PREFERENCE:
                        score += 0.4
                        reasons.append({"kind": "applicable_preference"})
                    if item.memory_class == MemoryClass.WORKING:
                        score += 0.5
                        reasons.append({"kind": "current_session_state"})
                    if item.memory_class == MemoryClass.CANONICAL and item.namespace != "personal":
                        score += 0.4
                        reasons.append({"kind": "current_scope_canonical_state"})
                    if item.memory_class == MemoryClass.EPISODIC and utc(
                        item.created_at
                    ) > now() - timedelta(days=3):
                        score += 0.25
                        reasons.append({"kind": "recent_event"})
                if reasons:
                    ranked.append((score, item, reasons))
            # pgvector uses float32; normalize ordering across both retrieval paths.
            ranked.sort(key=lambda hit: (-round(hit[0], 6), hit[1].id))
            selected = ranked[: max(1, min(limit, 50))]
            # Embedding calls may yield while memory is corrected, deleted or expired.
            live = {
                item.id: item
                for item in await session.scalars(
                    select(MemoryItem)
                    .where(
                        *self.predicates(scope),
                        MemoryItem.id.in_([m.id for _, m, _ in selected]),
                    )
                    .execution_options(populate_existing=True)
                )
            }
            selected = [hit for hit in selected if hit[1].id in live]
            views = await self._views(session, [live[item.id] for _, item, _ in selected])
            return [
                dict(
                    view,
                    retrieval={
                        "score": round(score, 4),
                        "reasons": reasons,
                        "candidate_limit": self.settings.memory_candidates,
                    },
                )
                for view, (score, _, reasons) in zip(views, selected, strict=True)
            ]

    async def propose(self, scope: MemoryScope, body: MemoryCreate) -> dict:
        scope.require("memory.propose")
        if body.namespace not in scope.namespaces:
            raise MemoryDenied("Memory namespace denied")
        if body.memory_class == MemoryClass.CANONICAL or body.visibility in {
            Visibility.GM_SECRET,
            Visibility.RETIRED,
        }:
            raise MemoryDenied("Models cannot propose canonical or protected visibility records")
        async with self.db.sessions.begin() as session:
            proposal = MemoryProposal(owner_id=scope.actor.id, payload=body.model_dump(mode="json"))
            session.add(proposal)
            await session.flush()
            audit(session, scope.actor.id, "memory.proposed", {"proposal_id": proposal.id})
            return {"proposal_id": proposal.id, "status": "PENDING", "memory_created": False}

    async def proposals(self, scope: MemoryScope) -> list[dict]:
        scope.require("memory.read")
        async with self.db.sessions() as session:
            rows = await session.scalars(
                select(MemoryProposal)
                .where(
                    MemoryProposal.owner_id == scope.actor.id,
                    MemoryProposal.payload["namespace"].as_string().in_(scope.namespaces),
                    or_(
                        MemoryProposal.payload["mode"].as_string().is_(None),
                        MemoryProposal.payload["mode"].as_string() == scope.mode.value,
                    ),
                )
                .order_by(MemoryProposal.created_at.desc())
                .limit(100)
            )
            return [
                {
                    "id": p.id,
                    "status": p.status,
                    "payload": p.payload,
                    "memory_id": p.memory_id,
                    "trust": "UNTRUSTED_PROPOSAL",
                }
                for p in rows
            ]

    async def decide_proposal(self, scope: MemoryScope, proposal_id: str, *, accept: bool) -> dict:
        scope.require("memory.write")
        async with self.db.sessions.begin() as session:
            proposal = await session.scalar(
                select(MemoryProposal)
                .where(
                    MemoryProposal.id == proposal_id,
                    MemoryProposal.owner_id == scope.actor.id,
                    MemoryProposal.payload["namespace"].as_string().in_(scope.namespaces),
                    or_(
                        MemoryProposal.payload["mode"].as_string().is_(None),
                        MemoryProposal.payload["mode"].as_string() == scope.mode.value,
                    ),
                )
                .with_for_update()
            )
            if proposal is None:
                raise KeyError("Memory proposal not found")
            status = "ACCEPTED" if accept else "REJECTED"
            claimed = await session.scalar(
                update(MemoryProposal)
                .where(
                    MemoryProposal.id == proposal.id,
                    MemoryProposal.status == "PENDING",
                )
                .values(status=status)
                .returning(MemoryProposal.id)
            )
            if claimed is None:
                raise MemoryConflict("Memory proposal already decided")
            result = {"id": proposal.id, "status": status}
            if accept:
                body = MemoryCreate.model_validate(proposal.payload)
                if body.memory_class == MemoryClass.CANONICAL or body.visibility in {
                    Visibility.GM_SECRET,
                    Visibility.RETIRED,
                }:
                    raise MemoryDenied("Protected model proposal rejected")
                body.sources = [SourceInput(kind=SourceKind.MODEL_PROPOSAL, locator=proposal.id)]
                item = await self._insert(session, scope, body)
                proposal.memory_id = item.id
                result["memory_id"] = item.id
            audit(session, scope.actor.id, f"memory.proposal_{status.lower()}", {"id": proposal.id})
            return result
