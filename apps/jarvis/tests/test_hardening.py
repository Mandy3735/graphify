import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from jarvis.api import create_app
from jarvis.budgets import BudgetExceeded, ProviderBudget
from jarvis.config import Settings
from jarvis.db import AuditEvent, VoiceSession
from jarvis.domain import Message, ModelResult
from jarvis.ingress import Ingress
from jarvis.models import OpenAIModelProvider


def production(settings):
    values = settings.model_dump()
    values.update(
        environment="production",
        public_origin="https://jarvis.example",
        auth_token="x" * 48,
        database_url="postgresql+asyncpg://runtime@localhost/jarvis",
    )
    return Settings(**values, _env_file=None)


@pytest.mark.parametrize(
    "change",
    [
        {"public_origin": "http://jarvis.example"},
        {"auth_token": "x" * 32},
        {"database_url": "sqlite+aiosqlite:///x"},
        {"public_origin": "https://user:secret@jarvis.example"},
        {"public_origin": "https://jarvis.example/path"},
        {"pricing": {"model": [float("nan"), 1]}},
        {"provider_operation_costs": {"speech:model": -1}},
    ],
)
def test_production_configuration_rejects_incomplete_or_nonfinite_controls(settings, change):
    values = production(settings).model_dump()
    values.update(change)
    with pytest.raises(ValidationError):
        Settings(**values, _env_file=None)


async def test_ingress_byte_bounds_rate_and_origin_before_database_work(settings, database):
    settings.api_requests_per_minute = 10
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {settings.auth_token.get_secret_value()}"},
        ) as client,
    ):
        assert (await client.post("/api/chat", json={"message": "x" * 270000})).status_code == 413
        assert (
            await client.post(
                "/api/chat", json={"message": "x"}, headers={"Origin": "https://evil.example"}
            )
        ).status_code == 403

        async def chunks():
            yield b"x" * 200000
            yield b"x" * 100000

        assert (await client.post("/api/chat", content=chunks())).status_code == 413
        for _ in range(8):
            assert (await client.get("/api/settings")).status_code == 200
        limited = await client.get("/api/settings")
        assert limited.status_code == 429 and limited.headers["retry-after"] == "60"
        assert limited.headers["cache-control"] == "no-store"
        async with database.sessions() as session:
            events = list(await session.scalars(select(AuditEvent)))
            assert len(events) == 8  # Only admitted authenticated reads reached the DB.


async def test_unauthenticated_rate_ignores_forwarded_header(settings, database):
    settings.unauthenticated_requests_per_minute = 5
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client,
    ):
        for i in range(5):
            assert (
                await client.get("/api/settings", headers={"X-Forwarded-For": f"1.2.3.{i}"})
            ).status_code == 401
        assert (await client.get("/api/settings")).status_code == 429
        client.headers["Authorization"] = f"Bearer {settings.auth_token.get_secret_value()}"
        assert (await client.get("/api/settings")).status_code == 200


async def test_https_host_and_lease_fail_closed_without_trusting_forwarded_headers(settings):
    cfg = production(settings)
    response_events = []
    called = False

    async def target(scope, receive, send):
        nonlocal called
        called = True

    guard = SimpleNamespace(healthy=False)
    gate = Ingress(target, cfg, guard)
    scope = {
        "type": "http",
        "scheme": "http",
        "path": "/api/settings",
        "headers": [(b"host", b"jarvis.example"), (b"x-forwarded-proto", b"https")],
        "client": ("127.0.0.1", 1),
    }

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(event):
        response_events.append(event)

    await gate(scope, receive, send)
    assert response_events[0]["status"] == 400 and not called
    response_events.clear()
    scope["scheme"] = "https"
    await gate(scope, receive, send)
    assert response_events[0]["status"] == 503 and not called
    response_events.clear()
    scope["headers"] = [(b"host", b"attacker.example")]
    await gate(scope, receive, send)
    assert response_events[0]["status"] == 400


