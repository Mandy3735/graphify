"""Bound HTTP work before parsing, authentication audits or database/provider work."""

import asyncio
import json
import logging
import secrets
import time
from collections import OrderedDict, deque
from urllib.parse import urlsplit

from jarvis.config import Settings


class Ingress:
    def __init__(self, app, cfg: Settings, runtime):
        self.app, self.cfg, self.runtime = app, cfg, runtime
        self.authenticated: deque[float] = deque()
        self.public: deque[float] = deque()
        self.peers: OrderedDict[str, deque[float]] = OrderedDict()
        self.active = 0
        self.public_active = 0

    def allow(self, bucket: deque[float], limit: int) -> bool:
        current = time.monotonic()
        while bucket and bucket[0] <= current - 60:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(current)
        return True

    async def reject(self, send, status: int, message: str):
        body = json.dumps({"detail": message}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            (b"cache-control", b"no-store"),
        ]
        if status == 429:
            headers.append((b"retry-after", b"60"))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        for header in [b"host", b"authorization", b"origin", b"content-length"]:
            if sum(k == header for k, _ in scope["headers"]) > 1:
                return await self.reject(send, 400, "Ambiguous request headers")
        scheme = scope.get("scheme", "http")
        host = headers.get(b"host", b"").decode("latin1").lower()
        if self.cfg.public_origin and host != urlsplit(self.cfg.public_origin).netloc:
            return await self.reject(send, 400, "Host not allowed")
        if self.cfg.environment == "production" and scheme != "https":
            # Only Uvicorn's explicitly trusted proxy may set the ASGI scheme.
            return await self.reject(send, 400, "HTTPS required")
        origin = headers.get(b"origin")
        expected = self.cfg.public_origin or f"{scheme}://{host}"
        if origin is not None and origin.decode("latin1").lower() != expected:
            return await self.reject(send, 403, "Origin not allowed")
        api = scope["path"].startswith("/api/")
        if api and not self.runtime.healthy:
            return await self.reject(send, 503, "Runtime lease unavailable")
        authorization = headers.get(b"authorization", b"")
        authenticated = len(authorization) <= 520 and secrets.compare_digest(
            authorization, b"Bearer " + self.cfg.auth_token.get_secret_value().encode()
        )
        if api or scope["path"] == "/health":
            if authenticated:
                allowed = self.allow(self.authenticated, self.cfg.api_requests_per_minute)
            else:
                peer = str((scope.get("client") or ("unknown",))[0])
                bucket = self.peers.setdefault(peer, deque())
                self.peers.move_to_end(peer)
                while len(self.peers) > 128:
                    self.peers.popitem(last=False)
                allowed = self.allow(self.public, 120) and self.allow(
                    bucket, self.cfg.unauthenticated_requests_per_minute
                )
            if not allowed:
                return await self.reject(send, 429, "Request budget reached")
            if api and not authenticated:
                return await self.reject(send, 401, "Bearer authentication required")
        method = scope.get("method", "GET")
        if not api and method not in {"GET", "HEAD"}:
            return await self.reject(send, 405, "Method not allowed")
        active = self.active if authenticated else self.public_active
        ceiling = self.cfg.concurrent_http_requests if authenticated else 4
        if active >= ceiling:
            return await self.reject(send, 429, "Concurrent request budget reached")
        # Audio has a dedicated wire ceiling. All other endpoints share a smaller bound.
        maximum = 2_700_000 if scope["path"] == "/api/voice/transcribe" else self.cfg.request_bytes
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await self.reject(send, 400, "Invalid content length")
        if length < 0 or length > maximum:
            return await self.reject(send, 413, "Request exceeds byte budget")
        bodyless = method in {"GET", "HEAD"}
        if bodyless and (length or b"transfer-encoding" in headers):
            return await self.reject(send, 400, "Request body not allowed")
        if authenticated:
            self.active += 1
        else:
            self.public_active += 1
        try:
            body = bytearray()
            try:
                async with asyncio.timeout(self.cfg.request_body_timeout):
                    while not bodyless:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        body.extend(message.get("body", b""))
                        if len(body) > maximum:
                            return await self.reject(send, 413, "Request exceeds byte budget")
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await self.reject(send, 408, "Request body timed out")
            delivered = False

            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            started, finished = False, False

            async def guarded_send(message):
                nonlocal started, finished
                if message["type"] == "http.response.start":
                    started = True
                if message["type"] == "http.response.body" and not message.get("more_body", False):
                    finished = True
                await send(message)

            try:
                await self.app(scope, replay, guarded_send)
            except Exception as exc:
                if self.cfg.environment != "production":
                    raise
                logging.getLogger(__name__).error("Request failed (%s)", type(exc).__name__)
                if not started:
                    await self.reject(send, 500, "Internal service error")
                elif not finished:
                    await send({"type": "http.response.body", "body": b"", "more_body": False})
        finally:
            if authenticated:
                self.active -= 1
            else:
                self.public_active -= 1
