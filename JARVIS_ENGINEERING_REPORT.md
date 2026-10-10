# JARVIS engineering report — 2026-10-10

A runnable **Tutor checkpoint** is implemented in the existing Graphify
repository. It completes the bounded phases 0–7 scope in JARVIS_PLAN.md. The full
personal AI operating system specification is not complete.

Repository: `/workspace/graphify`; active published branch `jarvis/phase-7-tutor`;
receiving checkpoint `b5c613ffae1163b30e5b8c9897afec6abce175ea`, the published
Phase 6 tip. Original Graphify parent `5c7b84792f453582676548185aaec3824d51dfe2`,
release 0.9.77, is preserved. The user authorized the Phase 7 push on 2026-10-10;
implementation commit `6d35a7bf22b17b299150ae8731082ac19c41f90d` is on the remote
branch. No merge or deployment occurred. The published Phase 6 history remains
documented below.
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
- Structured personal memory, provenance, scoped semantic/lexical retrieval,
  bounded explainable context, authenticated inspector/export/correction/deletion
  APIs, and human acceptance for inactive model proposals. See MEMORY.md.
- Source-grounded Tutor objectives, cited lessons/quizzes, authenticated human
  attempts, deterministic evidence-backed mastery and persisted spaced reviews.

The four mode identifiers exist and keep independent run context. Dedicated
Chief of Staff and Game Master workflows are pending. Only opt-in kernel-isolated system-Python execution is registered when verified;
no host shell or real external-write integration is registered. Fake integration
fixtures prove approval behavior without performing external communications.

## Foundation verification history

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

## Foundation-era deferred work and next task (historical)

At the foundation checkpoint, phases 6–10 were pending: OS-isolated
Engineer editing/testing/worktrees, Tutor evidence/mastery, canonical GM state/
visibility/dice/rules/transcripts, responsive Command Center/PWA, optional voice.
Phases 6 and 7 are now implemented in later sections. Game Master, Command Center,
voice, watchers/integrations and full production hardening remain pending.

Production still requires multi-user identity/session/OAuth, TLS and secret
rotation, restricted DB role, deployment/worker coordination, request quotas,
budget enforcement, integration idempotency and true untrusted-code sandboxing.
Do not run multiple API workers or publicly deploy this local prototype.

**Foundation-era next task (historical):** phase 6: isolated
Engineer worktrees, Graphify retrieval/impact, constrained OS worker, regression
execution and reviewed diffs. Establish isolation before enabling shell/code
execution. Preserve the memory visibility, provenance and lifecycle guarantees
and rerun the existing JARVIS/PostgreSQL tests, relevant upstream checks, update
Graphify, review security and record actual results.

## Demonstrations

Setup: `docs/jarvis/LOCAL_DEVELOPMENT.md` and `apps/jarvis/.env.example`.

- **A — Code intelligence:** index/update registered project; graph query/explain/
  path/impact API; inspect source/confidence in durable run result.
- **B — Engineer:** graph-first text analysis works. Editing/worktree/test/diff
  E2E was deferred at the foundation checkpoint; phase 6 below now covers it.
- **C — Chief of Staff:** generic text runs and approval contract work; projects/
  checkpoints are pending; personal memory/context works. Fake external approval demo is tested.
- **D — Tutor:** source-grounded objectives, cited material, quizzes, authenticated
  human attempts, deterministic mastery evidence and spaced reviews are implemented.
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

## Phase 5 implementation and verification

Application 0.2.0 adds a separate memory database boundary, retaining the Graphify
source, CLI, package metadata, root lock, licenses and generated skills unchanged.
New source modules: memory.py, memory_schema.py, memory_api.py, memory_tools.py,
context.py and embeddings.py. Immutable migration 0002 adds MemoryItem,
MemorySource and MemoryProposal without rewriting foundation schema/history.
Configuration, run/model input preparation, typed execution context, inspector
router, CI and tests extend the existing package. Full source requirements remain
in MASTER_SPEC.md; the dedicated mode/UI program is not claimed complete.