async def test_body_deadline_concurrency_and_duplicate_headers(settings):
    async def target(*args):
        raise AssertionError("Rejected request must not execute")

    gate = Ingress(target, settings, SimpleNamespace(healthy=True))
    gate.cfg.request_body_timeout = 0.01
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/api/chat",
        "client": ("test", 0),
        "headers": [
            (b"host", b"test"),
            (b"authorization", b"Bearer " + settings.auth_token.get_secret_value().encode()),
        ],
    }
    output = []

    async def send(message):
        output.append(message)

    async def slow():
        await asyncio.Event().wait()

    await gate(scope, slow, send)
    assert output[0]["status"] == 408 and gate.active == 0
    output.clear()
    gate.active = settings.concurrent_http_requests
    await gate(scope, slow, send)
    assert output[0]["status"] == 429
    output.clear()
    scope["headers"].append((b"host", b"second"))
    await gate(scope, slow, send)
    assert output[0]["status"] == 400


async def test_provider_budget_survives_restart_after_uncertain_outcome(settings, database):
    settings.provider_daily_budget_usd = 0.01
    settings.pricing = {"live": (1, 1)}
    budget = ProviderBudget(database, settings)
    key = await budget.reserve("reasoning", "live", 6000)
    await budget.finish(key, None, {}, "UNCERTAIN")
    restarted = ProviderBudget(database, settings)
    with pytest.raises(BudgetExceeded):
        await restarted.reserve("reasoning", "live", 6000)
    assert (await restarted.status())["charged_estimate_usd"] == 0.006
    with pytest.raises(BudgetExceeded):
        budget.token_cost("unpriced", 10)
    with pytest.raises(BudgetExceeded):
        budget.operation_cost("speech", "unpriced")


async def test_budget_settlement_and_pre_call_denial(settings, database):
    budget = ProviderBudget(database, settings)
    key = await budget.reserve("reasoning", "priced", 5000)
    await budget.finish(key, 1000, {"input_tokens": 1000}, "SETTLED")
    await budget.finish(key, 0, {}, "SETTLED")
    assert (await budget.status())["charged_estimate_usd"] == 0.001
    provider = OpenAIModelProvider(settings, budget=budget)
    provider._respond = AsyncMock(return_value=ModelResult(text="not called"))
    with pytest.raises(BudgetExceeded):
        await provider.respond("unpriced", [Message(role="user", text="request")], [])
    provider._respond.assert_not_called()


async def test_provider_cancellation_retains_reservation_and_usage_settles(settings, database):
    settings.pricing = {"live": (1, 1)}
    budget = ProviderBudget(database, settings)
    provider = OpenAIModelProvider(settings, budget=budget)
    entered = asyncio.Event()

    async def pending(*args):
        entered.set()
        await asyncio.Event().wait()

    provider._respond = pending
    task = asyncio.create_task(provider.respond("live", [Message(role="user", text="request")], []))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    status = await budget.status()
    assert status["calls"][0]["state"] == "UNCERTAIN"
    provider._respond = AsyncMock(
        return_value=ModelResult(text="result", input_tokens=10, output_tokens=5)
    )
    await provider.respond("live", [Message(role="user", text="request")], [])
    assert (await budget.status())["calls"][0]["usage"] == {"input_tokens": 10, "output_tokens": 5}


async def test_saved_voice_identifier_is_recovered_without_replay(settings, database, monkeypatch):
    settings.voice_provider = "fake"
    app = create_app(settings)
    async with database.sessions.begin() as session:
        session.add(
            VoiceSession(
                id="orphan",
                actor_id=str(settings.actor_id),
                provider="openai",
                provider_id="rtc_saved",
                state="STOP_FAILED",
            )
        )
    stop = AsyncMock()
    monkeypatch.setattr("jarvis.voice_api.OpenAILiveVoiceProvider.stop", stop)
    await app.state.voice.recover()
    assert stop.call_args.args[0].provider_id == "rtc_saved"
    async with database.sessions() as session:
        assert (await session.get(VoiceSession, "orphan")).state == "STOPPED"
    await app.state.database.dispose()


