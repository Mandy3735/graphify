# JARVIS Phase 10 checkpoint 0.7.0

Authenticated single-user FastAPI/PostgreSQL application around preserved Graphify,
with memory, policy/exact approvals, bounded Engineer, human-evidence Tutor,
visibility-scoped Game Master, responsive React/PWA and optional voice/transcription.
The full personal operating system and production hardening remain incomplete.

Use [local setup/demos](../../docs/jarvis/LOCAL_DEVELOPMENT.md),
[UI setup](../../docs/jarvis/USER_EXPERIENCE.md), [voice setup](../../docs/jarvis/VOICE.md),
[architecture](../../docs/jarvis/ARCHITECTURE.md), [progress](../../JARVIS_PROGRESS.md)
and [security](../../THREAT_MODEL.md). Fake text mode needs no API key; voice is
independently disabled by default. Fake voice uses no microphone and silent test audio.

The application has its own hashed dependency lock and wheel; Graphify is installed
alongside, not vendored. Apply Alembic migrations before startup and use one backend
worker. Build frontend with `npm ci && npm run build` before serving or packaging.
Start `uvicorn jarvis.api:create_app --factory`. Interactive API docs are `/docs`.
Live model identifiers come from trusted configuration, never browser inputs.
