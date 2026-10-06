# JARVIS engineering report — 2026-10-05

A runnable **foundation checkpoint** is implemented in the existing Graphify
repository. It completes the bounded phases 0–4 scope in JARVIS_PLAN.md. The full
personal AI operating system specification is not complete.

Repository: `/workspace/graphify`; branch `jarvis/foundation`; parent commit
`5c7b84792f453582676548185aaec3824d51dfe2`, Graphify 0.9.77. The foundation is
prepared as a local checkpoint with Codex continuation instructions. Consult the
delivery manifest and remote branch for its commit and publication status.
The adjacent empty My-JARVIS-AI- repository was left untouched.

## What works

- Independent FastAPI/OpenAPI application with mandatory single-user bearer
  authentication, SQLAlchemy async PostgreSQL, versioned Alembic schema and Compose.
- Graphify index/update/query/explain/path/impact/health over operator-registered
  project IDs, with source provenance and relationship confidence retained.
- Typed tool registry, deterministic capabilities/risk checks, exact operation
  approvals, expiry/replay/mutation protection and append-oriented audit.
- Configurable official OpenAI Responses and offline fake providers, explicit
  fallback policy, error mapping, SDK streaming, usage/configured cost metadata.
- Durable bounded AgentRuns, transitions, cancellation, crash-safe failure,
  approval pause/resume and run-state SSE. Engineer requests query Graphify first.
- Credential-free parser worker, descriptor-relative no-follow source IO, safe
  snapshot staging, atomic writes, and file/byte/context/tool/time/concurrency caps.

The four mode identifiers exist and keep independent run context. Dedicated
Chief of Staff, Tutor and Game Master workflows are pending. No arbitrary-code
execution or real external-write integration is registered; fake integration
fixtures prove approval behavior without performing external communications.

## Verification actually executed

| Check | Observed result |
|---|---|
| Complete upstream baseline | 6,439 passed, 108 skipped, 40 failed; 103.15 s |
| Upstream after missing optional test deps installed | 6,470 passed, 108 skipped, 9 failed; 119.41 s |
| Comparison of remaining failures | All 9 were in the baseline; no new upstream failure name |
| Upstream architecture doc regression | 38 passed, 1 warning |
| Full JARVIS unit/security/Graphify/PostgreSQL suite | **59 passed**, 6.01 s |
| JARVIS Ruff lint/format and Pyright | Passed; 0 type errors/warnings |
| PostgreSQL upgrade/downgrade/upgrade and metadata consistency | Passed |
| PostgreSQL competing approval claims, audit mutation guard, reconnect | Passed |
| Wheel/sdist build | Passed; source distribution includes migrations/setup/tests |
| Real HTTP/PostgreSQL smoke | Health 200; unauthenticated 401; Engineer run COMPLETED with Graphify evidence |
| Graph synchronization | 19,004 nodes, 39,013 edges, 1,061 communities |
| Scoped post-change query/explain/impact | Worked; Engine impact reported 48 affected nodes |
| Root Ruff lint | Passed |
| Root formatter baseline | 430 files would reformat; 23 already formatted — unchanged upstream drift |
| Root Pyright with explicitly configured existing venv | 639 errors, 4 warnings — pre-existing upstream issues/dependencies |
| Staged diff whitespace and preserved core boundary | Passed; no changes to graphify/, tests/, root pyproject/uv.lock or license notices |

The initial default-PATH baseline was interrupted during uv installer resolution:
5,659 passed, 102 skipped, 28 failed at interruption (354.49 s). A complete offline
baseline then ran with the installed Graphify interpreter on PATH and no uv on
PATH. Initial Pyright invocations had interpreter-resolution noise (880/881
errors); an explicit venv config gave the reported 639. These are documented,
not suppressed. SQLite's async worker stalled under the shell sandbox's socket
restrictions; local socket-authorized test execution completed without changing
application behavior or weakening tests.

No live OpenAI call, paid model use, frontend test/build, production deployment,
OAuth integration, voice integration or complete GM secrecy test is claimed.