Owner/namespace/mode/visibility/lifecycle predicates precede candidate reads and
ranking. Required sources retain IDs, locators, quotes, timestamps and hashes of
supplied source assertions. Correction creates linked immutable revisions;
eligible deletion purges their content/sources/embeddings and accepted proposal
payloads. PostgreSQL lock/claim tests cover edit/delete and acceptance races.
WORKING state is session-scoped and expires without extending on correction;
EPISODIC/CANONICAL retention is protected through this inspector. Canonical memory
cannot modify authorization, campaign state or learner mastery.

Context combines only relevant fitting class records and separate Graphify tool
evidence. It labels personal memory as untrusted data, counts UTF-8 bytes/framing
as a conservative token bound including registered tool schemas, records
retrieval explanations/source IDs and
rebuilds before model calls. It revalidates after embedding awaits and refilters
historical memory tools. Models can propose inactive notes, with run-bound actor/
mode/namespaces; only explicit human acceptance creates active memory. No memory
text can grant permissions or bypass exact protected-tool approvals.

Deterministic fake embeddings default to an offline bounded retrieval path.
Official SDK live embeddings require configured model/dimension/key. Optional
pgvector runs real cosine SQL on already-authorized candidate IDs; the operator
must explicitly enable the flag and install the extension. The default fixed
migration is independent of extension availability. No ANN index, cross-owner
sharing, campaign membership, background expiry purge or dedicated inspector UI
is claimed; MEMORY.md documents these limits and separate transcript retention.

| Phase-5 check | Actual result |
|---|---|
| Receiving foundation baseline | 59 passed including PostgreSQL (6.51 s), lint/format/types passed |
| Final complete application + ordinary PostgreSQL | 106 passed, 1 optional-vector skip (15.27 s) |
| Final complete application + PostgreSQL/pgvector | 106 passed, 1 missing-extension skip (14.05 s) |
| Application lint/format/types | Passed; 30 files formatted; 0 type errors/warnings |
| Migration/metadata/foundation persistence | Upgrade/downgrade/upgrade and 0001 → 0002 sentinel retained |
| Memory concurrency and lifecycle | Correction/delete races, one-use proposal acceptance, reconnect, no stale resurrection passed |
| Security and provenance | Owner/namespace/mode/GM filters, filter-before-limit, injection denial, Unicode budgets, deleted-tool refresh, grounded fake citations passed |
| Real migrated loopback HTTP / pgvector | Health 200, unauthorized 401, create 201, search/chat provenance, correction 200/stale 409, delete 204, empty search/export |
| 0.2.0 wheel and source distribution | Built successfully; source migrations/tests included |
| Full upstream regression | 6,470 passed, 108 skipped, same 9 failures (119.53 s); no new failures |

The application suite requires no paid service. Both vector CI configurations were
added; local runs verify them, without claiming a remotely executed CI result.
Complete logs/builds/smoke evidence are in ignored work/. Portable summaries and
failure comparison are in docs/jarvis/verification. JARVIS_REVIEW.md records fixes,
including a deletion/embedding race and real pgvector parameter-binding issue.
At the phase-5 checkpoint, the handoff resumed phase 6. The current prompt
now resumes phase 7.

## GitHub configuration correction — 2026-10-07

The foundation push completed successfully. GitHub Actions run 37407305664 then
failed its type-check step with nine missing Graphify imports; tests and builds
were skipped. A fresh checkout using all three workflow installation commands
reproduced those errors. Pyright cannot follow the root setuptools editable
import hook, so the application config now explicitly adds the repository root
as `extraPaths = ["../.."]`. No checks were disabled or upstream files changed.

In that fresh environment, lint and format passed (30 files), Pyright reported
zero errors/warnings, wheel/sdist built, and the complete suites passed on both
PostgreSQL (106 passed, 1 skip; 11.50 s) and pgvector (106 passed, 1 skip; 12.71 s).
These observations are local; GitHub Actions provides the remote run outcome.
The user explicitly authorized publication of the complete Phase 5 branch.

## Phase 6 implementation and review — 2026-10-07

Receiving branch was clean jarvis/phase-5-memory at 5f622c0. Its unchanged suite
passed 106 tests with one skip (10.04 s); lint/format/types passed. Work continued
on a new local jarvis/phase-6-engineer branch. No regeneration or upstream rewrite.

