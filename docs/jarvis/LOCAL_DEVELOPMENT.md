# Local development and demonstrations

Requirements: Python 3.11+, uv, POSIX filesystem, Docker Compose/PostgreSQL 17.
No model key is required in fake mode. Use one API worker at this checkpoint.

## Install

From the Graphify repository root:

```sh
uv sync --frozen
uv pip install --python .venv/bin/python --require-hashes -r apps/jarvis/requirements.lock
uv pip install --python .venv/bin/python --no-deps --no-build-isolation -e apps/jarvis
cd apps/jarvis
cp .env.example .env
```

Put a generated token into JARVIS_AUTH_TOKEN in `.env`:

```sh
../../.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))'
docker compose up -d postgres
```

Load `.env` for Alembic and start the server (both from apps/jarvis):

```sh
../../.venv/bin/python - <<'PY'
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command
load_dotenv()
command.upgrade(Config("alembic.ini"), "head")
PY
../../.venv/bin/uvicorn jarvis.api:create_app --factory --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000/docs for the interactive API. This is API documentation,
not the future Command Center frontend. Models are server-only configuration.
Settings.from-env automatically reads `.env` in the current working directory.
Keep the token private; `.env` and local state are ignored by Git.

Authenticate requests with `Authorization: Bearer <your token>`. The single token
maps to the stable JARVIS_ACTOR_ID; changing that UUID creates a different data
owner. There is no multi-user registration or OAuth at this checkpoint.

## DEMO A — Code intelligence (implemented)

In `/docs`, POST `/api/code/projects/graphify/graph/update` with your authorization
header. Its response gives a run_id; poll GET `/api/runs/{id}` or connect to its
`/events` SSE endpoint. The update capability is enabled in `.env.example`.

Then POST `/api/code/projects/graphify/graph/query` with:

```json
{"question":"jarvis engine PolicyEngine approval", "budget":1200}
```

The completed run's result is a JSON tool envelope with source evidence and
confidence labels. `graph.explain` and `graph.impact` are available through
POST `/api/tools/execute`, e.g.:

```json
{"name":"graph.explain","arguments":{"project_id":"graphify","node":"apps/jarvis/src/jarvis/engine.py::Engine"}}
```

Project paths are trusted operator registrations, never accepted in tool args.
For a large repository, narrow questions or use file-qualified symbols.

## DEMO B — Engineer workflow (implemented in bounded scope)

POST `/api/chat` with:

```json
{"message":"How does approval resume a protected operation?", "mode":"ENGINEER", "project_id":"graphify"}
```

The run queries Graphify before the first model call and records evidence/tool
activity. Fake mode explicitly identifies its response. For an actual change workflow,
opt in to the verified Linux worker and POST /api/engineer/changes with exact
source hashes, proposed edits and standard-library Python test commands. Poll
the durable run, inspect the owner-scoped artifact, and review the patch. The
original repository stays unchanged. See [ENGINEER.md](ENGINEER.md) for setup,
limits, dry runs and a complete request example. test_engineer.py runs the real
worktree/command/impact workflow and adversarial isolation tests.

## Approval contract demonstration (implemented via fake integration tests)

No real external-write adapter is registered. The test
`test_external_write_pause_exact_approval_resume_and_replay` exercises a fake
external write, verifies no side effect before approval, approves exact normalized
arguments, resumes once and rejects replay. Other tests cover argument/target/run/
expiry/tool-version mutation, revoked capability, races and concurrent PG claims.

## DEMO C/D/E — Chief of Staff, Tutor, Game Master

These modes can start independent generic text runs with authorized personal
memory. Dedicated project/task, learner mastery, campaign membership/state/dice
workflows remain pending later milestones. Memory visibility is enforced, but campaign
membership and the complete GM secrecy system are not yet implemented.

## DEMO F — Memory inspector and provenance (implemented)

In `/docs`, use bearer authentication and POST `/api/memories`:

```json
{
  "memory_class": "SEMANTIC",
  "namespace": "personal",
  "visibility": "PRIVATE",
  "content": "The automobile repair manual is stored with my project notes.",
  "sources": [{"kind": "USER_NOTE", "locator": "owner note, 2026-10-05"}]
}
```

Save the returned ID. POST `/api/memories/search` with
`{"question":"vehicle repair manual"}`. Inspect its source IDs/locator and
retrieval reasons. POST `/api/chat` with that question, then inspect the run's
metadata.context_sources and retrieved_memory_ids. Fake mode verifies the flow;
it does not pretend to provide a live model's source-grounded answer. The E2E
grounded-fake test verifies response citations and inspector provenance.

PATCH `/api/memories/{id}` with expected_revision=1, new content, structured_data
and sources. The returned replacement ID links to the old record. Only the new
record is active in search; a stale revision gets 409. DELETE the replacement ID
and search again; its full correction lineage, sources and embeddings are purged.
GET `/api/memories/export` returns a scoped cursor page. Memory details and
retention limits are in MEMORY.md.

The `memory.propose_write` model tool creates an inactive proposal. Inspect it at
GET `/api/memory-proposals`; explicitly POST its `/accept` or `/reject` endpoint.
The model has no tool for accepting its own proposal or altering canonical state.

## Optional pgvector setup

Before creating a new local PostgreSQL volume, choose an image with the extension
available by adding `JARVIS_POSTGRES_IMAGE=pgvector/pgvector:pg17` to `.env`.
For an existing database, arrange compatible extension binaries with its operator
before enabling this setting; do not replace or delete persisted data.

After startup and migration, explicitly install the extension as the local
database administrator:

```sh
docker compose exec postgres psql -U jarvis -d jarvis -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