## Known upstream failures

1. `tests/test_detect.py::test_graphifyignore_hermetic_without_vcs` — existing
   vendor ignore/VCS-root assertion.
2. `tests/test_hooks.py::test_no_git_repo_raises` — sandbox read-only `/tmp/.git`.
3. `tests/test_security.py::test_validate_url_accepts_http`
4. `tests/test_security.py::test_validate_url_accepts_https`
5. `tests/test_security.py::test_safe_fetch_returns_bytes`
6. `tests/test_security.py::test_safe_fetch_raises_on_non_2xx`
7. `tests/test_security.py::test_safe_fetch_raises_on_size_exceeded`
8. `tests/test_security.py::test_safe_fetch_text_decodes_utf8`
9. `tests/test_security.py::test_safe_fetch_text_replaces_bad_bytes`

The last seven encounter DNS validation failures in this restricted environment.
Installing missing OpenAI and optional Erlang/R/Solidity/VB.NET test packages
removed 31 baseline failures. Only the local environment changed; upstream source,
fixtures, tests, dependency metadata and lock were preserved.

## Architecture and security decisions

Use a modular monolith and independent application package/lock/CI, not a rewrite
or microservice split. PostgreSQL owns application execution/approval state;
Graphify owns code structural intelligence. Internal Graphify query/path APIs are
isolated inside the adapter, pinned to/tested against 0.9.77. Full AST snapshots
are re-extracted on adapter update; existing semantic graph contributions survive.

Identity, project roots, capabilities and model routing are trusted configuration.
Models propose validated tool data and cannot grant authority. Approval digest
binds normalized arguments, tool definition/version/risk, target, actor, run,
nonce and expiry. Claim/transition/audit commit before effects; protected execution
rechecks consumed exact approval and current capability. Non-idempotent attempts
are not automatically replayed after crashes. Pending approvals persist.

Review fixed an approval-before-pause-completion race, strengthened execution-time
approval proof and path races, and made high-stakes routing and failed model
attempts inspectable. Audit mutations are rejected by a PostgreSQL trigger.
Database administrators remain trusted. No application secrets enter worker
or model context. See JARVIS_REVIEW.md and THREAT_MODEL.md for release limits.

## Model configuration

`JARVIS_PROVIDER=fake` by default. Live reasoning uses `OPENAI_API_KEY` server-side
and configurable `JARVIS_PRIMARY_REASONING_MODEL` (example `gpt-6-astra`),
`JARVIS_FALLBACK_REASONING_MODEL` (example `gpt-6.1-sol`) and optional utility model.
Availability/access to those example IDs was not assumed or verified. Fallback
needs both server policy and request consent; high-stakes/auth failures deny it.
Voice/embedding IDs are reserved configuration only, not implemented providers.
Pricing is supplied as configuration; without it estimated cost is unknown.

## Exact principal engineering commands

Commands ran from `/workspace/graphify` unless noted. Diagnostic searches/reads
were also performed; raw command/result logs are retained in ignored `work/`.
Credentials below are disposable local test credentials, not user secrets.

