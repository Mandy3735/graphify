"""Disposable browser-test host. Fake providers; no development state or live keys."""

import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI

from jarvis.api import create_app
from jarvis.config import Settings
from jarvis.db import Base

TOKEN = "phase9-browser-token-more-than-32-characters"
PLAYER_TOKEN = "phase9-player-token-more-than-32-characters"
PLAYER = UUID("57ecb6a8-acde-47aa-993b-ece0551e0b8b")
state = tempfile.TemporaryDirectory(prefix="jarvis-browser-")
database = f"sqlite+aiosqlite:///{Path(state.name) / 'browser.db'}"
test_config = {
    "database_url": database,
    "provider": "fake",
    "embedding_provider": "fake",
    "memory_pgvector": False,
    "engineer_enabled": False,
    "voice_provider": "fake",
    "project_roots": {},
    "capabilities": Settings.model_fields["capabilities"].default,
    "_env_file": None,
}
gm = create_app(
    Settings(auth_token=TOKEN, actor_id=UUID("afce9806-1dc4-4376-982b-74480ae698aa"), **test_config)
)
player = create_app(Settings(auth_token=PLAYER_TOKEN, actor_id=PLAYER, **test_config))


@asynccontextmanager
async def lifespan(app):
    async with gm.state.database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with gm.router.lifespan_context(gm), player.router.lifespan_context(player):
        yield
    state.cleanup()


host = FastAPI(lifespan=lifespan)


@host.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
async def unused():
    raise AssertionError("ASGI wrapper dispatches HTTP directly")


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        return await host(scope, receive, send)
    # Test-only two-identity host; production uses its existing single-token auth.
    headers = dict(scope.get("headers", []))
    target = player if headers.get(b"authorization") == f"Bearer {PLAYER_TOKEN}".encode() else gm
    return await target(scope, receive, send)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("JARVIS_BROWSER_PORT", "8765")),
        log_level="warning",
        access_log=False,
    )
