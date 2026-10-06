"""Offline embeddings are deterministic test data, not a live semantic model."""

import asyncio
import hashlib
import math
import re
from typing import Protocol

from jarvis.config import Settings
from jarvis.models import ProviderFailure


def terms(text: str) -> set[str]:
    # Bound work even for operator-supplied fixtures and non-ASCII text.
    return set(re.findall(r"\w{2,64}", text.lower()[:16000]))


def checked_vector(values, dimensions: int) -> list[float]:
    try:
        result = [float(v) for v in values]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProviderFailure("invalid_embedding") from exc
    if len(result) != dimensions or any(not math.isfinite(v) for v in result):
        raise ProviderFailure("invalid_embedding")
    norm = math.sqrt(sum(v * v for v in result))
    if not math.isfinite(norm) or norm == 0:
        raise ProviderFailure("invalid_embedding")
    return [v / norm for v in result]


class EmbeddingProvider(Protocol):
    key: str
    dimensions: int

    async def embed(self, text: str) -> list[float]: ...


class FakeEmbeddingProvider:
    # Small aliases exercise semantic retrieval deterministically without payment.
    aliases = {"automobile": "car", "vehicle": "car", "repair": "fix", "repairs": "fix"}

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions
        self.key = f"fake:hashed-terms-v1:{dimensions}"

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = terms(text) or {"empty"}
        for term in sorted(tokens):
            token = self.aliases.get(term, term)
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0
        if not any(vector):
            vector[0] = 1.0
        return checked_vector(vector, self.dimensions)


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings, client=None):
        self.settings, self.client = settings, client
        self.dimensions = settings.embedding_dimensions
        self.key = f"openai:{settings.embedding_model}:{self.dimensions}"

    async def embed(self, text: str) -> list[float]:
        from openai import AsyncOpenAI

        try:
            if self.client is None:
                self.client = AsyncOpenAI(timeout=self.settings.model_timeout, max_retries=0)
            async with asyncio.timeout(self.settings.model_timeout):
                response = await self.client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=text,
                    dimensions=self.dimensions,
                    encoding_format="float",
                )
            return checked_vector(response.data[0].embedding, self.dimensions)
        except ProviderFailure:
            raise
        except Exception as exc:
            # Never include SDK headers, request contents or credentials in API errors.
            raise ProviderFailure("embedding_provider_failed") from exc

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()


def embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    return FakeEmbeddingProvider(settings.embedding_dimensions)
