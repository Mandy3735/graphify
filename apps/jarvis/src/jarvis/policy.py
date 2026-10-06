import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Risk(StrEnum):
    READ_ONLY = "READ_ONLY"
    REVERSIBLE_WRITE = "REVERSIBLE_WRITE"
    EXTERNAL_WRITE = "EXTERNAL_WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"
    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass(frozen=True)
class Actor:
    id: str
    capabilities: frozenset[str]


class PolicyEngine:
    def evaluate(self, actor: Actor, tool, arguments: dict[str, Any], mode: str) -> Decision:
        if not tool.capabilities <= actor.capabilities or mode not in tool.modes:
            return Decision.DENY
        if tool.risk == Risk.SAFETY_CRITICAL:
            return Decision.DENY
        if tool.risk in {Risk.EXTERNAL_WRITE, Risk.DESTRUCTIVE}:
            return Decision.REQUIRE_APPROVAL
        return Decision.ALLOW


def operation_for(tool, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": tool.name,
        "risk": tool.risk.value,
        "capabilities": sorted(tool.capabilities),
        "version": tool.version,
        "target": str(arguments.get("project_id", arguments.get("target", "internal"))),
        "arguments": arguments,
        "side_effects": tool.side_effects,
    }


def operation_hash(
    operation: dict[str, Any], actor: str, run: str, nonce: str, expires: str
) -> str:
    payload = {
        "operation": operation,
        "actor": actor,
        "run": run,
        "nonce": nonce,
        "expires": expires,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()
