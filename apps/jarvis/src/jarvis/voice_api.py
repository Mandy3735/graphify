"""Authenticated, bounded voice transport; reviewed transcripts use the run engine."""

import asyncio
import base64
import binascii
import io
import time
import wave
from collections import deque
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import select

from jarvis.budgets import BudgetExceeded
from jarvis.config import Settings
from jarvis.db import AgentRun, VoiceSession, audit
from jarvis.domain import ChatRequest, StrictModel
from jarvis.voice import (
    FakeTranscriptionProvider,
    FakeVoiceProvider,
    OpenAILiveVoiceProvider,
    OpenAITranscriptionProvider,
    VoiceCall,
    VoiceUnavailable,
)


class Offer(StrictModel):
    sdp: str = Field(default="", max_length=64000)


class AudioInput(StrictModel):
    audio: str = Field(min_length=1, max_length=2_666_668)
    format: Literal["wav"]


class SpeechInput(StrictModel):
    run_id: str = Field(pattern=r"^[a-f0-9-]{36}$")


class ReconcileInput(StrictModel):
    remote_stopped: Literal[True]


class VoiceService:
    def __init__(self, settings: Settings, engine, provider=None, transcription=None):
        self.cfg, self.engine = settings, engine
        self.provider = provider or (
            OpenAILiveVoiceProvider(settings)
            if settings.voice_provider == "openai"
            else FakeVoiceProvider()
        )
        self.transcription = transcription or (
            OpenAITranscriptionProvider(self.provider)
            if isinstance(self.provider, OpenAILiveVoiceProvider)
            else FakeTranscriptionProvider()
        )
        self.lock = asyncio.Lock()
        self.sessions: dict[str, tuple[VoiceCall, asyncio.Task]] = {}
        self.admissions: deque[float] = deque()
        self.recovery_task: asyncio.Task | None = None

    def require_enabled(self):
        if self.cfg.voice_provider == "disabled":
            raise HTTPException(503, "Voice disabled; text remains available")

    def admit(self):
        self.require_enabled()
        now = time.monotonic()
        while self.admissions and self.admissions[0] < now - 3600:
            self.admissions.popleft()
        if len(self.admissions) >= 30:
            raise HTTPException(429, "Voice request budget reached")
        self.admissions.append(now)

    async def record(self, kind: str, detail: dict):
        async with self.engine.db.sessions.begin() as session:
            audit(session, self.engine.actor.id, kind, detail)

    async def session_state(self, key: str, state: str, provider_id: str | None = None):
        async with self.engine.db.sessions.begin() as session:
            row = await session.get(VoiceSession, key)
            if row is not None and row.actor_id == self.engine.actor.id:
                row.state = state
                if provider_id is not None:
                    row.provider_id = provider_id

    async def pending_cleanup(self) -> list[VoiceSession]:
        async with self.engine.db.sessions() as session:
            return list(
                await session.scalars(
                    select(VoiceSession)
                    .where(
                        VoiceSession.actor_id == self.engine.actor.id,
                        VoiceSession.state != "STOPPED",
                    )
                    .order_by(VoiceSession.created_at)
                    .limit(32)
                )
            )

    async def recover(self):
        async with self.lock:
            await self._recover()

    async def _recover(self):
        # Known IDs may be hung up; never recreate a call or replay speech.
        cleanup_provider = OpenAILiveVoiceProvider(self.cfg)
        try:
            async with asyncio.timeout(self.cfg.model_timeout):
                for row in await self.pending_cleanup():
                    if row.id in self.sessions:
                        continue
                    if row.provider == "fake":
                        await self.session_state(row.id, "STOPPED")
                    elif row.provider_id:
                        try:
                            await cleanup_provider.stop(VoiceCall(row.provider_id, ""))
                        except VoiceUnavailable:
                            await self.session_state(row.id, "STOP_FAILED")
                        else:
                            await self.session_state(row.id, "STOPPED")
                            await self.record("voice.recovered", {"session_id": row.id})
                    else:
                        await self.session_state(row.id, "UNRESOLVED")
        except TimeoutError:
            pass
        finally:
            await cleanup_provider.close()

    async def start(self, offer: str):
        if self.lock.locked() or self.sessions:
            raise HTTPException(429, "One voice operation at a time")
        async with self.lock:
            self.admit()
            if self.cfg.voice_provider == "openai" and (
                not offer.startswith("v=0") or "m=audio " not in offer or "m=video " in offer
            ):
                raise HTTPException(422, "Audio-only SDP required")
            if self.cfg.voice_provider == "openai" and (
                not self.cfg.voice_model or not self.cfg.transcription_model
            ):
                raise VoiceUnavailable()
            if self.cfg.voice_provider == "openai" and (
                self.cfg.environment == "production" or await self.pending_cleanup()
            ):
                # WebRTC data channels can alter provider generation settings. A reservation
                # cannot enforce that remote ceiling; production keeps capture disabled.
                raise VoiceUnavailable()
            key = str(uuid4())
            async with self.engine.db.sessions.begin() as session:
                session.add(
                    VoiceSession(
                        id=key,
                        actor_id=self.engine.actor.id,
                        provider=self.cfg.voice_provider,
                        provider_id="",
                        state="CREATING",
                    )
                )
            try:
                if self.cfg.voice_provider == "openai":
                    async with self.engine.budget.operation("realtime", self.cfg.voice_model):
                        call = await self.provider.connect(offer)
                else:
                    call = await self.provider.connect(offer)
            except BudgetExceeded:
                await self.session_state(key, "STOPPED")
                raise
            except BaseException:
                await asyncio.shield(self.session_state(key, "UNRESOLVED"))
                raise
            try:
                await self.session_state(key, "ACTIVE", call.provider_id)
            except BaseException:
                await self.provider.stop(call)
                raise
            task = asyncio.create_task(self.expire(key))
            self.sessions[key] = call, task
            try:
                await self.record(
                    "voice.started", {"session_id": key, "provider": self.cfg.voice_provider}
                )
            except BaseException:
                await self.stop(key)
                raise
            return {"id": key, "sdp": call.answer, "seconds": self.cfg.voice_session_seconds}

    async def expire(self, key: str):
        await asyncio.sleep(self.cfg.voice_session_seconds)
        try:
            await self.stop(key)
        except VoiceUnavailable:
            # A provider outage cannot prevent local device release or text operation.
            pass

    async def stop(self, key: str):
        entry = self.sessions.pop(key, None)
        if entry is None:
            return
        call, task = entry
        if task is not asyncio.current_task():
            task.cancel()
        try:
            await self.provider.stop(call)
        except VoiceUnavailable:
            await self.session_state(key, "STOP_FAILED")
            await self.record("voice.stop_failed", {"session_id": key})
            raise
        else:
            await self.session_state(key, "STOPPED")
            await self.record("voice.stopped", {"session_id": key})

    async def close(self):
        try:
            if self.recovery_task is not None:
                self.recovery_task.cancel()
                await asyncio.gather(self.recovery_task, return_exceptions=True)
            for key in list(self.sessions):
                try:
                    await self.stop(key)
                except VoiceUnavailable:
                    pass
        finally:
            await self.provider.close()


