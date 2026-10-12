# Next task — Phase 10 optional voice

Continue Graphify → JARVIS from the local `jarvis/phase-9-user-experience`
checkpoint. Inspect HEAD and working tree first. The receiving published Phase 8
branch does not contain Phase 9 unless a subsequent user-authorized push occurs.
Do not fall back to an older branch or regenerate the application.

Read AGENTS.md, CODEX_HANDOFF.md, JARVIS_PROGRESS.md, JARVIS_PLAN.md,
JARVIS_REVIEW.md, THREAT_MODEL.md and docs/jarvis/MASTER_SPEC.md,
UPSTREAM_BOUNDARY.md, LOCAL_DEVELOPMENT.md, USER_EXPERIENCE.md, MEMORY.md,
ENGINEER.md, TUTOR.md and GAME_MASTER.md. Preserve Graphify core/CLI/root locks/
licenses/skill generation and all existing backend and browser security contracts.

Implement Phase 10 optional voice/transcription according to the master spec.
Inspect the existing configuration and frontend before choosing interfaces.
Keep text/tools/state fully usable without voice, default microphone off and
require explicit user opt-in. Stop/cancel must release devices and promptly end
provider sessions. Use a configured replaceable provider with fake tests; never
embed a provider API key or durable token in browser code/URLs/storage/caches.
Any live WebRTC credential must be server-issued, scoped and ephemeral. Review
CSP/Permissions-Policy changes narrowly; do not enable camera/geolocation.
Transcripts remain untrusted data and never commit canonical campaign state.
Explicit human approval, Tutor evidence, memory filtering, campaign memberships,
GM/player secrecy, PC roll authority and exact approvals must stay authoritative.

Record receiving checks, define bounded acceptance, add fake provider/unit/browser
security and state tests, build/test the frontend, run appropriate backend and
real PostgreSQL/pgvector/kernel regression suites, and synchronize Graphify.
Review device lifecycle, permission denial, offline/reconnect/error handling,
authority spoofing, ephemeral credential lifetime, caching and accessibility.
Fix critical/high findings and update progress/review/report/setup/verification.
Commit a concrete local checkpoint. Do not pay for a provider call, publish,
merge, deploy or send communications without user authorization. Chief of Staff
watchers/integrations and full production hardening remain separate work.
