# Game Master — planned dedicated workflow

GAME_MASTER currently labels an independent generic text run. Campaigns, sessions,
visibility, ScenePacketBuilder, canonical event proposals, rules plugins, secure
dice and roll authority are not implemented. Generated prose cannot claim to
update authoritative game state. No GM secrecy guarantee is claimed for an
unimplemented campaign store.

Phase 8 will enforce PUBLIC/PARTY/PLAYER_PRIVATE/GM_SECRET/INFERRED/RUMOR/RETIRED
before context construction, make campaign membership explicit, preserve human PC
roll authority unless one-use delegation is active, and store auditable dice
results from an injectable RNG. Structured proposed events require validation/GM
approval before canonical commit. Tests must prove secrets never enter player
context. See JARVIS_PLAN.md and THREAT_MODEL.md for dependencies and boundaries.
