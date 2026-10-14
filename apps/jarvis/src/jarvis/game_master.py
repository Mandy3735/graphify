"""Canonical campaign state, visibility-first scene packets and roll authority."""

import hashlib
import json
import random
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import and_, or_, select

from jarvis.db import (
    Campaign,
    CampaignEntry,
    CampaignEvent,
    CampaignEventProposal,
    CampaignMember,
    CampaignSession,
    CampaignTranscript,
    Database,
    DiceRoll,
    RollDelegation,
    audit,
    now,
)
from jarvis.game_master_schema import (
    CampaignChangeAction,
    CampaignCreate,
    CampaignEntryCreate,
    CampaignMemberCreate,
    CampaignProposalCreate,
    CampaignSessionCreate,
    CampaignVisibility,
    DelegationCreate,
    DiceRequest,
    TranscriptCreate,
)
from jarvis.policy import Actor

DICE_PATTERN = re.compile(r"^([1-9][0-9]?)d([1-9][0-9]{0,3})(?:kh([1-9][0-9]?))?([+-][0-9]{1,4})?$")


class GameMasterDenied(PermissionError):
    pass


class GameMasterConflict(ValueError):
    pass


@dataclass(frozen=True)
class GameMasterScope:
    actor: Actor

    def require(self, capability: str) -> None:
        if capability not in self.actor.capabilities:
            raise GameMasterDenied(f"Missing capability: {capability}")


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class RulesPlugin(Protocol):
    name: str

    def get_rule(self, query: str) -> dict: ...

    def validate_action(self, change: dict) -> bool: ...

    def calculate_modifier(self, entity: dict, check_type: str) -> int: ...


class BasicRulesPlugin:
    name = "basic"

    def get_rule(self, query: str) -> dict:
        return {
            "plugin": self.name,
            "query": query[:200],
            "rule": "System-neutral checks use the explicitly supplied bounded dice expression.",
        }

    def validate_action(self, change: dict) -> bool:
        return change.get("action") in {"CREATE", "RETIRE"}

    def calculate_modifier(self, entity: dict, check_type: str) -> int:
        modifiers = entity.get("data", {}).get("modifiers", {})
        value = modifiers.get(check_type, 0) if isinstance(modifiers, dict) else 0
        return value if isinstance(value, int) and -1000 <= value <= 1000 else 0


class DiceEntropy(Protocol):
    provenance: str
    reference: str

    def randint(self, low: int, high: int) -> int: ...


class SystemDiceEntropy:
    provenance = "SYSTEM_ENTROPY"

    def __init__(self):
        self._random = secrets.SystemRandom()
        self.reference = hashlib.sha256(secrets.token_bytes(32)).hexdigest()

    def randint(self, low: int, high: int) -> int:
        return self._random.randint(low, high)


class SeededDiceEntropy:
    provenance = "DETERMINISTIC_TEST"

    def __init__(self, seed: str | int):
        self._random = random.Random(seed)
        self.reference = hashlib.sha256(str(seed).encode()).hexdigest()

    def randint(self, low: int, high: int) -> int:
        return self._random.randint(low, high)


@dataclass(frozen=True)
class ParsedDice:
    count: int
    sides: int
    keep: int
    modifier: int


def parse_dice(expression: str) -> ParsedDice:
    match = DICE_PATTERN.fullmatch(expression.strip().lower())
    if match is None:
        raise GameMasterConflict("Unsupported dice expression")
    count, sides = int(match[1]), int(match[2])
    keep = int(match[3]) if match[3] else count
    modifier = int(match[4] or 0)
    if count > 20 or sides < 2 or sides > 1000 or keep > count or abs(modifier) > 1000:
        raise GameMasterConflict("Dice expression exceeds configured limits")
    return ParsedDice(count, sides, keep, modifier)


class RollAuthorityPolicy:
    name = "personal_play"

    @staticmethod
    def decide(subject: CampaignEntry, actor_id: str, member_role: str, delegated: bool) -> str:
        if subject.kind == "NPC":
            return "JARVIS_NPC"
        if subject.kind != "PC":
            raise GameMasterDenied("Roll subject must be an NPC or player character")
        if actor_id != subject.player_actor_id and member_role != "GM":
            raise GameMasterDenied(
                "Only the Game Master or controlling player can request this roll"
            )
        return "JARVIS_DELEGATED" if delegated else "HUMAN"


