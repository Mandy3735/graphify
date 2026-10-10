# JARVIS Tutor checkpoint 0.4

An authenticated, single-user FastAPI backend around the existing Graphify engine.
This is the phases 0–7 checkpoint of the larger JARVIS program. It includes
structured personal memory, a kernel-isolated Engineer workflow and a persisted,
source-grounded Tutor workflow with human attempts, evidence-backed mastery and
spaced reviews. Game Master, web/PWA UI, voice and integrations remain pending.
Fake mode exercises the current backend without API keys.

See [local setup and demos](../../docs/jarvis/LOCAL_DEVELOPMENT.md),
[architecture](../../docs/jarvis/ARCHITECTURE.md),
[personal memory](../../docs/jarvis/MEMORY.md),
[Tutor workflow](../../docs/jarvis/TUTOR.md),
[security](../../THREAT_MODEL.md), and [progress](../../JARVIS_PROGRESS.md).

The application has its own hashed requirements lock and wheel. Graphify is
installed from this repository alongside it; this wheel does not vendor Graphify.
Start a single backend process using `uvicorn jarvis.api:create_app --factory`.
Apply Alembic migrations before startup. Interactive API documentation is `/docs`.
