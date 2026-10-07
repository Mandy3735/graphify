"""Bounded changes and commands; neither paths nor text can confer authority."""

from pydantic import Field, field_validator

from jarvis.domain import StrictModel
from jarvis.paths import TEXT_SUFFIXES, parts


class Edit(StrictModel):
    path: str = Field(min_length=1, max_length=200)
    content: str = Field(max_length=4000)
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    reason: str = Field(min_length=1, max_length=300)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value):
        from pathlib import Path

        parts(value)
        if Path(value).suffix.lower() not in TEXT_SUFFIXES or value.startswith("graphify-out/"):
            raise ValueError("Only non-secret source/document text edits are supported")
        return value


class Command(StrictModel):
    argv: list[str] = Field(min_length=1, max_length=16)
    purpose: str = Field(min_length=1, max_length=200)

    @field_validator("argv")
    @classmethod
    def bounded_argv(cls, argv):
        # Phase 6 intentionally supports the system Python standard-library runtime.
        import json

        if (
            argv[0] != "python3"
            or len(json.dumps(argv)) > 6000
            or any(len(a) > 4000 or "\x00" in a for a in argv)
        ):
            raise ValueError("Commands require python3 and bounded literal arguments")
        return argv


class ChangeRequest(StrictModel):
    project_id: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=1200)
    acceptance_criteria: list[str] = Field(min_length=1, max_length=4)
    edits: list[Edit] = Field(min_length=1, max_length=4)
    commands: list[Command] = Field(min_length=1, max_length=3)
    dry_run: bool = False

    @field_validator("acceptance_criteria")
    @classmethod
    def criteria_limit(cls, value):
        if any(not x or len(x) > 300 for x in value):
            raise ValueError("Acceptance criteria must be bounded nonempty text")
        return value


class SandboxRequest(StrictModel):
    project_id: str = Field(min_length=1, max_length=80)
    command: Command
