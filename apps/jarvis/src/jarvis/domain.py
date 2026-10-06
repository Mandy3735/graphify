from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Mode(StrEnum):
    CHIEF_OF_STAFF = "CHIEF_OF_STAFF"
    TUTOR = "TUTOR"
    ENGINEER = "ENGINEER"
    GAME_MASTER = "GAME_MASTER"


class RunState(StrEnum):
    RECEIVED = "RECEIVED"
    CONTEXT_BUILDING = "CONTEXT_BUILDING"
    PLANNING = "PLANNING"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    EXECUTING_TOOL = "EXECUTING_TOOL"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL = {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}
TRANSITIONS = {
    RunState.RECEIVED: {RunState.CONTEXT_BUILDING},
    RunState.CONTEXT_BUILDING: {RunState.PLANNING},
    RunState.PLANNING: {RunState.WAITING_FOR_TOOL, RunState.VERIFYING},
    RunState.WAITING_FOR_TOOL: {RunState.WAITING_FOR_APPROVAL, RunState.EXECUTING_TOOL},
    RunState.WAITING_FOR_APPROVAL: {RunState.EXECUTING_TOOL},
    RunState.EXECUTING_TOOL: {RunState.PLANNING},
    RunState.VERIFYING: {RunState.COMPLETED},
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolProposal(StrictModel):
    name: str = Field(max_length=128)
    arguments: dict[str, Any]
    call_id: str = Field(default="", max_length=128)


class ModelResult(StrictModel):
    text: str = ""
    tools: list[ToolProposal] = Field(default_factory=list, max_length=1)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)


class Message(StrictModel):
    role: str
    text: str = ""
    name: str = ""
    call_id: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=12000)
    mode: Mode = Mode.CHIEF_OF_STAFF
    project_id: str | None = Field(default=None, max_length=80)
    allow_fallback: bool = False
    high_stakes: bool = False
    utility: bool = False


class ToolOutput(StrictModel):
    data: dict[str, Any]
    trust: str = "UNTRUSTED_DATA"
