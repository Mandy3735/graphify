"""Authenticated Game Master API; canonical decisions remain human endpoints."""

from fastapi import APIRouter

from jarvis.game_master import GameMasterScope, GameMasterService
from jarvis.game_master_schema import (
    CampaignCreate,
    CampaignEntryCreate,
    CampaignMemberCreate,
    CampaignProposalCreate,
    CampaignSessionCreate,
    DelegationCreate,
    DiceRequest,
    HumanRollReport,
    ProposalDecision,
    TranscriptCreate,
)
from jarvis.policy import Actor


def game_master_router(
    game_master: GameMasterService, actor: Actor, dependencies: list
) -> APIRouter:
    router = APIRouter(prefix="/api/campaigns", tags=["game-master"], dependencies=dependencies)

    def scope() -> GameMasterScope:
        return GameMasterScope(actor)

    @router.post("", status_code=201)
    async def create_campaign(body: CampaignCreate):
        return await game_master.create_campaign(scope(), body)

    @router.get("")
    async def list_campaigns():
        return await game_master.list_campaigns(scope())

    @router.post("/{campaign_id}/members", status_code=201)
    async def add_member(campaign_id: str, body: CampaignMemberCreate):
        return await game_master.add_member(scope(), campaign_id, body)

    @router.post("/{campaign_id}/entries", status_code=201)
    async def create_entry(campaign_id: str, body: CampaignEntryCreate):
        return await game_master.create_entry(scope(), campaign_id, body)

    @router.get("/{campaign_id}/sessions")
    async def list_sessions(campaign_id: str):
        return await game_master.list_sessions(scope(), campaign_id)

    @router.post("/{campaign_id}/sessions", status_code=201)
    async def create_session(campaign_id: str, body: CampaignSessionCreate):
        return await game_master.create_session(scope(), campaign_id, body)

    @router.get("/{campaign_id}/scene")
    async def scene(campaign_id: str, session_id: str | None = None):
        return await game_master.scene_packet(scope(), campaign_id, session_id)

    @router.post("/{campaign_id}/sessions/{session_id}/transcript", status_code=201)
    async def append_transcript(campaign_id: str, session_id: str, body: TranscriptCreate):
        return await game_master.append_transcript(scope(), campaign_id, session_id, body)

    @router.post("/{campaign_id}/delegations", status_code=201)
    async def delegate(campaign_id: str, body: DelegationCreate):
        return await game_master.delegate_roll(scope(), campaign_id, body)

    @router.post("/{campaign_id}/dice", status_code=201)
    async def roll(campaign_id: str, body: DiceRequest):
        if body.campaign_id != campaign_id:
            from jarvis.game_master import GameMasterConflict

            raise GameMasterConflict("Campaign path and dice request differ")
        return await game_master.roll(scope(), body)

    @router.post("/{campaign_id}/rolls/{roll_id}/report")
    async def report(campaign_id: str, roll_id: str, body: HumanRollReport):
        return await game_master.report_human_roll(scope(), campaign_id, roll_id, body.total)

    @router.get("/{campaign_id}/events")
    async def list_proposals(campaign_id: str):
        return await game_master.list_proposals(scope(), campaign_id)

    @router.post("/{campaign_id}/events/propose", status_code=201)
    async def propose(campaign_id: str, body: CampaignProposalCreate):
        if body.campaign_id != campaign_id:
            from jarvis.game_master import GameMasterConflict

            raise GameMasterConflict("Campaign path and proposal differ")
        return await game_master.propose_event(scope(), body)

    @router.post("/{campaign_id}/events/{proposal_id}/decide")
    async def decide(campaign_id: str, proposal_id: str, body: ProposalDecision):
        return await game_master.decide_proposal(
            scope(), campaign_id, proposal_id, approve=body.approve
        )

    return router
