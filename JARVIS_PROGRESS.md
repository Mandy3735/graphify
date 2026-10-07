# JARVIS progress — 2026-10-07

Repository `/workspace/graphify`; active branch `jarvis/phase-5-memory`; parent
checkpoint `b04e109ab2d15967d06dff364f376de41e92bde0` (`jarvis/foundation`).
Original Graphify 0.9.77 parent: `5c7b84792f453582676548185aaec3824d51dfe2`.
Phase-5 implementation commit: `dc37855efea99f2074e5fe6e686df2a62b5ac6e3`.
The GitHub handoff branch is `jarvis/phase-5-memory`, including a subsequent
type-check configuration fix. The earlier `jarvis/foundation` remains available.
No deployment or merge is part of this handoff.

## GitHub check configuration verification — 2026-10-07

The foundation push succeeded, but workflow run 37407305664 stopped at Pyright:
nine Graphify imports were unresolved. Setuptools' editable import hook works
at runtime but cannot be followed by Pyright. JARVIS now explicitly configures
`extraPaths = ["../.."]` relative to its own pyproject.toml. No diagnostic was
disabled, and no upstream source or root lock was changed.

A fresh checkout using the exact workflow installation commands reproduced the
nine errors before the fix. After the fix: Ruff lint/format passed, Pyright
reported zero errors/warnings, both wheel and sdist built, ordinary PostgreSQL
passed 106 tests with one skip (11.50 s), and pgvector passed 106 tests with one
skip (12.71 s). These are local results; inspect GitHub Actions for remote status.

## Delivered checkpoint

Phases 0–5, bounded to the application scope defined in JARVIS_PLAN.md:

- Upstream reconnaissance, complete baseline, boundary and milestone plan.
- Independent application package/dependency lock; FastAPI/OpenAPI; authenticated
  single-user API; SQLAlchemy async PostgreSQL; immutable Alembic schema; local
  Compose; independent CI additions; startup recovery without effect replay.
- Bounded Graphify health/index/update/query/explain/path/impact, preserving
  provenance/confidence/direction and semantic contributions. Safe snapshot parser
  worker, path/byte limits, operator registrations and credential-free environment.
- Fake/official OpenAI Responses providers, configuration-driven model selection,
  explicit fallback, SDK streaming/error mapping, usage/cost metadata, durable runs,
  legal transitions, cancellation, SSE state updates and per-run budgets.
- Typed concrete graph/workspace tools, deterministic capability/risk policy,
  exact one-use approval, expiry/mutation/replay/revocation protection, PostgreSQL
  transaction tests and append-oriented audit with DB mutation guard.
- Engineer text requests query Graphify before model analysis when project_id is
  supplied. Four mode labels keep independent run context; dedicated mode workflows
  are not yet implemented. No arbitrary execution or real external writes enabled.
- WORKING/EPISODIC/SEMANTIC/CANONICAL/PREFERENCE memory with required sources,
  owner-scoped namespaces, mode/visibility/expiry filtering before retrieval,
  linked revision corrections, eligible lineage deletion and append-only audit.
- Deterministic offline embeddings and official SDK live embedding adapter;
  optional pgvector cosine SQL for bounded authorized candidates. Provider keys
  prevent mixing incompatible vectors; lexical retrieval remains available.
- ContextBuilder uses current request/mode/project/campaign/session and trusted
  capability scope, with token/character budgets and explainable source references.
  Live memory is rechecked after embedding awaits and before subsequent model
  context; automatic memory contents are not copied to durable run messages.
- Authenticated inspector/search/create/correction/delete/export APIs. Models have
  run-scoped memory.search and inactive memory.propose_write; only explicit human
  acceptance creates active memory. Canonical/GM-secret model proposals are denied.
- Additive immutable migration 0002, application 0.2.0, and PostgreSQL/pgvector CI
  configurations. No root Graphify code, dependencies, licenses or locks changed.

## Foundation verification history

| Check | Observed result |
|---|---|
| Initial default-PATH upstream suite | Interrupted installer resolution: 5,659 passed, 102 skipped, 28 failed at interruption |
| Complete offline upstream baseline | 6,439 passed, 108 skipped, 40 failed (103.15 s) |
| Upstream after installing missing optional test dependencies | 6,470 passed, 108 skipped, 9 failed (119.41 s); all 9 were pre-existing |
| Upstream architecture documentation after additive links | 38 passed, 1 warning |
| Root Ruff lint | Passed |
| Root formatter baseline | 430 files would reformat, 23 already formatted — pre-existing drift |
| Root Pyright with explicit venv | 639 errors, 4 warnings — existing upstream issues/dependencies |
| Full JARVIS including PostgreSQL | 59 passed (6.01 s), no paid service |
| JARVIS Ruff lint and format | Passed |
| JARVIS Pyright with explicit application venv | 0 errors, 0 warnings |
| PostgreSQL migrations | Upgrade/downgrade/upgrade and metadata consistency passed |
| PostgreSQL concurrency/audit/reconnect | Passed |
| Application wheel and sdist | Built successfully |
| Real HTTP smoke | Health 200; unauthenticated 401; Engineer run completed with Graphify evidence |
| Graph synchronization/query/impact | AST update succeeded; scoped post-change query/impact recorded in work logs |