Application 0.3.0 adds engineer.py, engineer_schema.py, engineer_tools.py and
sandbox.py plus test_engineer.py. Small integration edits cover API/config/tool
context/run failure metadata/source hashes. CI now installs the Linux runtime and
opts into real-kernel tests. No new Python dependency or schema migration was
needed; root/app locks and existing migrations remain unchanged. Engineer state
is generated artifact storage, while PostgreSQL keeps authoritative run status,
transitions and audit. Application architecture/policy/setup/threat/review/handoff
and continuation documentation were updated, including ENGINEER.md.

The change pipeline queries Graphify, reads safe tracked source, verifies target
hashes, creates a fresh sanitized Git snapshot repository and real detached
worktree, edits privately, computes a real Git diff, executes declared commands
in a verified read-only offline OS worker, updates the changed graph, computes
impact, rechecks original sources and returns owner/run-scoped artifacts. Dry runs
say NOT_RUN. Nonzero exits, output overflow, deadlines, stale sources and resource
failures cannot become successful AgentRuns. Actual source application, repository
commits, pushes, merges and deployment are not registered. This application
workflow does not perform the separate Git checkpoint action of this coding task.

Bubblewrap's kernel probe checks PID/network isolation, UID/capability drop,
no-new-privileges, hard process bounds and sanitized environment before tool
registration. prlimit caps CPU/address space/file/descriptors; tmpfs caps aggregate
temporary writes. No host fallback, application secrets, Git metadata, network or
project dependency installation are available in the worker. Requirements/limits
are documented precisely; production cgroup memory quotas, kernel defense in
depth and multi-worker operation remain future work. Command support is system
Python's standard library, not an unrestricted multi-language development image.

Tests found and fixed process-cap placement during namespace setup, a writable
private-root mount, generated PWD handling in readiness, CPU-signal wrapper exit
representation and bounded Unicode report previews. Adversarial cases include
symlink/path/credential targets, host/runtime/source writes, network, environment
secrets, malicious Git hooks/filter configuration and README instructions, CPU/
memory/process/file/tmpfs/log/wall limits, cancellation, stale hashes, source
changes during tests, artifact ownership/retention and policy denial. Fake-model
E2E traverses graph evidence → typed change → policy → real worker → durable result.
No paid provider call was required. JARVIS_REVIEW.md records the self-review.

Real migrated loopback HTTP smoke passed health 200, unauthorized 401, kernel
readiness, change submission 202, run COMPLETED/VERIFIED, artifact 200 and artifact
discovery. Source stayed unchanged; worker/server stopped afterward. Temporary
fixtures/database/artifacts remain isolated scratch, not user data.

Exact current commands (from apps/jarvis, fresh workflow dependency environment):

```sh
../../.venv/bin/ruff check .
../../.venv/bin/ruff format --check .
../../.venv/bin/pyright
JARVIS_TEST_SANDBOX=true JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-test@127.0.0.1:55432/jarvis_test ../../.venv/bin/python -m pytest -q
JARVIS_TEST_SANDBOX=true JARVIS_TEST_PGVECTOR=true JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-local-test@127.0.0.1:55433/jarvis_vector_test ../../.venv/bin/python -m pytest -q
```

Root commands actually executed:

```sh
PATH=/workspace/graphify/.venv/bin:/usr/local/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/ -q
work/jarvis-venv/bin/python -m build --no-isolation --outdir work/phase6-build apps/jarvis
work/jarvis-venv/bin/python work/phase6-http-smoke.py
.venv/bin/graphify update .
```

Raw logs/builds are in ignored work/phase6-* and recorded summaries are in
docs/jarvis/verification/. The initial restricted upstream run had 6,469 passes,
108 skips and ten failures, including an additional denied Unix socket. The
local-socket-authorized full run had 6,472 passes, 108 skips and seven existing
DNS-dependent failures (146.91 s). Comparison against Phase 5 shows no new failure
identifier. No upstream source/test/metadata/license drift was changed to make
checks pass. Graph synchronization produced 19,296 nodes, 40,153 edges and 1,109
communities; no paid labeling was run.

Next: phase 7 Tutor objectives/quizzes/learner-evidence mastery/review tasks.
Chief of Staff/watchers, campaigns and dice, frontend/PWA, optional voice,
integrations and complete production hardening remain pending. The Phase 6 branch
was subsequently published with explicit user authorization. No merge,
deployment or live-model availability is claimed.

