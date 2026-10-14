import math
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JARVIS_", env_file=".env", extra="ignore")

    auth_token: SecretStr
    actor_id: UUID = UUID("afce9806-1dc4-4376-982b-74480ae698aa")
    database_url: SecretStr
    environment: Literal["local", "production"] = "local"
    public_origin: str = ""
    request_bytes: int = Field(default=262144, ge=16384, le=1048576)
    request_body_timeout: float = Field(default=10, ge=1, le=30)
    api_requests_per_minute: int = Field(default=600, ge=10, le=1200)
    unauthenticated_requests_per_minute: int = Field(default=30, ge=5, le=120)
    concurrent_http_requests: int = Field(default=16, ge=4, le=64)
    provider_daily_budget_usd: float = Field(default=25, gt=0, le=1000)
    # Upper estimates per operation/model, e.g. "speech:configured-model": 0.10.
    provider_operation_costs: dict[str, float] = Field(default_factory=dict)
    provider: Literal["fake", "openai"] = "fake"
    primary_reasoning_model: str = "gpt-6-astra"
    fallback_reasoning_model: str = "gpt-6.1-sol"
    utility_model: str = ""
    voice_model: str = "gpt-live-1"
    voice_provider: Literal["disabled", "fake", "openai"] = "disabled"
    transcription_model: str = ""
    speech_model: str = ""
    speech_voice: str = "alloy"
    voice_session_seconds: int = Field(default=120, ge=15, le=300)
    embedding_model: str = ""
    embedding_provider: Literal["fake", "openai"] = "fake"
    embedding_dimensions: int = Field(default=64, ge=16, le=3072)
    memory_pgvector: bool = False
    memory_candidates: int = Field(default=128, ge=16, le=512)
    memory_context_tokens: int = Field(default=4000, ge=0, le=16000)
    context_token_budget: int = Field(default=24000, ge=1000, le=64000)
    working_memory_ttl: int = Field(default=3600, ge=60, le=86400)
    reasoning_effort: Literal["low", "medium", "high"] = "medium"
    allow_fallback: bool = False
    model_timeout: float = Field(default=30, gt=0, le=120)
    stream_responses: bool = True
    tool_timeout: float = Field(default=60, gt=0, le=180)
    run_timeout: float = Field(default=240, gt=0, le=600)
    max_tool_calls: int = Field(default=8, ge=1, le=32)
    max_output_tokens: int = Field(default=2000, ge=64, le=8000)
    context_chars: int = Field(default=24000, ge=1000, le=64000)
    approval_ttl: int = Field(default=900, ge=30, le=3600)
    project_roots: dict[str, Path] = Field(default_factory=dict)
    engineer_enabled: bool = False
    engineer_state_dir: Path | None = None
    sandbox_timeout: float = Field(default=15, ge=1, le=30)
    sandbox_memory_mb: int = Field(default=256, ge=64, le=512)
    sandbox_processes: int = Field(default=24, ge=8, le=48)
    sandbox_output_bytes: int = Field(default=8192, ge=1024, le=16384)
    capabilities: frozenset[str] = frozenset(
        {
            "graph.read",
            "workspace.read",
            "memory.read",
            "memory.write",
            "memory.propose",
            "tutor.read",
            "tutor.write",
            "tutor.attempt",
            "campaign.read",
            "campaign.write",
            "campaign.dice",
            "campaign.delegate",
            "campaign.propose",
            "campaign.approve",
            "campaign.transcript",
        }
    )
    # Per million input/output tokens. Empty means cost is unknown, not zero.
    pricing: dict[str, tuple[float, float]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def production_configuration(self):
        if (
            not math.isfinite(self.provider_daily_budget_usd)
            or any(
                not math.isfinite(rate) or rate < 0
                for pair in self.pricing.values()
                for rate in pair
            )
            or any(
                not math.isfinite(rate) or rate <= 0
                for rate in self.provider_operation_costs.values()
            )
        ):
            raise ValueError("Provider budget/pricing must be finite nonnegative amounts")
        if self.public_origin:
            origin = urlsplit(self.public_origin)
            if (
                origin.scheme not in {"http", "https"}
                or not origin.hostname
                or origin.username
                or origin.password
                or origin.path
                or origin.query
                or origin.fragment
                or any(ord(c) < 33 or ord(c) > 126 for c in self.public_origin)
            ):
                raise ValueError("Public origin must be an exact HTTP(S) origin without a path")
            _ = origin.port  # Validate a supplied port before accepting the deployment origin.
            self.public_origin = self.public_origin.lower()
        if self.environment == "production":
            if (
                not self.database_url.get_secret_value().startswith("postgresql+asyncpg://")
                or not self.public_origin.startswith("https://")
                or len(self.auth_token.get_secret_value()) < 48
            ):
                raise ValueError(
                    "Production requires PostgreSQL, exact HTTPS origin and 48+ token characters"
                )
        return self

    @field_validator("voice_provider", mode="before")
    @classmethod
    def optional_voice_provider(cls, value):
        # Bad optional transport configuration must not disable the text application.
        return value if value in {"disabled", "fake", "openai"} else "disabled"

    @field_validator("voice_session_seconds", mode="before")
    @classmethod
    def optional_voice_duration(cls, value):
        try:
            seconds = int(value)
        except (TypeError, ValueError, OverflowError):
            return 120
        return seconds if 15 <= seconds <= 300 else 120

    @model_validator(mode="after")
    def embedding_configuration(self):
        if self.embedding_provider == "openai" and not self.embedding_model:
            raise ValueError("An explicit embedding model is required for OpenAI embeddings")
        return self

    @field_validator("auth_token")
    @classmethod
    def token_strength(cls, token: SecretStr) -> SecretStr:
        value = token.get_secret_value()
        if not 32 <= len(value) <= 512 or any(ord(c) < 33 or ord(c) > 126 for c in value):
            raise ValueError("JARVIS_AUTH_TOKEN needs 32–512 printable non-space ASCII characters")
        return token

    @field_validator("project_roots")
    @classmethod
    def resolve_roots(cls, roots: dict[str, Path]) -> dict[str, Path]:
        for key, path in roots.items():
            if not key.isidentifier() or not path.is_dir():
                raise ValueError(
                    "Project registrations need identifier IDs and existing directories"
                )
        return {key: path.resolve() for key, path in roots.items()}
