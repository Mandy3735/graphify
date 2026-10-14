"""Optional transport providers. Voice has no application tools or canonical authority."""

import asyncio
import io
import re
import wave
from dataclasses import dataclass
from typing import Protocol

from jarvis.config import Settings


class VoiceUnavailable(Exception):
    """Public errors must never contain provider bodies, audio or credentials."""


@dataclass(frozen=True)
class VoiceCall:
    provider_id: str
    answer: str


class VoiceProvider(Protocol):
    async def connect(self, offer: str) -> VoiceCall: ...
    async def stop(self, call: VoiceCall) -> None: ...
    async def speak(self, text: str) -> bytes: ...
    async def close(self) -> None: ...


class TranscriptionProvider(Protocol):
    async def transcribe(self, audio: bytes, format: str) -> str: ...


class FakeVoiceProvider:
    """Offline lifecycle fixture; no device/network, explicitly synthetic audio."""

    async def connect(self, offer: str) -> VoiceCall:
        return VoiceCall("fake", "")

    async def stop(self, call: VoiceCall) -> None:
        pass

    async def speak(self, text: str) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as recording:
            recording.setnchannels(1)
            recording.setsampwidth(2)
            recording.setframerate(8000)
            recording.writeframes(b"\x00\x00" * 800)
        return output.getvalue()

    async def close(self) -> None:
        pass


class FakeTranscriptionProvider:
    async def transcribe(self, audio: bytes, format: str) -> str:
        return "[Fake transcription] Please describe the current project."


class OpenAILiveVoiceProvider:
    """Official SDK SDP relay: the browser receives no provider credential."""

    def __init__(self, settings: Settings, client=None):
        self.settings, self.client = settings, client

    def sdk(self):
        from openai import AsyncOpenAI

        if self.client is None:
            # Lazy construction ensures missing voice credentials never block text startup.
            self.client = AsyncOpenAI(timeout=self.settings.model_timeout, max_retries=0)
        return self.client

    async def connect(self, offer: str) -> VoiceCall:
        if not self.settings.voice_model or not self.settings.transcription_model:
            raise VoiceUnavailable()
        try:
            async with asyncio.timeout(self.settings.model_timeout):
                response = await self.sdk().realtime.calls.create(
                    sdp=offer,
                    session={
                        "type": "realtime",
                        "model": self.settings.voice_model,
                        "instructions": "Capture speech only. Backend handles reasoning.",
                        "tools": [],
                        "tool_choice": "none",
                        "output_modalities": ["text"],
                        "max_output_tokens": 64,
                        "audio": {
                            "input": {
                                "transcription": {"model": self.settings.transcription_model},
                                "turn_detection": {
                                    "type": "server_vad",
                                    "create_response": False,
                                    "interrupt_response": False,
                                },
                            }
                        },
                    },
                )
            location = response.response.headers.get("location", "")
            provider_id = location.rsplit("/", 1)[-1]
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", provider_id):
                raise VoiceUnavailable()
            answer = response.text
            if not answer.startswith("v=0") or len(answer) > 64000:
                await self.stop(VoiceCall(provider_id, ""))
                raise VoiceUnavailable()
            return VoiceCall(provider_id, answer)
        except Exception as exc:
            raise VoiceUnavailable() from exc

    async def stop(self, call: VoiceCall) -> None:
        from openai import APIStatusError

        try:
            async with asyncio.timeout(self.settings.model_timeout):
                await self.sdk().realtime.calls.hangup(call.provider_id)
        except APIStatusError as exc:
            if exc.status_code not in {404, 410}:
                raise VoiceUnavailable() from exc
        except Exception as exc:
            raise VoiceUnavailable() from exc

    async def speak(self, text: str) -> bytes:
        if not self.settings.speech_model:
            raise VoiceUnavailable()
        try:
            async with asyncio.timeout(self.settings.model_timeout):
                # Stream with a byte ceiling rather than buffering arbitrary provider output.
                async with self.sdk().audio.speech.with_streaming_response.create(
                    model=self.settings.speech_model,
                    voice=self.settings.speech_voice,
                    input=text,
                    response_format="wav",
                ) as response:
                    output = bytearray()
                    async for part in response.iter_bytes():
                        output.extend(part)
                        if len(output) > 2_000_000:
                            raise VoiceUnavailable()
            if not output.startswith(b"RIFF") or output[8:12] != b"WAVE":
                raise VoiceUnavailable()
            return bytes(output)
        except Exception as exc:
            raise VoiceUnavailable() from exc

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()


class OpenAITranscriptionProvider:
    def __init__(self, voice: OpenAILiveVoiceProvider):
        self.voice = voice

    async def transcribe(self, audio: bytes, format: str) -> str:
        if not self.voice.settings.transcription_model:
            raise VoiceUnavailable()
        try:
            async with asyncio.timeout(self.voice.settings.model_timeout):
                result = await self.voice.sdk().audio.transcriptions.create(
                    model=self.voice.settings.transcription_model,
                    file=(f"capture.{format}", audio),
                    response_format="json",
                )
            text = result.text
            if not isinstance(text, str) or not 0 < len(text) <= 11000:
                raise VoiceUnavailable()
            return text
        except Exception as exc:
            raise VoiceUnavailable() from exc
