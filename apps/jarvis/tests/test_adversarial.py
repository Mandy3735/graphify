"""Phase 12 reproductions: authority, secret exclusion and pre-auth availability."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from test_game_master import campaign_fixture

from jarvis.context import ContextBuilder
from jarvis.db import CampaignMember
from jarvis.domain import ChatRequest, Message, Mode, ToolOutput
from jarvis.embeddings import FakeEmbeddingProvider
from jarvis.engineer import git, source_manifest
from jarvis.game_master_schema import (
    CampaignEntryCreate,
    CampaignEntryKind,
    CampaignSessionCreate,
    CampaignVisibility,
)
from jarvis.ingress import Ingress
from jarvis.memory import MemoryService
from jarvis.paths import PathDenied, safe_read


async def test_public_slow_bodies_cannot_starve_authenticated_admission(settings):
    settings.concurrent_http_requests = 4
    gate = Ingress(None, settings, SimpleNamespace(healthy=True))

    async def target(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    gate.app = target
    release = asyncio.Event()

    async def slow():
        await release.wait()
        return {"type": "http.request", "body": b"x"}

    async def fast():
        return {"type": "http.request", "body": b""}

    async def ignore(message):
        pass

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "headers": [(b"host", b"test"), (b"content-length", b"1")],
        "client": ("attacker", 0),
    }
    requests = [asyncio.create_task(gate(dict(scope), slow, ignore)) for _ in range(4)]
    await asyncio.sleep(0)
    output = []

    async def capture(message):
        output.append(message)

    authorized = {
        **scope,
        "path": "/api/settings",
        "headers": [
            (b"host", b"test"),
            (b"authorization", b"Bearer " + settings.auth_token.get_secret_value().encode()),
        ],
    }
    try:
        await gate(authorized, fast, capture)
        assert output[0]["status"] == 200
    finally:
        release.set()
        await asyncio.gather(*requests, return_exceptions=True)


@pytest.mark.parametrize(
    "path",
    ["credentials.json", "secrets.yaml", "config/client_secret.toml", "gcp-service-account.json"],
)
def test_conventional_credential_configs_are_excluded(tmp_path, path):
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("REPRO_FAKE_CREDENTIAL")
    with pytest.raises(PathDenied):
        safe_read(tmp_path, path)


async def test_engineer_snapshot_excludes_tracked_credentials_but_preserves_code(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "app.py").write_text("def main(): return 1\n")
    (root / "credentials.json").write_text('{"key":"REPRO_FAKE_CREDENTIAL"}')
    (root / "credentials.py").write_text("def credentials(): return None\n")
    await git(root, "init", "--quiet")
    await git(root, "add", ".")
    await git(root, "commit", "--quiet", "-m", "Adversarial fixture")
    _, files = await source_manifest(root)
    assert "credentials.json" not in files
    assert "app.py" in files and "credentials.py" in files


async def downgrade(database, actor_id, campaign_id):
    async with database.sessions.begin() as session:
        member = await session.scalar(
            select(CampaignMember).where(
                CampaignMember.actor_id == actor_id, CampaignMember.campaign_id == campaign_id
            )
        )
        member.role = "PLAYER"


async def test_campaign_tool_history_cannot_replay_gm_secrets_after_revocation(database, settings):
    service, gm, _, _, campaign, game_session, _, _, _, secret = await campaign_fixture(
        database, settings
    )
    old_scene = await service.scene_packet(gm, campaign["id"], game_session["id"])
    assert secret["content"] in json.dumps(old_scene)
    await downgrade(database, gm.actor.id, campaign["id"])
    memory = MemoryService(database, settings, FakeEmbeddingProvider())
    builder = ContextBuilder(settings, memory, service)
    request = ChatRequest(
        message="Continue the scene",
        mode=Mode.GAME_MASTER,
        campaign_id=campaign["id"],
        session_id=game_session["id"],
    )
    built = await builder.build(
        gm.actor,
        request,
        [
            Message(role="user", text=request.message),
            Message(
                role="assistant_tool",
                name="campaign.get_scene",
                call_id="scene",
                arguments={"campaign_id": campaign["id"]},
            ),
            Message(
                role="tool",
                name="campaign.get_scene",
                call_id="scene",
                text=ToolOutput(data=old_scene).model_dump_json(),
            ),
        ],
    )
    assert built.scene_packet["campaign"]["membership_role"] == "PLAYER"
    assert secret["content"] not in " ".join(m.model_dump_json() for m in built.messages)


async def test_campaign_packet_is_rechecked_after_awaited_memory_retrieval(database, settings):
    service, gm, _, _, campaign, game_session, _, _, _, secret = await campaign_fixture(
        database, settings
    )
    memory = MemoryService(database, settings, FakeEmbeddingProvider())
    entered, release = asyncio.Event(), asyncio.Event()

    async def delayed_search(*args, **kwargs):
        entered.set()
        await release.wait()
        return []

    memory.search = delayed_search
    builder = ContextBuilder(settings, memory, service)
    request = ChatRequest(
        message="Continue the scene",
        mode=Mode.GAME_MASTER,
        campaign_id=campaign["id"],
        session_id=game_session["id"],
    )
    task = asyncio.create_task(
        builder.build(gm.actor, request, [Message(role="user", text=request.message)])
    )
    await asyncio.wait_for(entered.wait(), 5)
    await downgrade(database, gm.actor.id, campaign["id"])
    release.set()
    built = await task
    assert secret["content"] not in " ".join(m.model_dump_json() for m in built.messages)


async def test_player_session_views_do_not_expose_hidden_active_location(database, settings):
    service, gm, player, _, campaign, _, _, _, _, _ = await campaign_fixture(database, settings)
    location = await service.create_entry(
        gm,
        campaign["id"],
        CampaignEntryCreate(
            kind=CampaignEntryKind.LOCATION,
            name="Hidden vault",
            content="HIDDEN_LOCATION_TEXT",
            visibility=CampaignVisibility.GM_SECRET,
        ),
    )
    game_session = await service.create_session(
        gm,
        campaign["id"],
        CampaignSessionCreate(title="A session", active_location_id=location["id"]),
    )
    scene = await service.scene_packet(player, campaign["id"], game_session["id"])
    sessions = await service.list_sessions(player, campaign["id"])
    assert scene["session"]["active_location_id"] is None
    assert location["id"] not in json.dumps(sessions)


async def test_public_response_slots_are_separate_from_authenticated_work(settings):
    gate = Ingress(None, settings, SimpleNamespace(healthy=True))
    release = asyncio.Event()

    async def target(scope, receive, send):
        if scope["path"] == "/":
            await release.wait()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    gate.app = target

    async def receive():
        raise AssertionError("GET must not wait for a request body")

    async def ignore(message):
        pass

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "headers": [(b"host", b"test")],
    }
    requests = [asyncio.create_task(gate(dict(scope), receive, ignore)) for _ in range(4)]
    await asyncio.sleep(0)
    output = []

    async def capture(message):
        output.append(message)

    authorized = {
        **scope,
        "path": "/api/settings",
        "headers": [
            *scope["headers"],
            (b"authorization", b"Bearer " + settings.auth_token.get_secret_value().encode()),
        ],
    }
    try:
        assert gate.public_active == 4
        await gate(authorized, receive, capture)
        assert output[0]["status"] == 200
    finally:
        release.set()
        await asyncio.gather(*requests)
    assert gate.active == gate.public_active == 0


async def test_campaign_revocation_withholds_derived_prose_and_arguments(database, settings):
    from jarvis.context import scene_fingerprint

    service, gm, _, _, campaign, game_session, _, _, _, secret = await campaign_fixture(
        database, settings
    )
    old_scene = await service.scene_packet(gm, campaign["id"], game_session["id"])
    await downgrade(database, gm.actor.id, campaign["id"])
    builder = ContextBuilder(
        settings, MemoryService(database, settings, FakeEmbeddingProvider()), service
    )
    request = ChatRequest(
        message="Continue",
        mode=Mode.GAME_MASTER,
        campaign_id=campaign["id"],
        session_id=game_session["id"],
    )
    built = await builder.build(
        gm.actor,
        request,
        [
            Message(role="user", text=request.message),
            Message(role="assistant", text=secret["content"]),
            Message(
                role="assistant_tool",
                name="campaign.propose_event",
                call_id="proposal",
                arguments={"summary": secret["content"]},
            ),
            Message(
                role="tool",
                name="campaign.propose_event",
                call_id="proposal",
                text=ToolOutput(data={"summary": secret["content"]}).model_dump_json(),
            ),
        ],
        previous_scene_fingerprint=scene_fingerprint(old_scene),
    )
    assert secret["content"] not in " ".join(m.model_dump_json() for m in built.messages)
    assert [m.call_id for m in built.messages if m.role in {"assistant_tool", "tool"}] == [
        "proposal",
        "proposal",
    ]
    # The original durable history remains retained. Its cutoff must survive another
    # model step or a resumed run, rather than trusting only the newest fingerprint.
    again = await builder.build(
        gm.actor,
        request,
        [
            Message(role="user", text=request.message),
            Message(role="assistant", text=secret["content"]),
            Message(
                role="assistant_tool",
                name="campaign.propose_event",
                call_id="proposal",
                arguments={"summary": secret["content"]},
            ),
            Message(
                role="tool",
                name="campaign.propose_event",
                call_id="proposal",
                text=ToolOutput(data={"summary": secret["content"]}).model_dump_json(),
            ),
            Message(role="assistant", text="NEW_PLAYER_VISIBLE_CONTENT"),
        ],
        previous_scene_fingerprint=scene_fingerprint(built.scene_packet),
        scene_history_cutoff=built.scene_history_cutoff,
    )
    serialized = " ".join(m.model_dump_json() for m in again.messages)
    assert secret["content"] not in serialized
    assert "NEW_PLAYER_VISIBLE_CONTENT" in serialized
    legacy = await builder.build(
        gm.actor,
        request,
        [
            Message(role="user", text=request.message),
            Message(role="assistant", text=secret["content"]),
        ],
    )
    assert secret["content"] not in " ".join(m.model_dump_json() for m in legacy.messages)
