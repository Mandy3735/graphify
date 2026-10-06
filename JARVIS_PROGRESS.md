# JARVIS progress — 2026-10-05

Repository `/workspace/graphify`; branch `jarvis/foundation`; parent commit
`5c7b84792f453582676548185aaec3824d51dfe2` (Graphify 0.9.77).
The foundation is prepared as a reviewable checkpoint on `jarvis/foundation`.
`CODEX_HANDOFF.md` explains transfer and continuation. The delivery manifest and
remote branch establish checkpoint identity and publication status; no deployment
is part of this handoff.

## Delivered checkpoint

Phases 0–4, bounded to the foundation defined in JARVIS_PLAN.md:

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

## Actual checks

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

## Not done

Phases 5–10 (personal memory/pgvector/context/inspector, sandboxed Engineer edits,
Tutor, Game Master, Command Center/PWA, voice), watcher/transcript/integration
workflows, and complete production hardening/full-program adversarial acceptance
remain pending. Phases 11–12 checks/review were applied only to delivered scope.
No frontend build/tests or live paid model call is claimed. The full specification
definition of done is not met by this foundation checkpoint.

## Exact next milestone

Phase 5: PostgreSQL personal memory with explicit memory classes, ownership and
visibility; provenance; relevance/token budgets; ContextBuilder; memory inspector
APIs and security tests. Keep Graphify separate. Add pgvector only behind config
and preserve an offline retrieval path with fake embeddings.

Recommended next Codex instruction:

> Continue JARVIS phase 5 from JARVIS_PROGRESS.md and JARVIS_PLAN.md. Preserve
> Graphify and the verified foundation. Implement structured personal memory,
> provenance, owner/visibility filtering before retrieval, a bounded ContextBuilder,
> inspector APIs and deterministic embedding tests. Run existing JARVIS and
> PostgreSQL tests plus appropriate upstream checks, synchronize Graphify, review
> security, and update progress without claiming later modes are complete.

Setup/demonstrations: docs/jarvis/LOCAL_DEVELOPMENT.md. Review: JARVIS_REVIEW.md.
