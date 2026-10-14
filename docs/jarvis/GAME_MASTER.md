# Game Master workflow — phase 8

The 0.5.0 backend implements canonical campaign state in migration 0004. Campaign
state is separate from personal memory. Every scene, transcript, roll and event
operation first resolves the trusted actor's explicit campaign membership.

## Visibility and scene packets

Canonical entries use `PUBLIC`, `PARTY`, `PLAYER_PRIVATE`, `GM_SECRET`, `INFERRED`,
`RUMOR` or `RETIRED`. GM members can read all current entries. Players can read
public/party/inferred/rumor entries plus player-private entries bound to their actor
ID. `GM_SECRET` and another player's private content are excluded in SQL before
ordering, candidate limits, byte budgets and model context construction.

ScenePacketBuilder returns only the bounded campaign/session, authorized canonical
entries, authorized recent transcript lines and selected rules plugin output. Every
content field is labeled untrusted data. The packet is injected before a
GAME_MASTER model call only after membership and visibility checks. A complete
campaign database is never dumped into a prompt; the current cap is 16,000 encoded
bytes across at most 128 entry and 64 transcript candidates.

Transcript lines are searchable session records, not canonical events. Players
cannot create or retrieve GM-secret lines and can create private lines only for
themselves. No transcript model tool exists, so model prose cannot masquerade as a
human transcript or canonical state.

## Dice and roll authority

The parser accepts bounded forms such as `1d20`, `1d20+5`, `2d6+3` and `4d6kh3`:
at most 20 dice, sides 2–1000, keep count no greater than dice count and absolute
modifier at most 1,000. Production uses `SystemRandom`; tests inject a seeded RNG.
Each electronic result stores its requesting actor, purpose, visibility, all rolls,
kept and discarded dice, modifier, total, authority, timestamp, provenance and a
SHA-256 entropy/seed reference. Raw seeds are not stored. Direct dice requests
also enforce subject visibility; knowing a GM-secret entity UUID does not grant
roll access.

NPC rolls use the dice service. PC rolls create an `AWAITING_HUMAN` request whether
requested by the controlling player or GM. Only the controlling member can report
the result, and the total must be possible for the requested expression. The
controller can create an expiring, one-use delegation; the next
authorized PC request consumes it atomically and control immediately returns to the
human. Request IDs make exact retries idempotent and reject changed replay data.
Campaigns select a named, operator-registered roll policy; the default is the
personal-play policy described here.

## Canonical event authority

Members and the model may create bounded structured proposals containing CREATE or
RETIRE changes. Proposals are non-canonical. Only an authenticated member with the
`campaign.approve` capability and GM role can decide one. PostgreSQL locks the
proposal, applies its validated changes and creates exactly one immutable event in
one transaction. Rejection and replay are final. Audit records contain identifiers,
decisions and dice evidence, not secret campaign prose.

The only model tools are `campaign.get_scene`, `dice.roll` and
`campaign.propose_event`, all bound to the actual GAME_MASTER run campaign/session.
There is no model tool for membership, delegation, human roll reporting,
transcripts, proposal decisions or canonical commits.

## API surface

- `POST/GET /api/campaigns`
- `POST /api/campaigns/{id}/members`
- `POST /api/campaigns/{id}/entries`
- `POST /api/campaigns/{id}/sessions`
- `GET /api/campaigns/{id}/scene?session_id=...`
- `POST /api/campaigns/{id}/sessions/{session_id}/transcript`
- `POST /api/campaigns/{id}/dice`
- `POST /api/campaigns/{id}/rolls/{roll_id}/report`
- `POST /api/campaigns/{id}/delegations`
- `POST /api/campaigns/{id}/events/propose`
- `POST /api/campaigns/{id}/events/{proposal_id}/decide`

## Current limits

This remains a single-token/single-process prototype. Membership actor IDs are
configured application identities, not production sessions or OAuth users. The
basic rules plugin is deliberately system-neutral; campaign imports, initiative,
maps, semantic transcript search, recap generation, richer rulesets and the visual
GM console remain future work. Database administrators remain trusted. Production
still needs a restricted DB role, quotas/rate limits, multi-worker coordination,
identity/session hardening and notification/retention workers.

## Phase 12 secrecy review

Scene construction is refreshed after awaited retrieval. Historical scene tools are
rebound to the current authorized packet. Any packet change conservatively withholds
older derived model prose/tool arguments/results; a persisted history cutoff maintains
this across later steps/resumes while allowing new authorized content. Campaign
revocation does not erase owner-retained historical runs or recall already transmitted
context. Hidden/retired active-location UUIDs are null in session lists/scene views.
Session titles remain campaign-visible metadata. See root JARVIS_REVIEW.md.