Final fresh-environment suites: **137 passed, 1 skipped** on PostgreSQL (23.66 s)
and **137 passed, 1 skipped** on pgvector (21.44 s). Lint/format/types passed
(35 Python files, zero type errors/warnings); the 0.3.0 wheel/sdist built and package
source parity was checked. Full verification and preserved-boundary evidence are
recorded in JARVIS_PROGRESS.md and docs/jarvis/verification/. These are local
results; inspect the published branch's GitHub Actions for remote verification.

## Phase 6 publication compatibility

The first GitHub run (37635312503) passed dependency installation and static
checks but failed real isolation setup on Ubuntu's Bubblewrap 0.9.0. It reported
`loopback: Failed RTM_NEWADDR: Operation not permitted`. Setting no-new-privileges
before the trusted Bubblewrap executable transition can interfere with an
AppArmor launcher profile. The explicit wrapper now runs inside the isolated worker,
before Python; real
probes continue to require UID 65534, zero capabilities and no-new-privileges.
Remote run 37635976274 showed that this change alone was insufficient. Ubuntu's
distribution-supplied `bwrap-userns-restrict` launcher/child profile is now installed
in CI, while global AppArmor user namespace restrictions are explicitly required
to remain enabled. No host security control or opt-in real test was disabled.

Both full local suites passed after this adjustment: PostgreSQL **137 passed,
1 skipped** (28.01 s), pgvector **137 passed, 1 skipped** (28.29 s). Ruff checks,
format and Pyright passed, and Graphify was updated after the code edit. Remote
verification is recorded by subsequent GitHub Actions runs on the branch.

## Phase 7 Tutor implementation and review — 2026-10-10

Phase 7 resumed from published Phase 6 tip
`b5c613ffae1163b30e5b8c9897afec6abce175ea` on a new local
`jarvis/phase-7-tutor` branch. The receiving source was clean. Its retained JARVIS
environment passed Ruff/format/Pyright and 129 tests with nine database-specific
skips before implementation. The fresh root environment lacked the prior editable
JARVIS install; that setup error was recorded separately and was not a source failure.

Application 0.4.0 adds dedicated Tutor schema/service/API/tools and additive
migration 0003. Learning objectives require bounded source excerpts with locator,
quote and hash. Explanations, worked examples, Socratic prompts and quizzes must
cite sources owned by that objective. Accepted short answers are normalized and
hashed; they are never returned by quiz or context APIs.

Learner attempts enter only through the authenticated attempt endpoint and are
server-stamped `HUMAN_API`. Strict inputs cannot supply correctness, score,
evaluator, origin or mastery. Exact duplicate submissions are idempotent; mutated
replays conflict. The latest attempt per distinct quiz drives a deterministic
threshold. A one-time mastery record contains exact attempt IDs, score and
evaluator. It schedules persisted 1/3/7/14/30-day reviews; completion requires a
correct human attempt made at or after the due time.

Tutor model tools are TUTOR/objective/capability bound and limited to context,
lesson and quiz operations. There is no model tool for attempts, grading, mastery
or reviews. Prompt-injected source text stays untrusted data. Canonical Tutor state
is independent of personal memory.

Hostile review found and fixed same-timestamp retry ordering and premature reuse
of pre-due attempts for review evidence. PostgreSQL locks and unique constraints
were exercised with concurrent duplicate and distinct-quiz attempts. Migration
0002→0003 preserved existing memory and append-only audit records.

Full local suites with real kernel tests passed **152 tests, 1 skipped** on
ordinary PostgreSQL (31.70 s) and **152 tests, 1 skipped** on pgvector (31.38 s).
Ruff/format/Pyright passed for 41 Python files with zero type errors/warnings.
The 0.4.0 wheel/sdist, migrated PostgreSQL API smoke, relevant upstream architecture
tests, preserved-boundary diff and scoped Graphify query/explain all passed. The
graph contains 19,425 nodes, 40,630 edges and 1,041 communities. No paid provider,
merge, deployment or outbound communication was used. The checkpoint was later
pushed to its dedicated GitHub branch with user authorization.

Next: phase 8 Game Master canonical campaign state, visibility-before-context,
ScenePacketBuilder, rules/dice and roll authority. Chief of Staff/watchers,
frontend/PWA, voice/integrations and complete production hardening remain pending.
