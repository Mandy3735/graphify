from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from jarvis.web_ui import install_web_ui


@pytest.mark.asyncio
async def test_static_shell_allowlist_and_security_headers(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html>shell</html>")
    (tmp_path / "sw.js").write_text("// static only")
    (tmp_path / "secret.txt").write_text("PRIVATE")
    app = FastAPI()

    @app.get("/api/private")
    async def private():
        return {"private": "response"}

    install_web_ui(app, tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        for path in ["/", "/chat", "/engineer/graph", "/gm", "/settings"]:
            response = await client.get(path)
            assert response.status_code == 200
            assert "shell" in response.text
        for path in ["/api/missing", "/secret.txt", "/assets/../../secret.txt", "/unknown"]:
            assert (await client.get(path)).status_code == 404
        docs = await client.get("/docs")
        assert docs.status_code == 200
        assert "swagger-ui" in docs.text
        assert "content-security-policy" not in docs.headers
        assert docs.headers["cache-control"] == "no-store"
        for path in ["/", "/api/private", "/api/missing", "/sw.js"]:
            response = await client.get(path)
            assert response.headers["cache-control"] == "no-store"
            csp = response.headers["content-security-policy"]
            assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
            assert "frame-ancestors 'none'" in csp
            assert response.headers["referrer-policy"] == "no-referrer"
            assert response.headers["x-content-type-options"] == "nosniff"
            assert "microphone=()" in response.headers["permissions-policy"]


@pytest.mark.asyncio
async def test_unbuilt_shell_fails_explicitly(tmp_path: Path):
    app = FastAPI()
    install_web_ui(app, tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 503
        assert "not built" in response.text
