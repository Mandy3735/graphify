# Adversarial review — foundation and phase 5 checkpoint

Reviewed the delivered API/model/run/tool/Graphify/persistence boundary as a hostile
reviewer. This is source/test review, not a third-party penetration test. Future
features are not counted as complete merely because their names exist in config.

## High-severity findings fixed

1. **Approval could arrive while the paused task was still finishing.** A durable
   approval might be consumed before task scheduling rejected the still-running
   task, losing execution. Resume now waits for the previous paused task and then
   executes exactly once. A timing-controlled regression test exercises this.
2. **Approval proof needed rechecking immediately before the side effect.** The
   executor now requires a matching consumed actor/run/operation/nonce/expiry hash
   for protected risks, and reevaluates current mode/capability policy. Mutation,
   replay, revocation and competing PostgreSQL claims are tested.
3. **Path checks needed to survive filesystem races.** Descriptor-relative,
   no-follow traversal and atomic same-directory writes replace resolve-then-open
   patterns. Reads reject non-regular, oversized and multiply linked files.
   Graphify receives a safely staged source snapshot; the parser worker gets only
   PATH/LANG/PYTHONHASHSEED, not application credentials. No shell tool is enabled.
4. **High-stakes utility selection and failed fallback lacked sufficient records.**
   High-stakes requests select the configured reasoning model even when utility
   routing is requested; no high-stakes fallback. Selected models, failed attempts,
   usage and successful fallback are persisted/audited without provider secrets.

## Foundation verification history

Full JARVIS unit/security/fixture/PostgreSQL suite: **59 passed**. Ruff lint/format
and Pyright: passed; wheel/sdist build: passed. Real HTTP/PostgreSQL smoke: health
200, authentication 401 without token, Engineer run completed with Graphify data.
Upstream regression: 6,470 passed, 108 skipped, 9 failed; every remaining failure
was present in the initial complete baseline. Architecture-doc tests: 38 passed.

## Phase 5 review and fixes

- Owner, namespace, mode, visibility and expiry predicates are applied in SQL
  before candidate limits/ranking/source reads. Tests place more unauthorized
  matching records than the candidate cap to catch filter-after-limit mistakes.
- GM-secret memory requires a trusted capability plus GM mode; forged mode,
  another owner, PUBLIC/PARTY visibility and inspector/export/history requests
  cannot broaden authority. No campaign membership implementation is claimed.
- **Deletion during an embedding await initially left a stale in-memory result.**
  A live SQL recheck and ORM refresh now follow the await; historical memory-search
  tool results are revalidated afterward too. Timing-controlled tests prove
  deleted content never reenters subsequent model context.
- Revision mutation and deletion share the lineage root lock plus an atomic
  expected-revision claim. Real PostgreSQL races prove one correction wins and
  deletion leaves no active replacement or source/embedding residue.
- Models can only create inactive proposals. Actual-run context binds actor/mode/
  namespaces; schema/body text cannot grant these. Human acceptance is atomic and
  one-use. Canonical/GM-secret model proposals are denied and accepted notes are
  marked MODEL_PROPOSAL. Memory text requesting authority could not execute a
  protected fake external tool or gain a revoked capability.
- Sources are asserted bounded data; no source locator is fetched/executed.
  Context uses untrusted user data and conservative UTF-8 token bounds including
  tool schemas and arguments/results. Unicode/large memory/schema tests prove
  budget enforcement and omission.
- Optional pgvector initially exposed a query-binding incompatibility; real SQL
  tests led to explicit typed parameter binding. Vector results match the offline
  path; incompatible model/dimension keys use lexical matches. Missing extension
  fails clearly, and migrations never install it without operator action.
- Startup refuses an older foundation-only schema until memory migration 0002
  is applied, instead of reporting readiness and failing later memory requests.
- SDK embedding errors are sanitized; auto-memory text is not persisted in run
  messages. Deletion clears eligible content/source/embedding lineages and accepted
  proposal payloads; audit stores IDs without facts. Historical conversation/tool
  transcript retention remains explicitly separate.

Final full suites: **106 passed, 1 skipped** on ordinary PostgreSQL and **106
passed, 1 skipped** on PostgreSQL + pgvector. Each skip covers the opposite vector
configuration. Lint/format/types and 0.2.0 wheel/sdist pass. Real migrated HTTP
create/search/chat-provenance/correct/delete/export workflow passes with fake
providers. Full upstream regression retains the same nine pre-existing failures.

## Remaining limitations and release decision

- Only single-user bearer identity, one API process, local POSIX deployment and a
  trusted operator configuration are supported. Multi-worker recovery could fail
  another worker's active run; do not deploy multiple workers at this checkpoint.
- Database administrators remain trusted. Production needs a non-owner restricted
  application role; the append-only trigger alone does not constrain a superuser.
- No production TLS/token rotation/request-rate limiting or global cost quota.
  Concurrent runs, per-run tools/tokens/context/output/deadlines are bounded.
- The parser worker is a credential-free AST parser, not an arbitrary-code sandbox.
  Engineer editing/execution remains disabled pending OS sandbox isolation.
- Non-idempotent external effects need provider idempotency or human reconciliation
  after an interrupted attempt. No real external-write adapter is registered.
- Campaign membership/state/visibility, Tutor mastery, dedicated Chief of Staff,
  Engineer edits, frontend accessibility/PWA, voice, watchers and integrations are
  pending. They have no implemented security or functionality claim yet.
- Memory is owner-scoped, including PUBLIC/PARTY. Its dedicated UI, automatic
  expiry purge, comprehensive conversation retention and large-archive ANN indexing
  remain outside this checkpoint. Candidate windows and byte budgets are explicit.
- Live OpenAI calls/model availability were not tested or paid for; SDK behavior
  is covered with deterministic mocks and typed errors. SSE streams run states
  and final results; intermediate token display is pending UI work.
- Upstream formatter/type/test drift is documented and unchanged, not suppressed.

No unresolved CRITICAL/HIGH issue is known within the bounded, single-process
local checkpoint. This does not authorize public production release or imply the
complete JARVIS definition of done has been met. Next: phase 6 sandboxed Engineer
workflow, following JARVIS_PLAN.md.