class GameMasterService:
    def __init__(
        self,
        database: Database,
        *,
        entropy: DiceEntropy | None = None,
        rules_plugins: dict[str, RulesPlugin] | None = None,
        roll_policies: dict[str, RollAuthorityPolicy] | None = None,
        clock=now,
        scene_bytes: int = 16000,
    ):
        self.db = database
        self.entropy = entropy or SystemDiceEntropy()
        self.rules_plugins = rules_plugins or {"basic": BasicRulesPlugin()}
        self.roll_policies = roll_policies or {"personal_play": RollAuthorityPolicy()}
        self.clock = clock
        self.scene_bytes = scene_bytes

    async def _member(
        self, session, scope: GameMasterScope, campaign_id: str, *, lock: bool = False
    ) -> CampaignMember:
        statement = select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.actor_id == scope.actor.id,
        )
        if lock:
            statement = statement.with_for_update()
        member = await session.scalar(statement)
        if member is None:
            raise KeyError("Campaign not found")
        return member

    async def _campaign(self, session, campaign_id: str) -> Campaign:
        campaign = await session.get(Campaign, campaign_id)
        if campaign is None:
            raise KeyError("Campaign not found")
        return campaign

    @staticmethod
    def _require_gm(member: CampaignMember) -> None:
        if member.role != "GM":
            raise GameMasterDenied("Game Master membership required")

    async def _entry(
        self, session, campaign_id: str, entry_id: str, *, lock: bool = False
    ) -> CampaignEntry:
        statement = select(CampaignEntry).where(
            CampaignEntry.id == entry_id,
            CampaignEntry.campaign_id == campaign_id,
        )
        if lock:
            statement = statement.with_for_update()
        entry = await session.scalar(statement)
        if entry is None:
            raise KeyError("Campaign entry not found")
        return entry

    @staticmethod
    def _entry_visible(member: CampaignMember, actor_id: str, entry: CampaignEntry) -> bool:
        if entry.visibility == CampaignVisibility.RETIRED.value:
            return False
        if member.role == "GM":
            return True
        if entry.visibility == CampaignVisibility.GM_SECRET.value:
            return False
        return not (
            entry.visibility == CampaignVisibility.PLAYER_PRIVATE.value
            and entry.player_actor_id != actor_id
        )

    @staticmethod
    def _campaign_view(campaign: Campaign, role: str) -> dict:
        return {
            "id": campaign.id,
            "name": campaign.name,
            "game_system": campaign.game_system,
            "rules_plugin": campaign.rules_plugin,
            "roll_policy": campaign.roll_policy,
            "status": campaign.status,
            "membership_role": role,
            "created_at": utc(campaign.created_at).isoformat(),
            "updated_at": utc(campaign.updated_at).isoformat(),
        }

    @staticmethod
    def _entry_view(entry: CampaignEntry) -> dict:
        return {
            "id": entry.id,
            "kind": entry.kind,
            "name": entry.name,
            "content": entry.content,
            "data": entry.data_json,
            "visibility": entry.visibility,
            "player_actor_id": entry.player_actor_id,
            "source_proposal_id": entry.source_proposal_id,
            "trust": "UNTRUSTED_CANONICAL_CONTENT",
            "created_at": utc(entry.created_at).isoformat(),
        }

    @staticmethod
    def _session_view(session: CampaignSession | None) -> dict | None:
        if session is None:
            return None
        return {
            "id": session.id,
            "title": session.title,
            "status": session.status,
            "active_location_id": session.active_location_id,
            "created_at": utc(session.created_at).isoformat(),
        }

    async def _authorized_session_view(self, db_session, scope, member, row):
        view = self._session_view(row)
        if view and view["active_location_id"]:
            location = await db_session.get(CampaignEntry, view["active_location_id"])
            if location is None or not self._entry_visible(member, scope.actor.id, location):
                view["active_location_id"] = None
        return view

    async def create_campaign(self, scope: GameMasterScope, body: CampaignCreate) -> dict:
        scope.require("campaign.write")
        if body.rules_plugin not in self.rules_plugins:
            raise GameMasterConflict("Configured rules plugin is unavailable")
        if body.roll_policy not in self.roll_policies:
            raise GameMasterConflict("Configured roll policy is unavailable")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            campaign = Campaign(
                owner_id=scope.actor.id,
                name=body.name,
                game_system=body.game_system,
                rules_plugin=body.rules_plugin,
                roll_policy=body.roll_policy,
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(campaign)
            await session.flush()
            session.add(
                CampaignMember(
                    campaign_id=campaign.id,
                    actor_id=scope.actor.id,
                    role="GM",
                    display_name="Game Master",
                    created_at=timestamp,
                )
            )
            audit(
                session,
                scope.actor.id,
                "campaign.created",
                {
                    "campaign_id": campaign.id,
                    "rules_plugin": body.rules_plugin,
                    "roll_policy": body.roll_policy,
                },
            )
            return self._campaign_view(campaign, "GM")

    async def list_campaigns(self, scope: GameMasterScope) -> list[dict]:
        scope.require("campaign.read")
        async with self.db.sessions() as session:
            rows = (
                await session.execute(
                    select(Campaign, CampaignMember.role)
                    .join(
                        CampaignMember,
                        and_(
                            CampaignMember.campaign_id == Campaign.id,
                            CampaignMember.actor_id == scope.actor.id,
                        ),
                    )
                    .where(Campaign.status == "ACTIVE")
                    .order_by(Campaign.updated_at.desc())
                    .limit(100)
                )
            ).all()
            return [self._campaign_view(campaign, role) for campaign, role in rows]

    async def add_member(
        self, scope: GameMasterScope, campaign_id: str, body: CampaignMemberCreate
    ) -> dict:
        scope.require("campaign.write")
        async with self.db.sessions.begin() as session:
            member = await self._member(session, scope, campaign_id)
            self._require_gm(member)
            existing = await session.scalar(
                select(CampaignMember).where(
                    CampaignMember.campaign_id == campaign_id,
                    CampaignMember.actor_id == body.actor_id,
                )
            )
            if existing:
                if existing.role != body.role.value or existing.display_name != body.display_name:
                    raise GameMasterConflict("Campaign member already exists with different data")
                return {
                    "id": existing.id,
                    "actor_id": existing.actor_id,
                    "role": existing.role,
                    "display_name": existing.display_name,
                    "idempotent_replay": True,
                }
            created = CampaignMember(
                campaign_id=campaign_id,
                actor_id=body.actor_id,
                role=body.role.value,
                display_name=body.display_name,
                created_at=self.clock(),
            )
            session.add(created)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.member_added",
                {"campaign_id": campaign_id, "member_id": created.id, "role": created.role},
            )
            return {
                "id": created.id,
                "actor_id": created.actor_id,
                "role": created.role,
                "display_name": created.display_name,
                "idempotent_replay": False,
            }

    async def create_entry(
        self,
        scope: GameMasterScope,
        campaign_id: str,
        body: CampaignEntryCreate,
    ) -> dict:
        scope.require("campaign.write")
        async with self.db.sessions.begin() as session:
            member = await self._member(session, scope, campaign_id)
            self._require_gm(member)
            if body.player_actor_id:
                player = await session.scalar(
                    select(CampaignMember).where(
                        CampaignMember.campaign_id == campaign_id,
                        CampaignMember.actor_id == body.player_actor_id,
                    )
                )
                if player is None:
                    raise GameMasterConflict("Entry controller must be a campaign member")
            timestamp = self.clock()
            entry = CampaignEntry(
                campaign_id=campaign_id,
                created_by=scope.actor.id,
                kind=body.kind.value,
                name=body.name,
                content=body.content,
                data_json=body.data,
                visibility=body.visibility.value,
                player_actor_id=body.player_actor_id,
                source_proposal_id=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(entry)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.entry_created",
                {
                    "campaign_id": campaign_id,
                    "entry_id": entry.id,
                    "kind": entry.kind,
                    "visibility": entry.visibility,
                },
            )
            return self._entry_view(entry)

    async def create_session(
        self, scope: GameMasterScope, campaign_id: str, body: CampaignSessionCreate
    ) -> dict:
        scope.require("campaign.write")
        async with self.db.sessions.begin() as session:
            member = await self._member(session, scope, campaign_id)
            self._require_gm(member)
            if body.active_location_id:
                location = await self._entry(session, campaign_id, body.active_location_id)
                if location.kind != "LOCATION" or location.visibility == "RETIRED":
                    raise GameMasterConflict("Active location must be a current LOCATION entry")
            timestamp = self.clock()
            created = CampaignSession(
                campaign_id=campaign_id,
                created_by=scope.actor.id,
                title=body.title,
                active_location_id=body.active_location_id,
                status="ACTIVE",
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(created)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.session_created",
                {"campaign_id": campaign_id, "session_id": created.id},
            )
            view = self._session_view(created)
            assert view is not None
            return view

    @staticmethod
    def _transcript_view(line: CampaignTranscript) -> dict:
        return {
            "id": line.id,
            "speaker": line.speaker,
            "content": line.content,
            "visibility": line.visibility,
            "player_actor_id": line.player_actor_id,
            "origin": line.origin,
            "trust": "UNTRUSTED_TRANSCRIPT_CONTENT",
            "created_at": utc(line.created_at).isoformat(),
        }

    async def append_transcript(
        self,
        scope: GameMasterScope,
        campaign_id: str,
        session_id: str,
        body: TranscriptCreate,
    ) -> dict:
        scope.require("campaign.transcript")
        async with self.db.sessions.begin() as session:
            member = await self._member(session, scope, campaign_id)
            game_session = await session.scalar(
                select(CampaignSession.id).where(
                    CampaignSession.id == session_id,
                    CampaignSession.campaign_id == campaign_id,
                )
            )
            if game_session is None:
                raise KeyError("Campaign session not found")
            if member.role != "GM":
                if body.visibility == CampaignVisibility.GM_SECRET:
                    raise GameMasterDenied("Players cannot create GM-secret transcript lines")
                if (
                    body.visibility == CampaignVisibility.PLAYER_PRIVATE
                    and body.player_actor_id != scope.actor.id
                ):
                    raise GameMasterDenied("Players can create only their own private transcript")
            if body.player_actor_id:
                target = await session.scalar(
                    select(CampaignMember.id).where(
                        CampaignMember.campaign_id == campaign_id,
                        CampaignMember.actor_id == body.player_actor_id,
                    )
                )
                if target is None:
                    raise GameMasterConflict("Transcript player must be a campaign member")
            line = CampaignTranscript(
                campaign_id=campaign_id,
                session_id=session_id,
                actor_id=scope.actor.id,
                speaker=body.speaker,
                content=body.content,
                visibility=body.visibility.value,
                player_actor_id=body.player_actor_id,
                origin="HUMAN_API",
                created_at=self.clock(),
            )
            session.add(line)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.transcript_appended",
                {
                    "campaign_id": campaign_id,
                    "session_id": session_id,
                    "transcript_id": line.id,
                    "visibility": line.visibility,
                },
            )
            return self._transcript_view(line)

    async def scene_packet(
        self,
        scope: GameMasterScope,
        campaign_id: str,
        session_id: str | None = None,
    ) -> dict:
        scope.require("campaign.read")
        async with self.db.sessions() as session:
            member = await self._member(session, scope, campaign_id)
            campaign = await self._campaign(session, campaign_id)
            current_session = None
            if session_id:
                current_session = await session.scalar(
                    select(CampaignSession).where(
                        CampaignSession.id == session_id,
                        CampaignSession.campaign_id == campaign_id,
                    )
                )
                if current_session is None:
                    raise KeyError("Campaign session not found")
            if member.role == "GM":
                visibility = CampaignEntry.visibility != CampaignVisibility.RETIRED.value
            else:
                visibility = or_(
                    CampaignEntry.visibility.in_(
                        [
                            CampaignVisibility.PUBLIC.value,
                            CampaignVisibility.PARTY.value,
                            CampaignVisibility.INFERRED.value,
                            CampaignVisibility.RUMOR.value,
                        ]
                    ),
                    and_(
                        CampaignEntry.visibility == CampaignVisibility.PLAYER_PRIVATE.value,
                        CampaignEntry.player_actor_id == scope.actor.id,
                    ),
                )
            entries = list(
                await session.scalars(
                    select(CampaignEntry)
                    .where(CampaignEntry.campaign_id == campaign_id, visibility)
                    .order_by(CampaignEntry.updated_at.desc(), CampaignEntry.id)
                    .limit(128)
                )
            )
            selected = []
            for entry in entries:
                view = self._entry_view(entry)
                candidate = [*selected, view]
                if len(json.dumps(candidate, ensure_ascii=False).encode()) <= self.scene_bytes:
                    selected.append(view)
            transcript = []
            transcript_candidates = []
            if current_session is not None:
                if member.role == "GM":
                    transcript_visibility = CampaignTranscript.visibility.in_(
                        ["PUBLIC", "PARTY", "PLAYER_PRIVATE", "GM_SECRET"]
                    )
                else:
                    transcript_visibility = or_(
                        CampaignTranscript.visibility.in_(["PUBLIC", "PARTY"]),
                        and_(
                            CampaignTranscript.visibility == "PLAYER_PRIVATE",
                            CampaignTranscript.player_actor_id == scope.actor.id,
                        ),
                    )
                transcript_candidates = list(
                    await session.scalars(
                        select(CampaignTranscript)
                        .where(
                            CampaignTranscript.campaign_id == campaign_id,
                            CampaignTranscript.session_id == current_session.id,
                            transcript_visibility,
                        )
                        .order_by(CampaignTranscript.created_at.desc(), CampaignTranscript.id)
                        .limit(64)
                    )
                )
                for line in reversed(transcript_candidates):
                    view = self._transcript_view(line)
                    candidate = [*transcript, view]
                    payload = {"entries": selected, "transcript": candidate}
                    if len(json.dumps(payload, ensure_ascii=False).encode()) <= self.scene_bytes:
                        transcript.append(view)
            plugin = self.rules_plugins.get(campaign.rules_plugin)
            if plugin is None:
                raise GameMasterConflict("Campaign rules plugin is unavailable")
            return {
                "trust": "UNTRUSTED_CAMPAIGN_CONTENT",
                "campaign": self._campaign_view(campaign, member.role),
                "session": await self._authorized_session_view(
                    session, scope, member, current_session
                ),
                "entries": selected,
                "transcript": transcript,
                "authorized_visibilities": sorted({item["visibility"] for item in selected}),
                "rules": plugin.get_rule("current scene"),
                "omitted_for_budget": (len(entries) - len(selected))
                + (len(transcript_candidates) - len(transcript)),
            }

    async def delegate_roll(
        self, scope: GameMasterScope, campaign_id: str, body: DelegationCreate
    ) -> dict:
        scope.require("campaign.delegate")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            await self._member(session, scope, campaign_id)
            subject = await self._entry(session, campaign_id, body.subject_entry_id)
            if subject.kind != "PC" or subject.player_actor_id != scope.actor.id:
                raise GameMasterDenied("Only the controlling player can delegate a PC roll")
            existing = await session.scalar(
                select(RollDelegation).where(
                    RollDelegation.campaign_id == campaign_id,
                    RollDelegation.actor_id == scope.actor.id,
                    RollDelegation.nonce == body.nonce,
                )
            )
            if existing:
                original_expiry = utc(existing.created_at) + timedelta(seconds=body.ttl_seconds)
                if (
                    existing.subject_entry_id != body.subject_entry_id
                    or utc(existing.expires_at) != original_expiry
                ):
                    raise GameMasterConflict("Delegation nonce was used with different data")
                return self._delegation_view(existing, True)
            delegation = RollDelegation(
                campaign_id=campaign_id,
                actor_id=scope.actor.id,
                subject_entry_id=body.subject_entry_id,
                nonce=body.nonce,
                max_uses=1,
                uses=0,
                status="ACTIVE",
                expires_at=timestamp + timedelta(seconds=body.ttl_seconds),
                created_at=timestamp,
            )
            session.add(delegation)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.roll_delegated",
                {
                    "campaign_id": campaign_id,
                    "delegation_id": delegation.id,
                    "subject_entry_id": body.subject_entry_id,
                    "expires_at": delegation.expires_at.isoformat(),
                },
            )
            return self._delegation_view(delegation, False)

    @staticmethod
    def _delegation_view(delegation: RollDelegation, replay: bool) -> dict:
        return {
            "id": delegation.id,
            "campaign_id": delegation.campaign_id,
            "subject_entry_id": delegation.subject_entry_id,
            "status": delegation.status,
            "max_uses": delegation.max_uses,
            "uses": delegation.uses,
            "expires_at": utc(delegation.expires_at).isoformat(),
            "idempotent_replay": replay,
        }

    @staticmethod
    def _roll_view(roll: DiceRoll, replay: bool = False) -> dict:
        return {
            "id": roll.id,
            "campaign_id": roll.campaign_id,
            "session_id": roll.session_id,
            "request_id": roll.request_id,
            "requested_by": roll.requested_by,
            "subject_entry_id": roll.subject_entry_id,
            "expression": roll.expression,
            "purpose": roll.purpose,
            "authority": roll.authority,
            "status": roll.status,
            "rolls": roll.rolls,
            "kept": roll.kept,
            "discarded": roll.discarded,
            "modifier": roll.modifier,
            "total": roll.total,
            "provenance": roll.provenance,
            "visibility": roll.visibility,
            "entropy_ref": roll.entropy_ref,
            "delegation_id": roll.delegation_id,
            "created_at": utc(roll.created_at).isoformat(),
            "resolved_at": utc(roll.resolved_at).isoformat() if roll.resolved_at else None,
            "idempotent_replay": replay,
        }

    async def roll(self, scope: GameMasterScope, body: DiceRequest) -> dict:
        scope.require("campaign.dice")
        parsed = parse_dice(body.expression)
        normalized_expression = body.expression.strip().lower()
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            member = await self._member(session, scope, body.campaign_id)
            campaign = await self._campaign(session, body.campaign_id)
            existing = await session.scalar(
                select(DiceRoll).where(
                    DiceRoll.campaign_id == body.campaign_id,
                    DiceRoll.requested_by == scope.actor.id,
                    DiceRoll.request_id == body.request_id,
                )
            )
            if existing:
                if (
                    existing.subject_entry_id != body.subject_entry_id
                    or existing.expression != normalized_expression
                    or existing.session_id != body.session_id
                    or existing.purpose != body.purpose
                ):
                    raise GameMasterConflict("Dice request ID was already used with different data")
                return self._roll_view(existing, True)
            if body.session_id:
                game_session = await session.scalar(
                    select(CampaignSession.id).where(
                        CampaignSession.id == body.session_id,
                        CampaignSession.campaign_id == body.campaign_id,
                    )
                )
                if game_session is None:
                    raise KeyError("Campaign session not found")
            subject = await self._entry(session, body.campaign_id, body.subject_entry_id)
            if not self._entry_visible(member, scope.actor.id, subject):
                raise KeyError("Campaign entry not found")
            delegation = None
            if subject.kind == "PC" and subject.player_actor_id == scope.actor.id:
                delegation_actor = subject.player_actor_id
            elif subject.kind == "PC":
                delegation_actor = subject.player_actor_id
            else:
                delegation_actor = None
            if delegation_actor:
                delegation = await session.scalar(
                    select(RollDelegation)
                    .where(
                        RollDelegation.campaign_id == body.campaign_id,
                        RollDelegation.actor_id == delegation_actor,
                        RollDelegation.subject_entry_id == subject.id,
                        RollDelegation.status == "ACTIVE",
                        RollDelegation.uses < RollDelegation.max_uses,
                        RollDelegation.expires_at > timestamp,
                    )
                    .order_by(RollDelegation.created_at, RollDelegation.id)
                    .with_for_update()
                )
            roll_policy = self.roll_policies.get(campaign.roll_policy)
            if roll_policy is None:
                raise GameMasterConflict("Campaign roll policy is unavailable")
            authority = roll_policy.decide(
                subject, scope.actor.id, member.role, delegation is not None
            )
            if authority == "HUMAN":
                created = DiceRoll(
                    campaign_id=body.campaign_id,
                    session_id=body.session_id,
                    requested_by=scope.actor.id,
                    request_id=body.request_id,
                    subject_entry_id=subject.id,
                    expression=normalized_expression,
                    purpose=body.purpose,
                    authority="HUMAN",
                    status="AWAITING_HUMAN",
                    rolls=[],
                    kept=[],
                    discarded=[],
                    modifier=parsed.modifier,
                    total=None,
                    provenance="HUMAN_PENDING",
                    visibility=subject.visibility,
                    entropy_ref="",
                    created_at=timestamp,
                )
            else:
                rolls = [self.entropy.randint(1, parsed.sides) for _ in range(parsed.count)]
                kept = sorted(rolls, reverse=True)[: parsed.keep]
                discarded = sorted(rolls)[: parsed.count - parsed.keep]
                if delegation is not None:
                    delegation.uses += 1
                    delegation.status = "CONSUMED"
                    delegation.consumed_at = timestamp
                created = DiceRoll(
                    campaign_id=body.campaign_id,
                    session_id=body.session_id,
                    requested_by=scope.actor.id,
                    request_id=body.request_id,
                    subject_entry_id=subject.id,
                    expression=normalized_expression,
                    purpose=body.purpose,
                    authority=authority,
                    status="ROLLED",
                    rolls=rolls,
                    kept=kept,
                    discarded=discarded,
                    modifier=parsed.modifier,
                    total=sum(kept) + parsed.modifier,
                    provenance=self.entropy.provenance,
                    visibility=subject.visibility,
                    entropy_ref=self.entropy.reference,
                    delegation_id=delegation.id if delegation else None,
                    created_at=timestamp,
                    resolved_at=timestamp,
                )
            session.add(created)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.dice_recorded",
                {
                    "campaign_id": body.campaign_id,
                    "roll_id": created.id,
                    "authority": created.authority,
                    "status": created.status,
                    "expression": created.expression,
                    "total": (
                        created.total
                        if created.visibility not in {"GM_SECRET", "PLAYER_PRIVATE"}
                        else None
                    ),
                    "provenance": created.provenance,
                },
            )
            return self._roll_view(created)

    async def report_human_roll(
        self, scope: GameMasterScope, campaign_id: str, roll_id: str, total: int
    ) -> dict:
        scope.require("campaign.dice")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            roll = await session.scalar(
                select(DiceRoll)
                .where(
                    DiceRoll.id == roll_id,
                    DiceRoll.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if roll is None:
                raise KeyError("Dice roll request not found")
            member = await self._member(session, scope, roll.campaign_id)
            subject = await self._entry(session, roll.campaign_id, roll.subject_entry_id)
            if not self._entry_visible(member, scope.actor.id, subject):
                raise KeyError("Dice roll request not found")
            if roll.authority != "HUMAN" or subject.player_actor_id != scope.actor.id:
                raise GameMasterDenied("Only the controlling player can report this roll")
            parsed = parse_dice(roll.expression)
            minimum = parsed.keep + parsed.modifier
            maximum = parsed.keep * parsed.sides + parsed.modifier
            if total < minimum or total > maximum:
                raise GameMasterConflict("Human roll total is impossible for the requested dice")
            if roll.status == "ROLLED":
                if roll.total != total:
                    raise GameMasterConflict("Human roll was already reported with another total")
                return self._roll_view(roll, True)
            roll.status = "ROLLED"
            roll.total = total
            roll.provenance = "HUMAN_REPORTED"
            roll.resolved_at = timestamp
            audit(
                session,
                scope.actor.id,
                "campaign.human_roll_reported",
                {"campaign_id": roll.campaign_id, "roll_id": roll.id, "total": total},
            )
            return self._roll_view(roll)

    async def propose_event(
        self,
        scope: GameMasterScope,
        body: CampaignProposalCreate,
        *,
        origin: str = "HUMAN_API",
        run_id: str | None = None,
    ) -> dict:
        scope.require("campaign.propose")
        async with self.db.sessions.begin() as session:
            await self._member(session, scope, body.campaign_id)
            campaign = await self._campaign(session, body.campaign_id)
            if body.session_id:
                found = await session.scalar(
                    select(CampaignSession.id).where(
                        CampaignSession.id == body.session_id,
                        CampaignSession.campaign_id == body.campaign_id,
                    )
                )
                if found is None:
                    raise KeyError("Campaign session not found")
            plugin = self.rules_plugins.get(campaign.rules_plugin)
            changes = [item.model_dump(mode="json") for item in body.changes]
            if plugin is None or not all(plugin.validate_action(change) for change in changes):
                raise GameMasterConflict("Rules plugin rejected the proposed change")
            proposal = CampaignEventProposal(
                campaign_id=body.campaign_id,
                session_id=body.session_id,
                proposed_by=scope.actor.id,
                summary=body.summary,
                changes=changes,
                status="PENDING",
                origin=origin,
                created_at=self.clock(),
            )
            session.add(proposal)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.event_proposed",
                {
                    "campaign_id": body.campaign_id,
                    "proposal_id": proposal.id,
                    "origin": origin,
                    "change_count": len(changes),
                },
                run_id,
            )
            return self._proposal_view(proposal)

    @staticmethod
    def _proposal_view(proposal: CampaignEventProposal) -> dict:
        return {
            "id": proposal.id,
            "campaign_id": proposal.campaign_id,
            "session_id": proposal.session_id,
            "summary": proposal.summary,
            "changes": proposal.changes,
            "status": proposal.status,
            "origin": proposal.origin,
            "created_at": utc(proposal.created_at).isoformat(),
            "decided_at": utc(proposal.decided_at).isoformat() if proposal.decided_at else None,
        }

    async def list_sessions(self, scope: GameMasterScope, campaign_id: str) -> list[dict]:
        scope.require("campaign.read")
        async with self.db.sessions() as session:
            member = await self._member(session, scope, campaign_id)
            rows = await session.scalars(
                select(CampaignSession)
                .where(CampaignSession.campaign_id == campaign_id)
                .order_by(CampaignSession.created_at.desc())
                .limit(100)
            )
            views = [
                await self._authorized_session_view(session, scope, member, row) for row in rows
            ]
            return [view for view in views if view is not None]

    async def list_proposals(self, scope: GameMasterScope, campaign_id: str) -> list[dict]:
        """The cockpit needs durable proposal history; full changes are GM-only."""
        scope.require("campaign.read")
        async with self.db.sessions() as session:
            member = await self._member(session, scope, campaign_id)
            self._require_gm(member)
            rows = await session.scalars(
                select(CampaignEventProposal)
                .where(CampaignEventProposal.campaign_id == campaign_id)
                .order_by(CampaignEventProposal.created_at.desc())
                .limit(100)
            )
            return [self._proposal_view(row) for row in rows]

    async def decide_proposal(
        self,
        scope: GameMasterScope,
        campaign_id: str,
        proposal_id: str,
        *,
        approve: bool,
    ) -> dict:
        scope.require("campaign.approve")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            proposal = await session.scalar(
                select(CampaignEventProposal)
                .where(
                    CampaignEventProposal.id == proposal_id,
                    CampaignEventProposal.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if proposal is None:
                raise KeyError("Campaign proposal not found")
            member = await self._member(session, scope, proposal.campaign_id)
            self._require_gm(member)
            if proposal.status != "PENDING":
                raise GameMasterConflict("Campaign proposal was already decided")
            proposal.status = "APPROVED" if approve else "REJECTED"
            proposal.decided_by = scope.actor.id
            proposal.decided_at = timestamp
            event = None
            applied = []
            if approve:
                for change in proposal.changes:
                    if change["action"] == CampaignChangeAction.CREATE.value:
                        body = CampaignEntryCreate.model_validate(change["entry"])
                        if body.player_actor_id:
                            player = await session.scalar(
                                select(CampaignMember.id).where(
                                    CampaignMember.campaign_id == proposal.campaign_id,
                                    CampaignMember.actor_id == body.player_actor_id,
                                )
                            )
                            if player is None:
                                raise GameMasterConflict(
                                    "Proposed entry controller is not a campaign member"
                                )
                        entry = CampaignEntry(
                            campaign_id=proposal.campaign_id,
                            created_by=scope.actor.id,
                            kind=body.kind.value,
                            name=body.name,
                            content=body.content,
                            data_json=body.data,
                            visibility=body.visibility.value,
                            player_actor_id=body.player_actor_id,
                            source_proposal_id=proposal.id,
                            created_at=timestamp,
                            updated_at=timestamp,
                        )
                        session.add(entry)
                        await session.flush()
                        applied.append({"action": "CREATE", "entry_id": entry.id})
                    else:
                        target = await self._entry(
                            session,
                            proposal.campaign_id,
                            change["target_entry_id"],
                            lock=True,
                        )
                        if target.visibility == CampaignVisibility.RETIRED.value:
                            raise GameMasterConflict("Campaign entry is already retired")
                        target.visibility = CampaignVisibility.RETIRED.value
                        target.updated_at = timestamp
                        applied.append({"action": "RETIRE", "entry_id": target.id})
                event = CampaignEvent(
                    campaign_id=proposal.campaign_id,
                    session_id=proposal.session_id,
                    proposal_id=proposal.id,
                    approved_by=scope.actor.id,
                    summary=proposal.summary,
                    applied_changes=applied,
                    created_at=timestamp,
                )
                session.add(event)
                await session.flush()
            audit(
                session,
                scope.actor.id,
                "campaign.event_decided",
                {
                    "campaign_id": proposal.campaign_id,
                    "proposal_id": proposal.id,
                    "decision": proposal.status,
                    "event_id": event.id if event else None,
                    "applied_entry_ids": [item["entry_id"] for item in applied],
                },
            )
            return {
                "proposal": self._proposal_view(proposal),
                "event": (
                    {
                        "id": event.id,
                        "campaign_id": event.campaign_id,
                        "proposal_id": event.proposal_id,
                        "applied_changes": event.applied_changes,
                        "created_at": utc(event.created_at).isoformat(),
                    }
                    if event
                    else None
                ),
            }
