"""Run explicitly against a disposable local database whose name ends in _test."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_engine_api import drain, fake_external, pending_approval

from jarvis.config import Settings
from jarvis.db import Base, Database
from jarvis.domain import ChatRequest, RunState
from jarvis.engine import Conflict, Engine
from jarvis.models import FakeModelProvider, ModelRouter

TEST_URL = os.environ.get("JARVIS_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="Set disposable JARVIS_TEST_DATABASE_URL")


@pytest.fixture(scope="module")
def migrated_postgres():
    from sqlalchemy.engine import make_url

    url = make_url(TEST_URL)
    assert url.host in {"localhost", "127.0.0.1"} and url.database.endswith("_test"), (
        "Destructive migration test requires an explicitly disposable local *_test database"
    )
    ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    environment = {**os.environ, "JARVIS_DATABASE_URL": TEST_URL}
    for operation in [("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")]:
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(ini), *operation],
            env=environment,
            check=True,
            capture_output=True,
            timeout=30,
        )
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