```sh
.venv/bin/graphify --help
.venv/bin/graphify query 'What are the architectural boundaries and extension seams?' --budget 1200
.venv/bin/graphify update .
.venv/bin/graphify query 'graphify.extract extract build_from_json _query_graph_text serve' --budget 1400
.venv/bin/graphify explain 'graphify/serve.py::_query_graph_text'
.venv/bin/python -m pytest tests/ -q
PATH=/workspace/graphify/.venv/bin:/usr/local/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/ -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pyright
.venv/bin/python -m pyright --pythonpath /workspace/graphify/.venv/bin/python
.venv/bin/pyright --project work/pyright-baseline.json
.venv/bin/python -m pytest tests/ --collect-only -q
.venv/bin/python -m pytest tests/test_architecture_doc.py -q

git switch -c jarvis/foundation
UV_CACHE_DIR=/workspace/graphify/work/uv-cache uv pip compile apps/jarvis/pyproject.toml --extra dev -o apps/jarvis/requirements.lock --generate-hashes
UV_CACHE_DIR=/workspace/graphify/work/uv-cache uv venv work/jarvis-venv
UV_CACHE_DIR=/workspace/graphify/work/uv-cache uv pip install --python work/jarvis-venv/bin/python --require-hashes -r apps/jarvis/requirements.lock
UV_CACHE_DIR=/workspace/graphify/work/uv-cache uv pip install --python work/jarvis-venv/bin/python --no-deps --no-build-isolation -e apps/jarvis
UV_CACHE_DIR=/workspace/graphify/work/uv-cache uv pip install --python .venv/bin/python openai tree-sitter-language-pack==0.11.0 tree-sitter-solidity==1.2.13 tree-sitter-vb-dotnet==0.3.0
work/jarvis-venv/bin/ruff check apps/jarvis --fix
work/jarvis-venv/bin/ruff format apps/jarvis
work/jarvis-venv/bin/ruff check apps/jarvis
work/jarvis-venv/bin/ruff format --check apps/jarvis
work/jarvis-venv/bin/pyright --project work/pyright-jarvis.json
work/jarvis-venv/bin/python -m compileall -q apps/jarvis/src apps/jarvis/migrations
work/jarvis-venv/bin/python -m build --no-isolation apps/jarvis --outdir work/jarvis-dist
JARVIS_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-test@127.0.0.1:55432/jarvis work/jarvis-venv/bin/alembic -c apps/jarvis/alembic.ini upgrade head

# From apps/jarvis; targeted test runs also exercised policy/provider and PostgreSQL files.
../../work/jarvis-venv/bin/python -m pytest -q
JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-test@127.0.0.1:55432/jarvis_test ../../work/jarvis-venv/bin/python -m pytest -q tests/test_postgres.py
JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-test@127.0.0.1:55432/jarvis_test ../../work/jarvis-venv/bin/python -m pytest -q

# Back at the repository root.
.venv/bin/graphify query 'apps/jarvis/src/jarvis/engine.py Engine approve PolicyEngine' --budget 800
.venv/bin/graphify explain 'apps/jarvis/src/jarvis/engine.py::Engine'
git diff --cached --check
```

Docker commands explicitly targeted the managed local daemon, clearing inherited
endpoint/context/TLS selectors. Ran `docker ... info`, `run -d --name
jarvis-test-postgres -e POSTGRES_USER=jarvis -e POSTGRES_PASSWORD=jarvis-local-test
-e POSTGRES_DB=jarvis -p 127.0.0.1:55432:5432 postgres:17-alpine`, and `exec
jarvis-test-postgres createdb -U jarvis jarvis_test`. Smoke scripts under work
started a loopback uvicorn server with a generated private token and verified
health/auth/Engineer HTTP behavior. The temporary server was then stopped.

The verification venv had a local .pth pointing to the already installed upstream
Graphify source/dependencies; that scratch convenience is not in the deliverable.
Normal installation uses the documented root uv environment and editable app.
No root pyproject/uv.lock changes are necessary.

## Files

Core Graphify changes: **none**. Small additive edits: `.gitignore`, `README.md`,
`ARCHITECTURE.md`, `SECURITY.md`. New source, tests, lock, CI, migration and docs:

