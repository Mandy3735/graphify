# JARVIS memory checkpoint 0.2

An authenticated, single-user FastAPI backend around the existing Graphify engine.
This is the phases 0–5 checkpoint of the larger JARVIS program. Personal memory
includes structured classes, provenance, filtered retrieval and inspector APIs.
Engineer editing sandbox, Tutor, Game Master, web/PWA UI, voice and integrations
remain pending. Fake mode exercises the complete current backend without API keys.

See [local setup and demos](../../docs/jarvis/LOCAL_DEVELOPMENT.md),
[architecture](../../docs/jarvis/ARCHITECTURE.md),
[personal memory](../../docs/jarvis/MEMORY.md),
[security](../../THREAT_MODEL.md), and [progress](../../JARVIS_PROGRESS.md).

The application has its own hashed requirements lock and wheel. Graphify is
installed from this repository alongside it; this wheel does not vendor Graphify.
Start a single backend process using `uvicorn jarvis.api:create_app --factory`.
Apply Alembic migrations before startup. Interactive API documentation is `/docs`.