Then set `JARVIS_MEMORY_PGVECTOR=true` in `.env` and restart the backend. Without
that flag, no extension is needed. With it, startup checks extension availability.
JSON vectors are ranked with the cosine operator only after authorization and a
bounded candidate selection; no ANN index or Python pgvector dependency is added.

Offline embeddings remain the default. For deliberate live embedding calls,
select JARVIS_EMBEDDING_PROVIDER=openai, an accessible JARVIS_EMBEDDING_MODEL, and
compatible JARVIS_EMBEDDING_DIMENSIONS. The OpenAI key stays on the backend.

## Tests

From apps/jarvis, with the root .venv from the setup above:

```sh
../../.venv/bin/python -m pytest -q
../../.venv/bin/ruff check .
../../.venv/bin/ruff format --check .
../../.venv/bin/pyright
```

JARVIS's Pyright config explicitly includes the repository root as a source
search path. This resolves Graphify imports because Pyright cannot follow
setuptools' editable import hook; retain this path when changing CI setup.

Default suite skips PostgreSQL integration if JARVIS_TEST_DATABASE_URL is absent.
To include it, explicitly create a disposable local `jarvis_test` database and
set that variable. The tests perform upgrade/downgrade/upgrade and teardown its
schema; they refuse non-local addresses and database names without `_test`.
Use a separate database from your persisted development runs.

```sh
JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-only@127.0.0.1:5432/jarvis_test \
  ../../.venv/bin/python -m pytest -q
```

To verify optional vector SQL, use a separate disposable local `_test` database
with pgvector available, and run the same suite with `JARVIS_TEST_PGVECTOR=true`:

```sh
JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-only@127.0.0.1:5432/jarvis_vector_test \
  JARVIS_TEST_PGVECTOR=true ../../.venv/bin/python -m pytest -q
```

The opt-in test setup installs the extension only in that explicitly disposable
database. Both configurations run migration, persistence, correction/deletion
race, proposal-claim, protected audit and approval tests. CI has both image jobs.

From the repository root, preserve and run upstream tests independently:
`.venv/bin/python -m pytest tests/ -q`. Optional language/model dependencies affect
upstream results. Its installer tests prefer uv tool resolution when uv is on PATH;
for offline testing use a PATH containing the root .venv and standard system bins.
See UPSTREAM_BASELINE.md for the exact session environment and known failures.

## Live models

Set JARVIS_PROVIDER=openai and OPENAI_API_KEY only on the backend. Configure model
IDs from your own provider access; example IDs are preferences, not an availability
guarantee. Fallback needs both JARVIS_ALLOW_FALLBACK=true and allow_fallback=true
on the request. High-stakes requests deny fallback. Live streaming is consumed
through the Responses SDK; the public SSE surface streams run updates and the
completed result, not intermediate reasoning or token deltas.

## Linux Engineer tests

Install the Bubblewrap/util-linux/system-Python runtime described in ENGINEER.md.
Add `JARVIS_TEST_SANDBOX=true` to both disposable PostgreSQL test commands above.
This opts in to real kernel isolation tests; an unavailable sandbox fails those
tests. The application keeps execution disabled by default and text available.
