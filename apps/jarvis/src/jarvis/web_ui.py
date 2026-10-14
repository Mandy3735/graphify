"""Same-origin static application shell; API content is never a cacheable asset."""

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
    "font-src 'self'; connect-src 'self'; media-src blob:; worker-src 'self'; manifest-src 'self'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
)
SPA = re.compile(
    r"(?:chat|missions|projects|memory|approvals|engineer(?:/graph)?|tutor|"
    r"gm(?:/[a-fA-F0-9-]{36}(?:/session)?)?|settings)?"
)


def install_web_ui(app: FastAPI, directory: Path | None = None) -> None:
    root = directory or Path(__file__).parent / "web"

    @app.middleware("http")
    async def browser_boundary(request: Request, call_next):
        response = await call_next(request)
        # Preserve FastAPI's optional developer docs and their existing asset policy.
        # The product shell/assets/API retain the restrictive browser boundary.
        if request.url.path not in {"/docs", "/redoc", "/docs/oauth2-redirect"}:
            response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        voice = getattr(app.state, "voice", None)
        microphone = (
            "(self)"
            if (
                voice
                and voice.cfg.voice_provider == "openai"
                and voice.cfg.environment != "production"
            )
            else "()"
        )
        response.headers["Permissions-Policy"] = (
            f"microphone={microphone}, camera=(), geolocation=()"
        )
        response.headers["X-Frame-Options"] = "DENY"
        # The service worker caches a finite build-generated static allowlist only.
        # All ordinary HTTP responses, including authentication errors, are no-store.
        response.headers["Cache-Control"] = "no-store"
        if voice and voice.cfg.environment == "production" and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/{web_path:path}", include_in_schema=False)
    async def web_shell(web_path: str):
        if web_path.startswith(("api/", "health", "docs", "openapi")):
            raise HTTPException(404, "Resource not found")
        if not (root / "index.html").is_file():
            raise HTTPException(503, "Command Center not built; run npm ci and npm run build")
        if SPA.fullmatch(web_path):
            return FileResponse(root / "index.html")
        if web_path in {"sw.js", "icon.svg", "manifest.webmanifest"} or re.fullmatch(
            r"assets/[a-zA-Z0-9_-]+\.(?:js|css)", web_path
        ):
            target = root / web_path
            if target.is_file() and not target.is_symlink():
                return FileResponse(target)
        raise HTTPException(404, "Resource not found")
