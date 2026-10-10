# JARVIS progress — 2026-10-10

Repository `/workspace/graphify`; active local branch `jarvis/phase-7-tutor`;
receiving checkpoint `b5c613ffae1163b30e5b8c9897afec6abce175ea` on the published
`jarvis/phase-6-engineer` branch. Original Graphify parent remains
`5c7b84792f453582676548185aaec3824d51dfe2`. Phase 7 is local and is not pushed,
merged or deployed. Resolve the exact checkpoint with `git rev-parse HEAD` after
the phase-7 commit.

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

Phases 0–7, bounded to the application scope defined in JARVIS_PLAN.md:

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
  supplied. Four mode labels keep independent run context; bounded Engineer and
  Tutor workflows are implemented below. No unrestricted host execution or real
  external-write adapter is enabled.
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
- Phase-5 immutable migration 0002, application 0.2.0, and PostgreSQL/pgvector CI
  configurations. No root Graphify code, dependencies, licenses or locks changed.

- Opt-in kernel-verified Linux Bubblewrap worker: offline read-only source/runtime,
  unprivileged UID, no capabilities, no-new-privileges, disabled nested user
  namespaces and bounded CPU/memory/process/file/output/tmpfs/time resources.
- Graph-first private sanitized Git snapshot repository and real detached worktree;
  expected source hashes, dry-run proposals, actual Git patch, declared tests,
  graph update/impact, source recheck and owner/run-scoped artifacts.
- ENGINEER-only tools and authenticated status/change/artifact APIs; denied
  capabilities cannot execute; failed verification makes the durable run FAILED.
  Source reads expose exact SHA-256 and preview status. Cancellation kills workers,
  cleans intermediates and retains discoverable CANCELLED reports.
- No migration added: schema 0002 and all existing memory/approval/audit contracts
  remain intact. Worker supports system-Python standard-library commands only;
  see docs/jarvis/ENGINEER.md for precise limits and retained-artifact handling.
- Dedicated migration 0003 and owner-scoped Tutor objectives/sources, cited
  explanation/worked-example/Socratic artifacts, quizzes with hashed accepted
  answers, authenticated human attempts and deterministic evaluation.
- Mastery requires the latest correct HUMAN_API attempts across the configured
  distinct-quiz threshold and retains exact evidence IDs. Models have no attempt,
  mastery or review-completion tool. One-use submission IDs and objective locks
  cover retries/races. Persisted reviews require a new correct attempt at/after due.

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

## Phase 6 actual checks — local checkpoint

| Check | Observed result |
|---|---|
| Receiving phase-5 baseline | 106 passed, 1 skip (10.04 s); lint/format/types passed |
| Final fresh-environment PostgreSQL + real sandbox | **137 passed, 1 skipped** (23.66 s) |
| Final fresh-environment pgvector + real sandbox | **137 passed, 1 skipped** (21.44 s) |
| Real-kernel / workflow coverage | Isolation, resource limits, cancellation, artifact ownership, stale sources, policy denial and fake-model E2E passed |
| Ruff lint/format / Pyright | Passed; 35 Python files formatted; zero type errors/warnings |
| Application 0.3.0 wheel/sdist | Built successfully; source/test/binary parity checked |
| Real migrated loopback HTTP | Health 200, unauthorized 401, sandbox ready, submit 202, COMPLETED/VERIFIED, artifact 200, original source unchanged |
| Full authorized upstream regression | 6,472 passed, 108 skipped, 7 existing DNS failures (146.91 s); no new failure identifier |
| Restricted upstream run | 6,469 passed, 108 skipped, 10 failed; additional Unix-socket restriction resolved with local-socket authorization |
| Graph synchronization / navigation | 19,296 nodes, 40,153 edges, 1,109 communities; scoped query/explain worked |
| Preserved boundary | No changes to Graphify core/tests, root metadata/lock, licenses, skill generation, application lock or existing migrations |

The kernel suite is opt-in; these runs explicitly enabled it and did not skip
unavailable OS isolation. The single skip in each full run covers the opposite
vector configuration. No paid provider call, source apply, merge or deployment
was performed. The subsequently authorized GitHub push is recorded above;
inspect GitHub Actions for remote results. Recorded local snapshots are in
`docs/jarvis/verification/phase6-*`; full logs/builds stay in ignored work/.

## Phase 6 GitHub publication check

