from pathlib import Path

import pytest

from jarvis.config import Settings
from jarvis.db import Base, Database


@pytest.fixture
def settings(tmp_path: Path):
    return Settings(
        auth_token="test-auth-token-with-more-than-32-characters",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'jarvis.db'}",
        project_roots={},
        capabilities=frozenset({"graph.read", "graph.write", "workspace.read", "test.write"}),
        _env_file=None,
    )


@pytest.fixture
async def database(settings):
    db = Database(settings.database_url.get_secret_value())
    async with db.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield db
    await db.dispose()
