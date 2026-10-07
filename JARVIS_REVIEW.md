# Adversarial review — foundation, memory and Engineer checkpoint

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
   PATH/LANG/PYTHONHASHSEED, not application credentials. No unrestricted host shell is enabled.
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

## Phase 6 hostile review and fixes

- Verified real PID/network namespace separation, UID 65534, zero effective
  capabilities, no-new-privileges and hard process caps before registering tools.
  Unavailable isolation leaves text/memory operational with no execution fallback.
- **Applying NPROC before namespace setup blocked the runtime under shared host
  user counts.** It now applies after isolation and privilege drop, before Python.
  Real fork tests demonstrate the enforced cap without skipping failed setup.
- **The private sandbox root initially allowed disposable root-file writes.**
  Root/dev/proc are now read-only; only a 16 MiB private tmpfs is writable. Tests
  prove host/source/runtime writes, symlink targets and network access are denied.
- No Git checkout/add/diff runs against the untrusted original repository. Only
  HEAD/tracked-name reads are allowed there; source bytes use no-follow IO. Fresh
  private snapshot repositories exclude hooks/config/attributes/credentials.
  Malicious post-checkout hooks, smudge configuration and README instructions
  cannot gain host authority. Source trees never enter host shell execution.
- Exact source hashes, duplicate-path rejection, new-target/symlink checks, actual
  Git patches and source rechecks prevent stale/ambiguous edits. Source SHA is
  emitted by the existing bounded read tool. The original repository is unchanged.
- Untrusted tests get no inherited API/database/token secrets or Git metadata.
  Memory, CPU, processes, per-file and aggregate tmpfs, wall/output limits are
  exercised in real workers. Cancellation closes subprocess sessions/descendants,
  removes intermediates and retains an owner/run-scoped report.
- Failure envelopes make AgentRun FAILED before a model can describe success.
  Artifact owner checks, real API authentication, mode/project/grant denial and
  durable fake-model E2E are verified alongside all existing approval/memory tests.
- Full reports retain bounded output and provenance; budgeted previews and Unicode
  fallback envelopes prevent large reports overflowing registry/model context.
  Retention is capped at 128 jobs; no unbounded artifact accumulation is permitted.

Remaining execution limits: ordinary local Git repositories, eligible tracked
text only, small replacement edits, standard-library Python runtime, no network
or dependency installation, shared Linux kernel and per-process (not aggregate
cgroup) memory cap. Operator cleanup handles retained/orphan jobs. No multi-worker,
source-apply, repository commit/merge/push/deploy, or production release is claimed.
See docs/jarvis/ENGINEER.md for details. This is a self-review, not an independent
penetration test.

Final Phase 6 checks: 137 passed, one configuration-specific skip in each full
PostgreSQL/pgvector suite with real kernel tests enabled; lint/format/types,
0.3.0 package builds, real HTTP smoke and scoped graph navigation passed. Full
authorized upstream regression had 6,472 passes and seven existing DNS failures.
No new upstream failure identifier. See progress for the restricted-run comparison.

## Remaining limitations and release decision

- Only single-user bearer identity, one API process, local POSIX deployment and a
  trusted operator configuration are supported. Multi-worker recovery could fail
  another worker's active run; do not deploy multiple workers at this checkpoint.
- Database administrators remain trusted. Production needs a non-owner restricted
  application role; the append-only trigger alone does not constrain a superuser.
- No production TLS/token rotation/request-rate limiting or global cost quota.
  Concurrent runs, per-run tools/tokens/context/output/deadlines are bounded.
- The parser worker is a credential-free AST parser, not an arbitrary-code sandbox.
  Engineer execution is opt-in, kernel-verified and limited to system-Python commands.
- Non-idempotent external effects need provider idempotency or human reconciliation
  after an interrupted attempt. No real external-write adapter is registered.
- Campaign membership/state/visibility, Tutor mastery, dedicated Chief of Staff,
  frontend accessibility/PWA, voice, watchers and integrations are
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
complete JARVIS definition of done has been met. Next: phase 7 evidence-backed
Tutor workflow, following JARVIS_PLAN.md.
