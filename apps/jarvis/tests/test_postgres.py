"""Run explicitly against a disposable local database whose name ends in _test."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from test_engine_api import drain, fake_external, pending_approval
from test_memory import correction, record

from jarvis.config import Settings
from jarvis.db import (
    AuditEvent,
    Base,
    CampaignEntry,
    CampaignEvent,
    CampaignEventProposal,
    Database,
    MasteryEvidence,
    MemoryItem,
    MemoryProposal,
    TutorAttempt,
    audit,
)
from jarvis.domain import ChatRequest, Mode, RunState
from jarvis.embeddings import FakeEmbeddingProvider
from jarvis.engine import Conflict, Engine
from jarvis.game_master import (
    GameMasterConflict,
    GameMasterScope,
    GameMasterService,
    SeededDiceEntropy,
)
from jarvis.game_master_schema import (
    CampaignChange,
    CampaignChangeAction,
    CampaignCreate,
    CampaignEntryCreate,
    CampaignEntryKind,
    CampaignMemberCreate,
    CampaignProposalCreate,
    CampaignRole,
    CampaignVisibility,
    DelegationCreate,
    DiceRequest,
)
from jarvis.memory import MemoryConflict, MemoryScope, MemoryService
from jarvis.models import FakeModelProvider, ModelRouter
from jarvis.policy import Actor
from jarvis.tutor import TutorScope, TutorService
from jarvis.tutor_schema import (
    LearnerAttemptCreate,
    LearningObjectiveCreate,
    LearningSourceInput,
    LearningSourceKind,
    QuizCreate,
)

TEST_URL = os.environ.get("JARVIS_TEST_DATABASE_URL", "")
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
pytestmark = pytest.mark.skipif(not TEST_URL, reason="Set disposable JARVIS_TEST_DATABASE_URL")


@pytest.fixture(scope="module")
def migrated_postgres():
    from sqlalchemy.engine import make_url

    url = make_url(TEST_URL)
    assert url.host in {"localhost", "127.0.0.1"} and url.database.endswith("_test"), (
        "Destructive migration test requires an explicitly disposable local *_test database"
    )
    ini = ALEMBIC_INI
    environment = {**os.environ, "JARVIS_DATABASE_URL": TEST_URL}
    for operation in [("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")]:
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(ini), *operation],
            env=environment,
            check=True,
            capture_output=True,
            timeout=30,
        )
    if os.environ.get("JARVIS_TEST_PGVECTOR") == "true":

        async def enable_vector():
            db = Database(TEST_URL)
            async with db.sessions.begin() as session:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await db.dispose()

        asyncio.run(enable_vector())
    yield
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini), "downgrade", "base"],
        env=environment,
        check=True,
        capture_output=True,
        timeout=30,
    )


@pytest.fixture
async def postgres(migrated_postgres):
    db = Database(TEST_URL)
    yield db
    await db.dispose()


def pg_settings():
    return Settings(
        auth_token="test-token-with-at-least-32-characters",
        database_url=TEST_URL,
        capabilities=frozenset({"test.write"}),
        _env_file=None,
    )


async def test_postgres_migrations_match_metadata(postgres):
    async with postgres.engine.connect() as connection:
        differences = await connection.run_sync(
            lambda c: compare_metadata(MigrationContext.configure(c), Base.metadata)
        )
        assert differences == []


async def test_postgres_approval_claim_is_atomic_and_run_survives_reconnect(postgres):
    cfg = pg_settings()
    registry, effects = fake_external()
    engine = Engine(cfg, postgres, ModelRouter(cfg, FakeModelProvider()), registry)
    run_id = await engine.create(ChatRequest(message='[tool:external.write] {"target":"pg"}'))
    await drain(engine)
    approval = await pending_approval(postgres, run_id)
    competing = Engine(cfg, postgres, ModelRouter(cfg, FakeModelProvider()), registry)
    claims = await asyncio.gather(
        engine.approve(approval.id), competing.approve(approval.id), return_exceptions=True
    )
    await drain(engine)
    await drain(competing)
    assert sum(isinstance(value, Conflict) for value in claims) == 1
    assert sum(isinstance(value, str) for value in claims) == 1
    assert effects == [{"target": "pg", "value": 1}]
    fresh = Database(TEST_URL)
    restored = Engine(cfg, fresh, ModelRouter(cfg, FakeModelProvider()), registry)
    await restored.recover()
    run = await restored._snapshot(run_id)
    assert run.state == RunState.COMPLETED and run.result
    await fresh.dispose()


async def test_postgres_audit_cannot_be_updated_deleted_or_truncated(postgres):
    for statement in [
        "UPDATE audit_events SET event='rewritten'",
        "DELETE FROM audit_events",
        "TRUNCATE audit_events",
    ]:
        with pytest.raises(DBAPIError, match="append-only"):
            async with postgres.sessions.begin() as session:
                await session.execute(text(statement))


def pg_memory(database, *, vector=False):
    cfg = pg_settings().model_copy(update={"memory_pgvector": vector})
    service = MemoryService(database, cfg, FakeEmbeddingProvider())
    actor = Actor(str(cfg.actor_id), frozenset({"memory.read", "memory.write", "memory.propose"}))
    return service, MemoryScope(actor, Mode.CHIEF_OF_STAFF)


async def test_postgres_memory_revision_upgrade_preserves_existing_foundation_audit(postgres):
    # Exercise the actual additive 0001 → 0002 boundary, with existing protected audit.
    async with postgres.sessions.begin() as session:
        audit(
            session, str(pg_settings().actor_id), "phase5.migration_sentinel", {"foundation": True}
        )
    async with postgres.sessions() as session:
        before = list(await session.scalars(select(AuditEvent.id)))
    ini = ALEMBIC_INI
    environment = {**os.environ, "JARVIS_DATABASE_URL": TEST_URL}
    for operation in [("downgrade", "0001"), ("upgrade", "head")]:
        await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "alembic", "-c", str(ini), *operation],
            env=environment,
            check=True,
            capture_output=True,
            timeout=30,
        )
    async with postgres.sessions() as session:
        after = list(await session.scalars(select(AuditEvent.id)))
    assert set(before) == set(after)


async def test_postgres_memory_survives_reconnect_and_remains_owner_scoped(postgres):
    memory, scope = pg_memory(postgres)
    item = await memory.create(scope, record("persistent automobile repair"))
    fresh = Database(TEST_URL)
    restored, _ = pg_memory(fresh)
    hits = await restored.search(scope, "vehicle fix")
    assert any(h["id"] == item["id"] and h["sources"] for h in hits)
    foreign = MemoryScope(
        Actor("2e85dfde-df21-49e9-840c-2b5e04b2eed0", scope.actor.capabilities), scope.mode
    )
    assert await restored.search(foreign, "vehicle fix") == []
    await fresh.dispose()


async def test_postgres_concurrent_corrections_and_delete_cannot_resurrect_memory(postgres):
    memory, scope = pg_memory(postgres)
    original = await memory.create(scope, record("concurrent memory"))
    first, second = await asyncio.gather(
        memory.correct(scope, original["id"], correction("first correction")),
        memory.correct(scope, original["id"], correction("second correction")),
        return_exceptions=True,
    )
    assert sum(isinstance(value, MemoryConflict) for value in [first, second]) == 1
    current = next(value for value in [first, second] if isinstance(value, dict))
    results = await asyncio.gather(
        memory.correct(scope, current["id"], correction("race against deletion", revision=2)),
        memory.delete(scope, original["id"]),
        return_exceptions=True,
    )
    assert all(value is None or isinstance(value, (dict, MemoryConflict)) for value in results)
    async with postgres.sessions() as session:
        rows = list(
            await session.scalars(select(MemoryItem).where(MemoryItem.lineage_id == original["id"]))
        )
    assert all(
        row.deleted_at is not None and row.content == "" and not row.embedding_json for row in rows
    )


async def test_postgres_memory_proposal_acceptance_is_atomic(postgres):
    memory, scope = pg_memory(postgres)
    proposal = await memory.propose(scope, record("one accepted proposal"))
    claims = await asyncio.gather(
        memory.decide_proposal(scope, proposal["proposal_id"], accept=True),
        memory.decide_proposal(scope, proposal["proposal_id"], accept=True),
        return_exceptions=True,
    )
    assert sum(isinstance(value, MemoryConflict) for value in claims) == 1
    accepted = next(value for value in claims if isinstance(value, dict))
    async with postgres.sessions() as session:
        stored = await session.get(MemoryProposal, proposal["proposal_id"])
        assert stored.status == "ACCEPTED" and stored.memory_id == accepted["memory_id"]
    assert (await memory.inspect(scope, accepted["memory_id"]))["sources"][0][
        "kind"
    ] == "MODEL_PROPOSAL"


def pg_tutor(database):
    cfg = pg_settings()
    actor = Actor(str(cfg.actor_id), frozenset({"tutor.read", "tutor.write", "tutor.attempt"}))
    return TutorService(database), TutorScope(actor)


async def tutor_fixture(tutor, scope, *, required=1):
    objective = await tutor.create_objective(
        scope,
        LearningObjectiveCreate(
            title="PostgreSQL Tutor race",
            description="Prove learner evidence remains atomic.",
            mastery_required_quizzes=required,
            mastery_min_score=80,
            sources=[
                LearningSourceInput(
                    kind=LearningSourceKind.DOCUMENT,
                    locator="test:postgres-tutor",
                    quote="Evidence must come from a human learner attempt.",
                )
            ],
        ),
    )
    source_id = objective["sources"][0]["id"]
    quizzes = []
    for number in range(required):
        quizzes.append(
            await tutor.create_quiz(
                scope,
                objective["id"],
                QuizCreate(
                    prompt=f"Answer quiz {number + 1}",
                    accepted_answers=[f"answer {number + 1}"],
                    source_ids=[source_id],
                ),
            )
        )
    return objective, quizzes


async def test_phase7_migration_preserves_memory_and_audit(postgres):
    memory, scope = pg_memory(postgres)
    item = await memory.create(scope, record("survives the Tutor migration boundary"))
    async with postgres.sessions.begin() as session:
        audit(
            session,
            str(pg_settings().actor_id),
            "phase7.migration_sentinel",
            {"memory_id": item["id"]},
        )
    ini = ALEMBIC_INI
    environment = {**os.environ, "JARVIS_DATABASE_URL": TEST_URL}
    for operation in [("downgrade", "0002"), ("upgrade", "head")]:
        await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "alembic", "-c", str(ini), *operation],
            env=environment,
            check=True,
            capture_output=True,
            timeout=30,
        )
    assert (await memory.inspect(scope, item["id"]))["content"] == (
        "survives the Tutor migration boundary"
    )
    async with postgres.sessions() as session:
        sentinel = await session.scalar(
            select(AuditEvent).where(AuditEvent.event == "phase7.migration_sentinel")
        )
        assert sentinel is not None


async def test_postgres_duplicate_tutor_submission_and_mastery_are_atomic(postgres):
    tutor, scope = pg_tutor(postgres)
    objective, quizzes = await tutor_fixture(tutor, scope)
    body = LearnerAttemptCreate(submission_id="same-http-retry", answer="answer 1")
    results = await asyncio.gather(
        tutor.submit_attempt(scope, quizzes[0]["id"], body),
        tutor.submit_attempt(scope, quizzes[0]["id"], body),
    )
    assert results[0]["id"] == results[1]["id"]
    assert sum(result["idempotent_replay"] for result in results) == 1
    async with postgres.sessions() as session:
        attempts = list(
            await session.scalars(
                select(TutorAttempt).where(TutorAttempt.objective_id == objective["id"])
            )
        )
        evidence = list(
            await session.scalars(
                select(MasteryEvidence).where(MasteryEvidence.objective_id == objective["id"])
            )
        )
    assert len(attempts) == 1 and len(evidence) == 1


async def test_postgres_concurrent_distinct_quizzes_create_one_mastery_record(postgres):
    tutor, scope = pg_tutor(postgres)
    objective, quizzes = await tutor_fixture(tutor, scope, required=2)
    results = await asyncio.gather(
        tutor.submit_attempt(
            scope,
            quizzes[0]["id"],
            LearnerAttemptCreate(submission_id="parallel-1", answer="answer 1"),
        ),
        tutor.submit_attempt(
            scope,
            quizzes[1]["id"],
            LearnerAttemptCreate(submission_id="parallel-2", answer="answer 2"),
        ),
    )
    assert all(result["correct"] for result in results)
    state = await tutor.inspect_objective(scope, objective["id"])
    assert state["status"] == "MASTERED"
    assert state["mastery_evidence"]["distinct_quizzes"] == 2


def pg_game(database):
    cfg = pg_settings()
    actor = Actor(
        str(cfg.actor_id),
        frozenset(
            {
                "campaign.read",
                "campaign.write",
                "campaign.dice",
                "campaign.delegate",
                "campaign.propose",
                "campaign.approve",
                "campaign.transcript",
            }
        ),
    )
    return GameMasterService(database, entropy=SeededDiceEntropy("postgres-phase8")), (
        GameMasterScope(actor)
    )


async def pg_campaign(database):
    service, gm = pg_game(database)
    campaign = await service.create_campaign(gm, CampaignCreate(name="PostgreSQL campaign"))
    player_id = "57ecb6a8-acde-47aa-993b-ece0551e0b8b"
    await service.add_member(
        gm,
        campaign["id"],
        CampaignMemberCreate(
            actor_id=player_id,
            role=CampaignRole.PLAYER,
            display_name="PostgreSQL player",
        ),
    )
    player = GameMasterScope(Actor(player_id, gm.actor.capabilities))
    pc = await service.create_entry(
        gm,
        campaign["id"],
        CampaignEntryCreate(
            kind=CampaignEntryKind.PC,
            name="Player",
            content="A controlled player character.",
            visibility=CampaignVisibility.PLAYER_PRIVATE,
            player_actor_id=player_id,
        ),
    )
    return service, gm, player, campaign, pc


async def test_phase8_migration_preserves_tutor_and_audit(postgres):
    tutor, scope = pg_tutor(postgres)
    objective, _ = await tutor_fixture(tutor, scope)
    async with postgres.sessions.begin() as session:
        audit(
            session,
            str(pg_settings().actor_id),
            "phase8.migration_sentinel",
            {"objective_id": objective["id"]},
        )
    environment = {**os.environ, "JARVIS_DATABASE_URL": TEST_URL}
    for operation in [("downgrade", "0003"), ("upgrade", "head")]:
        await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *operation],
            env=environment,
            check=True,
            capture_output=True,
            timeout=30,
        )
    assert (await tutor.inspect_objective(scope, objective["id"]))["title"] == (
        "PostgreSQL Tutor race"
    )
    async with postgres.sessions() as session:
        sentinel = await session.scalar(
            select(AuditEvent).where(AuditEvent.event == "phase8.migration_sentinel")
        )
        assert sentinel is not None


async def test_postgres_campaign_proposal_decision_is_atomic(postgres):
    service, gm, _, campaign, _ = await pg_campaign(postgres)
    proposal = await service.propose_event(
        gm,
        CampaignProposalCreate(
            campaign_id=campaign["id"],
            summary="Atomic canonical event",
            changes=[
                CampaignChange(
                    action=CampaignChangeAction.CREATE,
                    entry=CampaignEntryCreate(
                        kind=CampaignEntryKind.STATE,
                        name="Atomic state",
                        content="Committed once.",
                        visibility=CampaignVisibility.PARTY,
                    ),
                )
            ],
        ),
    )
    results = await asyncio.gather(
        service.decide_proposal(gm, campaign["id"], proposal["id"], approve=True),
        service.decide_proposal(gm, campaign["id"], proposal["id"], approve=True),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, GameMasterConflict) for result in results) == 1
    async with postgres.sessions() as session:
        proposals = list(
            await session.scalars(
                select(CampaignEventProposal).where(
                    CampaignEventProposal.campaign_id == campaign["id"]
                )
            )
        )
        events = list(
            await session.scalars(
                select(CampaignEvent).where(CampaignEvent.campaign_id == campaign["id"])
            )
        )
        entries = list(
            await session.scalars(
                select(CampaignEntry).where(
                    CampaignEntry.campaign_id == campaign["id"],
                    CampaignEntry.content == "Committed once.",
                )
            )
        )
    assert len(proposals) == len(events) == len(entries) == 1


async def test_postgres_one_use_roll_delegation_is_atomic(postgres):
    service, _, player, campaign, pc = await pg_campaign(postgres)
    await service.delegate_roll(
        player,
        campaign["id"],
        DelegationCreate(subject_entry_id=pc["id"], nonce="postgres-one-use"),
    )
    results = await asyncio.gather(
        service.roll(
            player,
            DiceRequest(
                campaign_id=campaign["id"],
                request_id="parallel-roll-1",
                subject_entry_id=pc["id"],
                expression="1d20",
            ),
        ),
        service.roll(
            player,
            DiceRequest(
                campaign_id=campaign["id"],
                request_id="parallel-roll-2",
                subject_entry_id=pc["id"],
                expression="1d20",
            ),
        ),
    )
    assert sorted(result["authority"] for result in results) == ["HUMAN", "JARVIS_DELEGATED"]


@pytest.mark.skipif(
    os.environ.get("JARVIS_TEST_PGVECTOR") != "true", reason="Optional pgvector database"
)
async def test_postgres_pgvector_retrieval_matches_offline_ranking(postgres):
    memory, scope = pg_memory(postgres)
    item = await memory.create(scope, record("optional automobile repair"))
    offline = await memory.search(scope, "vehicle fix", limit=50)
    configured, _ = pg_memory(postgres, vector=True)
    await configured.check_backend()
    accelerated = await configured.search(scope, "vehicle fix", limit=50)
    assert [h["id"] for h in accelerated] == [h["id"] for h in offline]
    assert item["id"] in [h["id"] for h in accelerated]
    assert [h["retrieval"]["score"] for h in accelerated] == pytest.approx(
        [h["retrieval"]["score"] for h in offline],
        abs=0.0001,
    )


@pytest.mark.skipif(
    os.environ.get("JARVIS_TEST_PGVECTOR") == "true", reason="Vector intentionally installed"
)
async def test_postgres_vector_flag_requires_installed_extension(postgres):
    memory, _ = pg_memory(postgres, vector=True)
    with pytest.raises(MemoryConflict, match="extension is not installed"):
        await memory.check_backend()


async def test_postgres_voice_delegation_persists_and_audits_without_canonical_authority(postgres):
    import httpx

    from jarvis.api import create_app

    cfg = pg_settings().model_copy(update={"actor_id": uuid4(), "voice_provider": "fake"})
    app = create_app(cfg)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {cfg.auth_token.get_secret_value()}"},
        ) as client,
    ):
        started = await client.post("/api/voice/sessions", json={})
        key = started.json()["id"]
        assert (await client.delete(f"/api/voice/sessions/{key}")).status_code == 204
        response = await client.post("/api/voice/submit", json={"message": "Voice fixture"})
        run_id = response.json()["run_id"]
        await drain(app.state.engine)
        assert (await client.get(f"/api/runs/{run_id}")).json()["state"] == "COMPLETED"
    async with postgres.sessions() as session:
        from jarvis.db import AgentRun

        run = await session.get(AgentRun, run_id)
        assert run.request["message"].startswith("[User-reviewed voice transcript;")
        events = list(
            await session.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_id == str(cfg.actor_id), AuditEvent.event.like("voice.%")
                )
            )
        )
        assert {e.event for e in events} == {"voice.started", "voice.stopped", "voice.delegated"}
        assert all("Voice fixture" not in str(e.details) for e in events)
