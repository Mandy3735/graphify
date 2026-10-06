"""Memory data is inspectable, source attributed, and never permission authority."""

import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from jarvis.domain import Mode, StrictModel

NAMESPACE_PATTERN = r"^(personal|(?:project|campaign|session):[a-zA-Z0-9_-]{1,80})$"


class MemoryClass(StrEnum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    CANONICAL = "CANONICAL"
    PREFERENCE = "PREFERENCE"


class Visibility(StrEnum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    PARTY = "PARTY"
    PLAYER_PRIVATE = "PLAYER_PRIVATE"
    GM_SECRET = "GM_SECRET"
    INFERRED = "INFERRED"
    RUMOR = "RUMOR"
    RETIRED = "RETIRED"


class SourceKind(StrEnum):
    USER_NOTE = "USER_NOTE"
    DOCUMENT = "DOCUMENT"
    CONVERSATION = "CONVERSATION"
    OBSERVATION = "OBSERVATION"
    IMPORT = "IMPORT"
    MODEL_PROPOSAL = "MODEL_PROPOSAL"


class SourceInput(StrictModel):
    kind: SourceKind
    locator: str = Field(min_length=1, max_length=300)
    quote: str = Field(default="", max_length=500)


class MemoryCreate(StrictModel):
    memory_class: MemoryClass = MemoryClass.SEMANTIC
    namespace: str = Field(default="personal", pattern=NAMESPACE_PATTERN)
    visibility: Visibility = Visibility.PRIVATE
    mode: Mode | None = None
    content: str = Field(min_length=1, max_length=4000)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceInput] = Field(min_length=1, max_length=8)
    expires_at: datetime | None = None

    @field_validator("structured_data")
    @classmethod
    def bounded_data(cls, value):
        try:
            encoded = json.dumps(value, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as exc:
            raise ValueError("Memory data must be finite JSON") from exc
        if len(encoded.encode()) > 4096:
            raise ValueError("Structured memory data exceeds its byte budget")
        return value

    @field_validator("expires_at")
    @classmethod
    def aware_expiry(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Memory expiry must include a timezone")
        return value

    @model_validator(mode="after")
    def class_contract(self):
        if self.memory_class == MemoryClass.WORKING and not self.namespace.startswith("session:"):
            raise ValueError("Working memory requires a session namespace")
        if self.memory_class == MemoryClass.CANONICAL and not self.structured_data:
            raise ValueError("Canonical memory requires structured state")
        return self


class MemoryCorrection(StrictModel):
    expected_revision: int = Field(ge=1, le=32)
    content: str = Field(min_length=1, max_length=4000)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceInput] = Field(min_length=1, max_length=8)

    @field_validator("structured_data")
    @classmethod
    def bounded_data(cls, value):
        return MemoryCreate.bounded_data(value)


class MemorySearch(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    namespace: str = Field(default="personal", pattern=NAMESPACE_PATTERN)
    mode: Mode = Mode.CHIEF_OF_STAFF
    limit: int = Field(default=10, ge=1, le=50)


EDITABLE = frozenset({MemoryClass.WORKING, MemoryClass.SEMANTIC, MemoryClass.PREFERENCE})