- `.github/workflows/jarvis.yml`
- `JARVIS_PLAN.md`
- `JARVIS_PROGRESS.md`
- `JARVIS_REVIEW.md`
- `THREAT_MODEL.md`
- `apps/jarvis/.env.example`
- `apps/jarvis/MANIFEST.in`
- `apps/jarvis/README.md`
- `apps/jarvis/alembic.ini`
- `apps/jarvis/compose.yaml`
- `apps/jarvis/migrations/env.py`
- `apps/jarvis/migrations/versions/0001_foundation.py`
- `apps/jarvis/pyproject.toml`
- `apps/jarvis/requirements.lock`
- `apps/jarvis/src/jarvis/__init__.py`
- `apps/jarvis/src/jarvis/api.py`
- `apps/jarvis/src/jarvis/config.py`
- `apps/jarvis/src/jarvis/db.py`
- `apps/jarvis/src/jarvis/domain.py`
- `apps/jarvis/src/jarvis/engine.py`
- `apps/jarvis/src/jarvis/graph.py`
- `apps/jarvis/src/jarvis/graph_worker.py`
- `apps/jarvis/src/jarvis/models.py`
- `apps/jarvis/src/jarvis/paths.py`
- `apps/jarvis/src/jarvis/policy.py`
- `apps/jarvis/src/jarvis/tools.py`
- `apps/jarvis/tests/conftest.py`
- `apps/jarvis/tests/test_engine_api.py`
- `apps/jarvis/tests/test_graph_security.py`
- `apps/jarvis/tests/test_policy_models.py`
- `apps/jarvis/tests/test_postgres.py`
- `apps/jarvis/tests/test_sdk_errors.py`
- `apps/jarvis/tests/test_streaming.py`
- `docs/jarvis/ARCHITECTURE.md`
- `docs/jarvis/GAME_MASTER.md`
- `docs/jarvis/GRAPHIFY_INTEGRATION.md`
- `docs/jarvis/LOCAL_DEVELOPMENT.md`
- `docs/jarvis/MASTER_SPEC.md`
- `docs/jarvis/MEMORY.md`
- `docs/jarvis/MODEL_ROUTING.md`
- `docs/jarvis/POLICY.md`
- `docs/jarvis/UPSTREAM_BASELINE.md`
- `docs/jarvis/UPSTREAM_BOUNDARY.md`
- `JARVIS_ENGINEERING_REPORT.md`

## Deferred work and next task

Phases 5–10 are pending: personal memory/pgvector/context inspector, OS-isolated
Engineer editing/testing/worktrees, Tutor evidence/mastery, canonical GM state/
visibility/dice/rules/transcripts, responsive Command Center/PWA, optional voice.
Watchers/integrations and full production hardening remain pending. Scope checks
and adversarial review were applied to this checkpoint only.

Production still requires multi-user identity/session/OAuth, TLS and secret
rotation, restricted DB role, deployment/worker coordination, request quotas,
budget enforcement, integration idempotency and true untrusted-code sandboxing.
Do not run multiple API workers or publicly deploy this local prototype.

**Next recommended task:** execute phase 5 from JARVIS_PROGRESS.md: structured
personal memory and source provenance, owner/visibility filtering before model
context, bounded ContextBuilder, inspector APIs and fake embedding tests. Preserve
and rerun the existing JARVIS/PostgreSQL tests, relevant upstream checks, update
Graphify, review security and record actual results.

## Demonstrations

Setup: `docs/jarvis/LOCAL_DEVELOPMENT.md` and `apps/jarvis/.env.example`.

- **A — Code intelligence:** index/update registered project; graph query/explain/
  path/impact API; inspect source/confidence in durable run result.
- **B — Engineer:** graph-first text analysis works. Editing/worktree/test/diff
  E2E is deferred to phase 6; adapter change-update-impact fixture tests pass.
- **C — Chief of Staff:** generic text runs and approval contract work; projects/
  checkpoints/personal retrieval are pending. Fake external approval demo is tested.
- **D — Tutor:** generic independent text mode only; quizzes/mastery pending phase 7.
- **E — Game Master:** generic independent text mode only; campaign secrets,
  player/NPC dice and canonical event proposals pending phase 8.

The handoff in `CODEX_HANDOFF.md` provides a dedicated GitHub branch workflow and
a self-contained Git bundle preserving source and upstream history. The delivery
manifest identifies the checkpoint; checksums cover portable artifacts. The source
ZIP is also retained as a snapshot. This cloud environment cannot create the
designated chat download directory (`/codex/.../output`); no downloadable chat
attachment/link is claimed. Publish the checkpoint branch to the user's existing
fork for another Codex cloud session, or clone the bundle for local Codex.
The built wheel requires Graphify installed alongside it and the source
migration/configuration files; it is not a standalone deployed product.
