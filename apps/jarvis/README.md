# JARVIS Game Master checkpoint 0.5

An authenticated, single-user FastAPI backend around the existing Graphify engine.
This is the phases 0–8 checkpoint of the larger JARVIS program. It includes
structured personal memory, a kernel-isolated Engineer workflow and a persisted,
source-grounded Tutor workflow with human attempts, evidence-backed mastery and
spaced reviews. Phase 8 adds membership-filtered canonical campaigns, bounded
scene packets, session transcripts, auditable dice/roll authority and GM-approved
event commits. Web/PWA UI, voice and integrations remain pending.
Fake mode exercises the current backend without API keys.

See [local setup and demos](../../docs/jarvis/LOCAL_DEVELOPMENT.md),
[architecture](../../docs/jarvis/ARCHITECTURE.md),
[personal memory](../../docs/jarvis/MEMORY.md),
[Tutor workflow](../../docs/jarvis/TUTOR.md),
[Game Master workflow](../../docs/jarvis/GAME_MASTER.md),
[security](../../THREAT_MODEL.md), and [progress](../../JARVIS_PROGRESS.md).

The application has its own hashed requirements lock and wheel. Graphify is
installed from this repository alongside it; this wheel does not vendor Graphify.
Start a single backend process using `uvicorn jarvis.api:create_app --factory`.
Apply Alembic migrations before startup. Interactive API documentation is `/docs`.

The Phase 9 Command Center/PWA is in `frontend/`. Run `npm ci` and
`npm run build` there before starting the API or packaging a wheel.
See [user experience setup](../../docs/jarvis/USER_EXPERIENCE.md).