async def test_unresolved_voice_requires_explicit_human_reconciliation(settings, database):
    settings.voice_provider = "fake"
    async with database.sessions.begin() as session:
        session.add(
            VoiceSession(
                id="unknown",
                actor_id=str(settings.actor_id),
                provider="openai",
                provider_id="",
                state="CREATING",
            )
        )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {settings.auth_token.get_secret_value()}"},
        ) as client,
    ):
        await app.state.voice.recovery_task
        assert (await client.get("/api/voice/status")).json()["cleanup_pending"] == [
            {"id": "unknown", "state": "UNRESOLVED"}
        ]
        assert (
            await client.post(
                "/api/voice/sessions/unknown/reconcile", json={"remote_stopped": False}
            )
        ).status_code == 422
        assert (
            await client.post(
                "/api/voice/sessions/unknown/reconcile", json={"remote_stopped": True}
            )
        ).status_code == 204
        assert (await client.get("/api/voice/status")).json()["cleanup_pending"] == []


async def test_startup_failure_still_closes_clients_and_disposes_database(settings, monkeypatch):
    app = create_app(settings)
    closed = AsyncMock()
    monkeypatch.setattr(app.state.engine, "close", closed)

    async def fail():
        raise RuntimeError("deliberate startup failure")

    monkeypatch.setattr(app.state.memory, "check_backend", fail)
    disposed = AsyncMock(wraps=app.state.database.dispose)
    monkeypatch.setattr(app.state.database, "dispose", disposed)
    with pytest.raises(RuntimeError, match="deliberate"):
        async with app.router.lifespan_context(app):
            pass
    closed.assert_awaited_once()
    disposed.assert_awaited_once()


async def test_production_errors_hide_exception_parameters(settings, caplog):
    cfg = production(settings)

    async def broken(*args):
        raise RuntimeError("PRIVATE_BODY_AND_CREDENTIAL")

    gate = Ingress(broken, cfg, SimpleNamespace(healthy=True))
    output = []

    async def send(message):
        output.append(message)

    async def receive():
        return {"type": "http.request", "body": b""}

    await gate(
        {
            "type": "http",
            "scheme": "https",
            "path": "/api/settings",
            "headers": [(b"host", b"jarvis.example"), (b"authorization", b"Bearer " + b"x" * 48)],
        },
        receive,
        send,
    )
    assert output[0]["status"] == 500
    assert "PRIVATE_BODY_AND_CREDENTIAL" not in json.dumps(output, default=str)
    assert "PRIVATE_BODY_AND_CREDENTIAL" not in caplog.text


async def test_unexpected_provider_usage_is_accounted_and_result_withheld(settings, database):
    settings.pricing = {"live": (1, 1)}
    budget = ProviderBudget(database, settings)
    provider = OpenAIModelProvider(settings, budget=budget)
    provider._respond = AsyncMock(
        return_value=ModelResult(text="withheld", input_tokens=10_000_000)
    )
    with pytest.raises(BudgetExceeded):
        await provider.respond("live", [Message(role="user", text="small request")], [])
    status = await budget.status()
    assert status["charged_estimate_usd"] == 10
    assert status["calls"][0]["state"] == "OVERRUN"


async def test_health_and_api_report_lost_runtime_lease(settings, database):
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {settings.auth_token.get_secret_value()}"},
        ) as client,
    ):
        assert (await client.get("/health")).status_code == 200
        app.state.runtime.healthy = False
        assert (await client.get("/health")).status_code == 503
        assert (await client.get("/api/settings")).status_code == 503


async def test_voice_shutdown_closes_sdk_even_if_journal_is_unavailable(settings, database):
    settings.voice_provider = "fake"
    app = create_app(settings)
    service = app.state.voice
    key = (await service.start(""))["id"]
    service.session_state = AsyncMock(side_effect=RuntimeError("journal unavailable"))
    service.provider.close = AsyncMock()
    with pytest.raises(RuntimeError, match="journal unavailable"):
        await service.close()
    service.provider.close.assert_awaited_once()
    assert key not in service.sessions
    await app.state.database.dispose()
