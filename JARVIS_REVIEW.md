# Adversarial review — foundation checkpoint

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

## Verification

Full JARVIS unit/security/fixture/PostgreSQL suite: **59 passed**. Ruff lint/format
and Pyright: passed; wheel/sdist build: passed. Real HTTP/PostgreSQL smoke: health
200, authentication 401 without token, Engineer run completed with Graphify data.
Upstream regression: 6,470 passed, 108 skipped, 9 failed; every remaining failure
was present in the initial complete baseline. Architecture-doc tests: 38 passed.

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
- Personal memory, campaign visibility, Tutor mastery, dedicated Chief of Staff,
  Engineer edits, frontend accessibility/PWA, voice, watchers and integrations are
  pending. They have no implemented security or functionality claim yet.
- Live OpenAI calls/model availability were not tested or paid for; SDK behavior
  is covered with deterministic mocks and typed errors. SSE streams run states
  and final results; intermediate token display is pending UI work.
- Upstream formatter/type/test drift is documented and unchanged, not suppressed.

No unresolved CRITICAL/HIGH issue is known within the bounded, single-process
local checkpoint. This does not authorize public production release or imply the
complete JARVIS definition of done has been met. Next: phase 5 memory/context,
then phase 6 sandboxed Engineer workflow, following JARVIS_PLAN.md.
