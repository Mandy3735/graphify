"""Strict Game Master API and tool inputs."""

from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from jarvis.domain import StrictModel

ID_PATTERN = r"^[a-zA-Z0-9_-]{1,80}$"


class CampaignRole(StrEnum):
    GM = "GM"
    PLAYER = "PLAYER"


class CampaignVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    PARTY = "PARTY"
    PLAYER_PRIVATE = "PLAYER_PRIVATE"
    GM_SECRET = "GM_SECRET"
    INFERRED = "INFERRED"
    RUMOR = "RUMOR"
    RETIRED = "RETIRED"


class CampaignEntryKind(StrEnum):
    LOCATION = "LOCATION"
    PC = "PC"
    NPC = "NPC"
    LORE = "LORE"
    FACTION = "FACTION"
    ITEM = "ITEM"
    HOOK = "HOOK"
    STATE = "STATE"


class CampaignCreate(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    game_system: str = Field(default="system-neutral", min_length=1, max_length=80)
    rules_plugin: str = Field(default="basic", pattern=ID_PATTERN)
    roll_policy: str = Field(default="personal_play", pattern=ID_PATTERN)


class CampaignMemberCreate(StrictModel):
    actor_id: str = Field(pattern=r"^[a-fA-F0-9-]{36}$")
    role: CampaignRole = CampaignRole.PLAYER
    display_name: str = Field(min_length=1, max_length=120)


class CampaignEntryCreate(StrictModel):
    kind: CampaignEntryKind
    name: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=8000)
    data: dict = Field(default_factory=dict)
    visibility: CampaignVisibility = CampaignVisibility.PARTY
    player_actor_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9-]{36}$")

    @model_validator(mode="after")
    def private_entry_has_player(self):
        if self.visibility == CampaignVisibility.PLAYER_PRIVATE and not self.player_actor_id:
            raise ValueError("PLAYER_PRIVATE entries require player_actor_id")
        if self.kind == CampaignEntryKind.PC and not self.player_actor_id:
            raise ValueError("PC entries require their controlling player_actor_id")
        if len(str(self.data)) > 8000:
            raise ValueError("Entry structured data exceeds budget")
        return self


class CampaignSessionCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    active_location_id: str | None = Field(default=None, max_length=36)


class TranscriptCreate(StrictModel):
    speaker: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    visibility: CampaignVisibility = CampaignVisibility.PARTY
    player_actor_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9-]{36}$")

    @model_validator(mode="after")
    def private_transcript_has_player(self):
        if self.visibility == CampaignVisibility.PLAYER_PRIVATE and not self.player_actor_id:
            raise ValueError("PLAYER_PRIVATE transcript lines require player_actor_id")
        if self.visibility not in {
            CampaignVisibility.PUBLIC,
            CampaignVisibility.PARTY,
            CampaignVisibility.PLAYER_PRIVATE,
            CampaignVisibility.GM_SECRET,
        }:
            raise ValueError("Unsupported transcript visibility")
        return self


class SceneQuery(StrictModel):
    campaign_id: str = Field(max_length=36)
    session_id: str | None = Field(default=None, max_length=36)


class DiceRequest(StrictModel):
    campaign_id: str = Field(max_length=36)
    session_id: str | None = Field(default=None, max_length=36)
    request_id: str = Field(pattern=ID_PATTERN)
    subject_entry_id: str = Field(max_length=36)
    expression: str = Field(min_length=3, max_length=32)
    purpose: str = Field(default="check", min_length=1, max_length=200)


class HumanRollReport(StrictModel):
    total: int = Field(ge=-1000, le=21000)


class DelegationCreate(StrictModel):
    subject_entry_id: str = Field(max_length=36)
    nonce: str = Field(pattern=ID_PATTERN)
    ttl_seconds: int = Field(default=300, ge=30, le=900)


class CampaignChangeAction(StrEnum):
    CREATE = "CREATE"
    RETIRE = "RETIRE"


class CampaignChange(StrictModel):
    action: CampaignChangeAction
    target_entry_id: str | None = Field(default=None, max_length=36)
    entry: CampaignEntryCreate | None = None

    @model_validator(mode="after")
    def complete_change(self):
        if self.action == CampaignChangeAction.CREATE and self.entry is None:
            raise ValueError("CREATE changes require an entry")
        if self.action == CampaignChangeAction.RETIRE and self.target_entry_id is None:
            raise ValueError("RETIRE changes require target_entry_id")
        if self.action == CampaignChangeAction.CREATE and self.target_entry_id is not None:
            raise ValueError("CREATE changes cannot target an existing entry")
        if self.action == CampaignChangeAction.RETIRE and self.entry is not None:
            raise ValueError("RETIRE changes cannot include replacement content")
        return self


class CampaignProposalCreate(StrictModel):
    campaign_id: str = Field(max_length=36)
    session_id: str | None = Field(default=None, max_length=36)
    summary: str = Field(min_length=1, max_length=500)
    changes: list[CampaignChange] = Field(min_length=1, max_length=16)

    @field_validator("changes")
    @classmethod
    def bounded_changes(cls, value):
        if len(str([item.model_dump(mode="json") for item in value])) > 32000:
            raise ValueError("Campaign proposal exceeds budget")
        return value


class ProposalDecision(StrictModel):
    approve: bool