Initial remote run [37635312503](https://github.com/Mandy3735/graphify/actions/runs/37635312503)
passed installation, lint, format and typing, but failed the real sandbox tests:
Ubuntu Bubblewrap reported `loopback: Failed RTM_NEWADDR: Operation not permitted`.
The wrapper was moved inside Bubblewrap before Python to permit an AppArmor
launcher transition, preserving all worker restrictions. Remote run 37635976274
showed that this adjustment alone was insufficient. CI now also installs Ubuntu's
child-restricting `bwrap-userns-restrict` profile and checks that global AppArmor
user namespace restrictions stay enabled. No real kernel checks are skipped.

After the fix, local full suites passed **137 tests, 1 skip** on PostgreSQL
(28.01 s) and pgvector (28.29 s); Ruff lint/format and Pyright passed. The Graphify
index was synchronized. Inspect subsequent GitHub runs for the remote verdict.

## Phase 7 actual checks — local checkpoint

| Check | Observed result |
|---|---|
| Receiving Phase 6 baseline | 129 passed, 9 database-specific skips (16.44 s); Ruff/format/Pyright passed |
| PostgreSQL + real sandbox | **152 passed, 1 skipped** (31.70 s) |
| PostgreSQL/pgvector + real sandbox | **152 passed, 1 skipped** (31.38 s) |
| Tutor E2E/adversarial coverage | Objective, cited lesson/quizzes, wrong answer/retry, duplicate replay, human evidence mastery, due review, owner/grant/source/injection boundaries |
| Migration/persistence/races | 0002 → 0003 preserves memory/audit; duplicate and concurrent distinct attempts produce one mastery record |
| Ruff lint/format / Pyright | Passed; 41 Python files formatted; zero type errors/warnings |
| Real migrated PostgreSQL API smoke | Unauthorized 401; objective 201; two HUMAN_API attempts changed ACTIVE → MASTERED; exact two-quiz/100% evidence; review 1 scheduled; no model attempt tool/answer exposure |
| Application 0.4.0 wheel/sdist | Built successfully; migration, Tutor source and tests packaged |
| Relevant upstream/preserved boundary | Architecture tests: 38 passed, 1 warning (0.31 s); no changes to Graphify core/tests, root metadata/lock/licenses, skill generation, application lock or migrations 0001/0002 |
| Graph synchronization/navigation | 19,425 nodes, 40,630 edges, 1,041 communities; scoped TutorService query/explain succeeded |

Both full runs explicitly enabled `JARVIS_TEST_SANDBOX=true`; real Engineer kernel
tests were not skipped. The single skip in each run is the opposite pgvector
configuration. No paid provider, live model, external write, push, merge or
deployment was used. The unchanged upstream boundary made a second full Graphify
regression unnecessary; the relevant architecture suite and exact preserved-path
diff were run. Portable result snapshots are in `docs/jarvis/verification/`.

## Not done

Phases 8–10 (Game Master, Command Center/PWA, voice), Chief of Staff project/watcher,
transcript/integration
workflows, and complete production hardening/full-program adversarial acceptance
remain pending. Phases 11–12 checks/review were applied only to delivered scope.
No frontend build/tests or live paid model call is claimed. The full specification
definition of done is not met by this Tutor checkpoint. Personal memory PUBLIC/
PARTY data remains owner-scoped; campaign membership/sharing is phase 8. The
dedicated memory UI is phase 9. Expired memory is filtered but not background
purged, and conversation/tool transcript retention is distinct from memory
deletion. See MEMORY.md for explicit lifecycle and retrieval limits.

## Exact next milestone

Phase 8: structured canonical campaigns, membership/visibility enforcement before
model context, ScenePacketBuilder, rules plugins, deterministic dice and bounded
roll-authority delegation/state proposals. Preserve Tutor learner-evidence and all
earlier authorization/sandbox/memory guarantees.

Recommended next Codex instruction:

> Read CODEX_HANDOFF.md and docs/jarvis/CODEX_NEXT_PROMPT.md, then implement phase
> 8's Game Master workflow. Preserve Graphify, memory, approvals, Tutor evidence
> and the opt-in kernel sandbox. Enforce GM visibility before model context.

Setup/demonstrations: docs/jarvis/LOCAL_DEVELOPMENT.md, ENGINEER.md and TUTOR.md. Review:
JARVIS_REVIEW.md. This checkpoint does not complete the full original specification.