def voice_router(service: VoiceService, auth: list) -> APIRouter:
    router = APIRouter(prefix="/api/voice", dependencies=auth)

    @router.get("/status")
    async def status():
        return {
            "provider": service.cfg.voice_provider,
            "enabled": service.cfg.voice_provider != "disabled",
            "transport": "fake" if service.cfg.voice_provider == "fake" else "webrtc",
            "session_seconds": service.cfg.voice_session_seconds,
            "speech_enabled": service.cfg.voice_provider == "fake"
            or bool(service.cfg.speech_model),
            "realtime_enabled": service.cfg.environment != "production",
            "cleanup_pending": [
                {"id": row.id, "state": row.state}
                for row in await service.pending_cleanup()
                if row.id not in service.sessions
            ],
        }

    @router.post("/sessions/{session_id}/reconcile", status_code=204)
    async def reconcile(session_id: str, request: ReconcileInput):
        rows = await service.pending_cleanup()
        row = next((row for row in rows if row.id == session_id), None)
        if (
            row is None
            or row.id in service.sessions
            or row.state not in {"UNRESOLVED", "STOP_FAILED"}
        ):
            raise HTTPException(409, "Session is not awaiting operator reconciliation")
        await service.session_state(session_id, "STOPPED")
        await service.record("voice.reconciled_by_human", {"session_id": session_id})

    @router.post("/sessions", status_code=201)
    async def start(request: Offer):
        return await service.start(request.sdp)

    @router.delete("/sessions/{session_id}", status_code=204)
    async def stop(session_id: str):
        service.require_enabled()
        await service.stop(session_id)

    @router.post("/transcribe")
    async def transcribe(request: AudioInput):
        if service.lock.locked():
            raise HTTPException(429, "One voice operation at a time")
        async with service.lock:
            service.admit()
            try:
                audio = base64.b64decode(request.audio, validate=True)
            except (ValueError, binascii.Error):
                raise HTTPException(422, "Invalid audio") from None
            if not 12 <= len(audio) <= 2_000_000:
                raise HTTPException(422, "Invalid audio")
            try:
                with wave.open(io.BytesIO(audio), "rb") as capture:
                    channels, width = capture.getnchannels(), capture.getsampwidth()
                    rate, frames = capture.getframerate(), capture.getnframes()
                    if (
                        channels not in {1, 2}
                        or width != 2
                        or not 8000 <= rate <= 48000
                        or not 0 < frames <= rate * 120
                        or capture.getcomptype() != "NONE"
                        or len(capture.readframes(frames)) != frames * channels * width
                    ):
                        raise ValueError("Invalid PCM capture")
            except (wave.Error, EOFError, ValueError):
                raise HTTPException(422, "Bounded PCM WAV required") from None
            if service.cfg.voice_provider == "openai":
                async with service.engine.budget.operation(
                    "transcription", service.cfg.transcription_model
                ):
                    transcript = await service.transcription.transcribe(audio, request.format)
            else:
                transcript = await service.transcription.transcribe(audio, request.format)
            await service.record("voice.transcribed", {"provider": service.cfg.voice_provider})
            return {"text": transcript, "trust": "UNTRUSTED_DATA", "canonical": False}

    @router.post("/submit", status_code=202)
    async def submit(request: ChatRequest):
        service.require_enabled()
        if len(request.message) > 11000:
            raise HTTPException(422, "Transcript too long")
        if len(service.engine.tasks) >= 4:
            raise HTTPException(429, "Concurrent run budget reached")
        # A transcript cannot call a human approval/attempt/roll-report endpoint.
        request = request.model_copy(
            update={
                "message": "[User-reviewed voice transcript; untrusted, noncanonical data]\n"
                + request.message
            }
        )
        run_id = await service.engine.create(request)
        await service.record("voice.delegated", {"run_id": run_id})
        return {"run_id": run_id}

    @router.post("/speech")
    async def speech(request: SpeechInput):
        if service.lock.locked():
            raise HTTPException(429, "One voice operation at a time")
        async with service.lock:
            service.admit()
            async with service.engine.db.sessions() as session:
                run = await session.scalar(
                    select(AgentRun).where(
                        AgentRun.id == request.run_id,
                        AgentRun.actor_id == str(service.engine.actor.id),
                    )
                )
                if run is None:
                    raise HTTPException(404, "Run unavailable")
                if run.state != "COMPLETED" or not run.result:
                    raise HTTPException(409, "Completed result required")
                text = run.result[:4000]
            if service.cfg.voice_provider == "openai":
                async with service.engine.budget.operation("speech", service.cfg.speech_model):
                    audio = await service.provider.speak(text)
            else:
                audio = await service.provider.speak(text)
            await service.record("voice.spoken", {"run_id": request.run_id})
            return {"audio": base64.b64encode(audio).decode(), "format": "wav", "synthetic": True}

    return router
