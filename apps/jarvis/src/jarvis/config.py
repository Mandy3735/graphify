from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JARVIS_", env_file=".env", extra="ignore")

    auth_token: SecretStr
    actor_id: UUID = UUID("afce9806-1dc4-4376-982b-74480ae698aa")
    database_url: SecretStr
    provider: Literal["fake", "openai"] = "fake"
    primary_reasoning_model: str = "gpt-6-astra"
    fallback_reasoning_model: str = "gpt-6.1-sol"
    utility_model: str = ""
    voice_model: str = "gpt-live-1"
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
        }
    )
    # Per million input/output tokens. Empty means cost is unknown, not zero.
    pricing: dict[str, tuple[float, float]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def embedding_configuration(self):
        if self.embedding_provider == "openai" and not self.embedding_model:
            raise ValueError("An explicit embedding model is required for OpenAI embeddings")
        return self

    @field_validator("auth_token")
    @classmethod
    def token_strength(cls, token: SecretStr) -> SecretStr:
        if len(token.get_secret_value()) < 32:
            raise ValueError("JARVIS_AUTH_TOKEN must have at least 32 characters")
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