Root baseline formatter/type failures are not JARVIS failures. The first Pyright
invocations also had interpreter-resolution errors (880/881 errors); explicit venv
configuration reduced this to the documented 639, with no upstream source changes.
Sandboxed SQLite's cross-thread event-loop wakeup stalled; local socket-authorized
test execution completed. No application workaround or weakened test was used.

Remaining upstream failures: one ignore-without-VCS assertion, one hooks test
blocked by the sandbox's read-only `/tmp/.git`, and seven DNS-dependent URL/fetch
security tests in this restricted environment. Full test names/logs are retained.

## Phase 5 actual checks

| Check | Observed result |
|---|---|
| Unchanged receiving foundation baseline | 59 passed, including PostgreSQL (6.51 s); lint/format/types passed |
| Final full suite, ordinary PostgreSQL | **106 passed, 1 skipped** (15.27 s); skip is optional vector SQL |
| Final full suite, PostgreSQL + pgvector | **106 passed, 1 skipped** (14.05 s); skip is missing-extension check |
| Application Ruff lint/format | Passed; 30 Python files formatted |
| Application Pyright | 0 errors, 0 warnings |
| Additive migration / metadata | Upgrade/downgrade/upgrade; 0001 → 0002 retained existing foundation audit |
| PostgreSQL races / persistence | Competing corrections and deletion, proposal acceptance, reconnect, original approvals/audit passed |
| Source-grounded fake E2E / malicious memory | Citations and inspector provenance retained; memory could not gain capability or perform external write |
| Real HTTP with PostgreSQL + pgvector | Health 200, unauthenticated 401, create 201, search/context complete, correction 200/stale 409, delete 204, search/export empty |
| Application 0.2.0 wheel and sdist | Built successfully; migration/tests packaged |
| Post-change upstream architecture docs | 38 passed, 1 warning (0.31 s) |
| Graph synchronization | AST update: 19,202 nodes, 39,798 edges; local query/explain succeeded |
| Full upstream Graphify regression | 6,470 passed, 108 skipped, 9 failed (119.53 s); identical prior failure list, no new failures |

No paid model or embedding call was needed. SDK adapters are covered with fakes.
Portable verification snapshots are in docs/jarvis/verification; complete raw logs
remain in ignored work/. Graph synchronization is recorded there as well.

## Not done

Phases 6–10 (sandboxed Engineer edits,
Tutor, Game Master, Command Center/PWA, voice), watcher/transcript/integration
workflows, and complete production hardening/full-program adversarial acceptance
remain pending. Phases 11–12 checks/review were applied only to delivered scope.
No frontend build/tests or live paid model call is claimed. The full specification
definition of done is not met by this memory checkpoint. Personal memory PUBLIC/
PARTY data remains owner-scoped; campaign membership/sharing is phase 8. The
dedicated memory UI is phase 9. Expired memory is filtered but not background
purged, and conversation/tool transcript retention is distinct from memory
deletion. See MEMORY.md for explicit lifecycle and retrieval limits.

## Exact next milestone

Phase 6: Engineer workflow with Graphify plan/retrieval/impact, isolated worktrees,
a constrained worker, resource/time/output limits, a sanitized environment,
dry-run/diff review and meaningful regression tests. Establish OS isolation before
enabling any untrusted code execution. Preserve memory visibility/provenance,
exact approvals and the existing Graphify/application regression boundary.

Recommended next Codex instruction:

> Read CODEX_HANDOFF.md and docs/jarvis/CODEX_NEXT_PROMPT.md, then implement phase
> 6's sandboxed Engineer workflow. Preserve the verified Graphify, foundation and
> memory checkpoint. Do not register arbitrary host shell execution. Verify the
> actual OS sandbox boundary, Graphify evidence/impact, worktree isolation and
> complete applicable regression checks, review security and update progress.

Setup/demonstrations: docs/jarvis/LOCAL_DEVELOPMENT.md. Review: JARVIS_REVIEW.md.
