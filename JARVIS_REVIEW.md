# Phase 12 adversarial review — 2026-10-14

Reviewed published Phase 11 `6d0b05acdc7db62256cf8134e4990dd62a390000` and remediated
locally on `jarvis/phase-12-adversarial-review`, application **0.9.0**, schema **0005**.
This is a source/test review of supported prototype behavior, not an independent
penetration test or production release. Prior review sections below are historical.

## Findings and remediation

| ID | Severity | Reproduction / impact | Fix and evidence |
|---|---|---|---|
| P12-01 | HIGH | Four public GETs with an unfinished body exhausted a four-slot HTTP gate and made an authenticated request return 429. Public response work also shared authorized capacity. | Reject body-bearing GET/HEAD and unsupported public methods before body reads; bodyless requests never await inbound data; separate four-slot public response pool. Two adversarial admission tests verify authenticated capacity and cleanup. |
| P12-02 | HIGH | `credentials.json`, `secrets.yaml`, `client_secret.toml`, and service-account JSON passed workspace reads and eligible tracked-source staging. | Shared sensitive config-name and credential-container exclusions cover reads, Graphify staging and Engineer manifests. Four read cases and a real Git snapshot test prove exclusion while preserving `credentials.py`. |
| P12-03 | HIGH | A GM scene captured in tool history survived a canonical GM→PLAYER role downgrade; revocation during awaited retrieval also left an old scene in outgoing context. Derived prose and tool arguments could carry the same secret. | Refresh the scene after retrieval awaits, replace historical scene outputs with the current authorized view, and withhold historical assistant/tool content on a packet change. Persist a fingerprint and history cutoff in run metadata so later steps/resumes cannot reintroduce old content. Tests cover role changes, controlled await timing, derived text/arguments and a subsequent build preserving new authorized content. |
| P12-04 | MEDIUM | A player session/scene returned the UUID of a GM-secret active location. | Independently authorize the referenced location; return null for unavailable, retired or hidden entries in scene and session lists. Adversarial test exercises both surfaces. Session titles remain deliberately campaign-visible metadata. |
| P12-05 | MEDIUM | Microphone permission or WebRTC offer negotiation could stall before the session timer started. | A 120-second local deadline covers the entire setup/capture lifetime; server negotiation cannot extend it. Late permission streams are stopped and late sessions are hung up. Two fake-timer device tests cover pending permission and active capture during stalled offer creation. |
| P12-06 | MEDIUM | One throwing device cleanup callback prevented token clearing, pending request cancellation and later resource cleanup during sign-out. | Clear credentials and abort requests before isolated cleanup callbacks. A throwing-callback regression proves cancellation, subsequent cleanup and refusal of new authenticated requests. |

Nine receiving-source reproductions failed before remediation; all eleven final
backend adversarial cases pass, plus three new browser component/device regressions.
No identified critical/high finding remains open within supported scope. Filename
exclusion is not secret-content classification: arbitrary embedded literals or
unconventionally named configs remain an operator registration/content-hygiene risk.
No real credential was used in the fixtures.

## Hostile review coverage and residual limits

| Boundary reviewed | Evidence / decision |
|---|---|
| Architecture, Graphify coupling, future merges | Only `graph.py` / private `graph_worker.py` call preserved Graphify internals. AST staging uses the shared path exclusions; no upstream core/test/root dependency/license or prior migration change. Adapter extraction runs privately with a constructed environment. Internal Graphify API compatibility needs regression testing on future upstream upgrades. |
| Authorization and audit bypass | Strict registered schemas and trusted actor/capability/mode; exact operation/actor/run/nonce/expiry approvals rechecked at execution. PostgreSQL one-use races and restricted-role smoke verify audit append-only/DDL denial. Database admins/application source remain trusted; this is single-principal application authorization, not tenant isolation. |
| Secret handling / injection | Credential-config regression above; literal bounded UI, untrusted tool/graph/memory/scene data; poisoned memory/repository cannot grant capabilities or bypass policy. No URL locator fetching, model authority edits, canonical GM commits, or model Tutor mastery tools. Owner-retained historical runs are not retroactively erased by campaign revocation; subsequent model context is reauthorized. |
| Sandbox / async cleanup | All 13 real kernel probes run in both DB configurations: no host network/secret/Git/workspace writes; limits, cancellation and child cleanup; no host-shell fallback. Shared-kernel risks, aggregate cgroup memory limits and unsupported-host execution remain documented constraints. Public admission no longer consumes authenticated slots. |
| Models / fallbacks / cost | Fake and official Responses adapter protocols, explicit fallback consent, high-stakes/auth failures, timeout/cancel and visible usage tested. No paid SDK interoperability exercised. Daily durable estimates are admission controls, not an invoice ceiling; production live microphone remains disabled because remote data-channel generation settings cannot be bounded authoritatively. |
| Database consistency / lifecycle | Immutable migrations 0001–0005, upgrade/downgrade/upgrade/parity, approval/memory/Tutor/campaign/quota races, restart retention, monitored single-worker lease and unhealthy-on-loss tests. One worker is supported; HA/multi-user identity, external idempotency, operational backup/restore and retention require separate work. |
| GM secrecy / canonical state | SQL membership/visibility before candidate limits; scene/output/history revalidation above; controller-only human/default PC rolls and one-use delegation; auditable NPC dice; GM-only structured canonical decisions. Authorization reflects the final context snapshot; revocation cannot recall data already sent to a provider or previously read by an authorized actor. Packet changes conservatively withhold older derived context, trading continuity for secrecy. |
| Frontend accessibility / cache / device | Type/lint/format/build, 38 component/security/device tests, five Chromium flows including mobile axe, forms and identity changes; static-only worker and no private cache/storage. Complete manual keyboard/screen-reader, device/permission UX and live browser-provider checks remain unverified. |
| Deployment / supply chain / tests | Restricted-role SQL, exact HTTPS origin/proxy trust and offline Caddy validation; locked dependency audits and source scan. Templates are not deployed infrastructure. Certificate issuance, token lifecycle/production identity, backups/monitoring, paid provider and independent pen testing remain release prerequisites. Test fakes are visibly fake; skips and upstream failures remain explicit. |

## Master acceptance reconciliation

| Master scenario | Actual supported evidence |
|---|---|
| E2E-1 graph intelligence | Adapter fixture index/query/explain/path/impact/source provenance and `test_graphify_engineer_evidence_precedes_model_and_injection_cannot_grant`. |
| E2E-2 engineering change | Real `test_engineering_e2e_real_worktree_tests_graph_impact_and_artifact`: sanitized isolated worktree, configured targeted/regression commands, AST update, impact, diff/artifact. Bounded Python fixture support only. |
| E2E-3 approval | `test_external_write_pause_exact_approval_resume_and_replay`, mutation/expiry/revocation plus atomic PostgreSQL claims. External service is a fake fixture; no live integration delivery claimed. |
| E2E-4 memory provenance | `test_source_grounded_chat_exposes_retrieval_provenance`, inspector/revision/deletion and pgvector/offline ranking. Source citations are retained asserted data, not fetched verification. |
| E2E-5 GM secrecy | Player context/filter-before-limit and Phase 12 permission/history/await regressions; hidden location identifiers filtered. |
| E2E-6 human PC / E2E-7 NPC dice | `test_game_master_e2e_visibility_roll_authority_delegation_and_canonical_event` and competing one-use PG delegation; controller human reports, configured adjudication and auditable bounded dice. |
| E2E-8 injection | Graphify evidence, poisoned personal memory, project hooks/filters and campaign text adversarial tests; deterministic grants unchanged. |
| E2E-9 model migration | Routing/provider protocol and `test_visible_fallback_usage_metadata`; failure or allowed configured fallback, persisted attempts/usage; no assumed live model availability. |

The definition-of-done's preserved Graphify, bounded adapter, fake backend/frontend,
migrations, durable runs/cancellation, configuration/fallback, policy/approvals/audit,
provenance/structured memory, Engineer/Tutor/GM/dice/rules and injection/kernel/build
claims have executable prototype evidence. Responsive UI/accessibility has automated
coverage but not complete manual sign-off. Documentation reflects current scope.
The broad master product is **not complete**: dedicated Chief of Staff projects/tasks/
checkpoints/watchers, outbound integrations, richer graph/campaign features,
production identity/operations, billing authority, retention and live validation
remain deferred. Phase 12 review completion does not turn those omissions into delivery.

Final check results, commands and unchanged upstream failures are recorded in
[PHASE12_REPORT.md](docs/jarvis/PHASE12_REPORT.md) and `docs/jarvis/verification/phase12-*`.

---

# Adversarial review — foundation through Command Center checkpoint

Sections through Phase 8 retain the earlier review history; the Phase 9 section
below is the current browser/API review and release decision.

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
- **Ubuntu's AppArmor user namespace policy blocked launcher setup.**
  The explicit no-new-privileges wrapper now runs inside Bubblewrap, after trusted
  namespace setup and capability drop and before any project Python executes.
  Worker probes still require UID 65534, zero capabilities and no-new-privileges;
  Moving this wrapper alone did not fix GitHub's runner. CI additionally installs
  Ubuntu's child-restricting Bubblewrap profile and asserts that the global
  AppArmor user namespace restriction stays enabled. No host fallback is added.
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

## Phase 7 hostile review and fixes

- Tutor canonical state uses migration-0003 tables, separate from personal memory.
  All objective/source/artifact/attempt/evidence/review queries bind the trusted
  actor before returning or grading records. Foreign owners and missing grants are
  tested before content is exposed.
- Model tools are limited to objective-bound context and source-cited lesson/quiz
  creation in TUTOR mode. There is no attempt, scoring, mastery or review-completion
  tool. Attempts are strict authenticated inputs with server-owned origin, score,
  correctness and evaluator fields; fabricated fields fail schema validation.
- Source IDs must belong to the same owner/objective. Quotes and lessons remain
  labeled untrusted, and injection text cannot add a capability or mutate mastery.
  Accepted answers are persisted as hashes and never returned in Tutor views.
- **Same-timestamp retries initially used UUID order when selecting the latest
  answer.** Mastery evaluation now orders by explicit per-quiz attempt number.
  The E2E covers wrong-answer then correct retry at an identical test timestamp.
- Duplicate HTTP submission IDs replay only the identical hashed answer; changed
  content conflicts. PostgreSQL objective locks serialize mastery recomputation,
  and unique attempt/evidence/review constraints prevent duplicate canonical rows.
  Concurrent duplicate and distinct-quiz tests exercise both paths.
- **A review initially accepted any correct attempt created after its task.** It
  now requires a correct HUMAN_API attempt evaluated at or after the task due time,
  preventing early practice from being reused as spaced-review evidence.
- Mastery uses latest human performance across distinct quizzes and retains exact
  attempt IDs, score and evaluator version. Explanations, model-generated answers,
  self-reports and quiz creation alone leave the objective ACTIVE.

Current evaluation is exact normalized short-answer matching. It is deliberately
less flexible than semantic grading and unsuitable for open-ended/rubric assessment.
Bearer possession is the learner identity in this single-user checkpoint. Answer
hashes are not confidential against low-entropy offline guessing by a trusted DB
administrator. Notifications/watchers and a Tutor UI remain pending.

Phase 7 full local suites passed **152 tests, 1 skipped** on PostgreSQL and
**152 tests, 1 skipped** on PostgreSQL/pgvector with real kernel tests enabled.
Ruff, format and Pyright passed. The migrated API smoke, 0.4.0 package build,
relevant upstream architecture tests, preserved-boundary comparison and scoped
Graphify TutorService query/explain also passed. See progress for exact results.

## Phase 8 hostile review and fixes

- Campaign membership is resolved before reading campaign metadata or content.
  Scene entries and transcript lines use role/player visibility predicates in SQL
  before ordering, candidate limits, byte budgets and model input. A test places
  129 newer GM secrets ahead of an older allowed marker and still retrieves only
  the marker for the player.
- Scene packets are bounded to current campaign/session data, label every content
  field untrusted and retain only IDs/visibilities in run metadata. Player-facing
  provider capture proves secret text and IDs never reach the model.
- Model tools are limited to scene read, policy-controlled roll and pending event
  proposal. Membership, human transcript, delegation, human roll report, decision
  and canonical commit have no model tool. Prompt-injected lore cannot change role,
  reveal a secret or gain roll authority.
- **The initial roll policy allowed only a PC controller to request its roll.** It
  now permits a GM to create an awaiting-human request while only the controller
  can report it. A personal-play GM may control a PC because controllers need to be
  campaign members, not necessarily PLAYER-role members.
- **Delegation lookup initially followed the requester.** It now follows the PC's
  controller, so a GM request can consume only that controller's explicit active
  delegation. PostgreSQL locking, expiry, max-use and status make it one-use under
  concurrent requests; the other request immediately returns to human authority.
- **Direct dice requests initially trusted possession of an entry UUID after only
  checking campaign membership.** Subject visibility is now checked independently;
  GM-secret, another player's private and retired entities return the same not-found
  boundary before roll authority is evaluated.
- Electronic rolls use strict expression caps and an injected RNG. Records retain
  requesting actor, reason, visibility, raw/kept/discarded dice, modifier, total,
  authority, provenance and a hashed entropy reference. Exact request and delegation
  nonce replays reject changed data; reported human totals must fit the expression.
  Campaigns select a named operator-registered roll policy.
- Creative prose and transcripts never change canonical entries. Pending structured
  CREATE/RETIRE proposals require authenticated GM role/capability. A row lock and
  unique event/proposal constraint make competing decisions commit exactly once.
  Rejection is final. Audit data omits secret prose.

Phase 8 full local suites passed **173 tests, 1 skipped** on PostgreSQL and
**173 tests, 1 skipped** on PostgreSQL/pgvector with all real kernel tests enabled.
Ruff, format and Pyright passed. The 0.5.0 package build, migrated API smoke,
Graphify synchronization/query/explain and preserved upstream boundary passed.

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
- Dedicated Chief of Staff projects/watchers, frontend accessibility/PWA, voice
  and integrations are pending. Rich campaign imports/maps/initiative/recap and
  production identity remain outside the current Game Master checkpoint.
- Memory is owner-scoped, including PUBLIC/PARTY. Its dedicated UI, automatic
  expiry purge, comprehensive conversation retention and large-archive ANN indexing
  remain outside this checkpoint. Candidate windows and byte budgets are explicit.
- Live OpenAI calls/model availability were not tested or paid for; SDK behavior
  is covered with deterministic mocks and typed errors. SSE streams run states
  and final results; intermediate token display is pending UI work.
- Upstream formatter/type/test drift is documented and unchanged, not suppressed.

No unresolved CRITICAL/HIGH issue is known within the bounded, single-process
local checkpoint. This does not authorize public production release or imply the
complete JARVIS definition of done has been met. Next: phase 9 Command Center/PWA,
following JARVIS_PLAN.md.

## Phase 9 browser/API review

Reviewed the delivered frontend, static host, authentication lifecycle, build
output, cache policy and two additive cockpit read endpoints. No canonical model
write, policy bypass, grant change, upstream rewrite or migration was introduced.

- **Initial pinned dev tooling had known high/critical advisories.** Updated Vite,
  its React plugin and Vitest before delivery; regenerated the lock without forced
  peer overrides. The final npm audit reports zero vulnerabilities. Production
  dependencies are React/ReactDOM; test tooling is not shipped as a server.
- **Late 401 from a closed client could clear a newer identity.** The client checks
  closure/abort before processing responses; a regression test delivers a late
  unauthorized response after closure and proves no logout callback runs.
- **History restoration could retain private rendered state.** Pagehide closes
  the active client synchronously, aborts requests and hides the root before a
  browser snapshot; persisted pageshow forces reload/authentication. There is no
  token/session/API data in persistent storage or service-worker caches.
- Mode/path/session/namespace navigation remounts scoped surfaces; obsolete reads
  and actions cannot write into a new scope. Refresh clears earlier scene data,
  and 403/404 failures do not render server exception details or retain the scene.
- The new proposal-history API checks membership and GM role before reading full
  structured changes. A player and a nonmember cannot retrieve them. Session
  summaries require membership and expose the same campaign-wide session metadata
  already returned by authorized scene requests; titles are campaign-visible.
- Every retrieved string is React text, including malicious HTML, source locators,
  JSON, model results and transcript/campaign content. No dynamic hyperlinks,
  HTML insertion, graph iframe or renderer with script execution exists. Response
  bytes and displayed text are bounded. Approval buttons submit only the existing
  exact approval ID; the full bound operation is visible and cannot be edited.
- CSP denies inline/eval scripts, frames and unknown origins. API/auth/error HTTP
  responses are no-store, with no-referrer/nosniff and disabled device permissions.
  Existing optional FastAPI developer docs retain their original asset policy
  rather than breaking Swagger with the product CSP; the UI has no CDN dependency.
  The finite production worker allowlist caches only the public static shell and
  build assets, never API/authenticated/write/query/cross-origin requests. Generated
  worker tests and an actual offline browser navigation verify this boundary.
- Browser E2E demonstrates fake durable runs, human Tutor mastery, canonical
  proposal approval, session transcript, NPC dice, human-default PC rolls, and
  GM-to-player secret exclusion after sign-out. Automated mobile axe has no
  violations; keyboard/native-label/focus/reduced-motion rules are implemented.

No unresolved CRITICAL/HIGH issue is known in this bounded Phase 9 checkpoint.
The dependency audit is a point-in-time check, not an ongoing security guarantee.
Production multi-user identity/TLS/rate limiting, aggregate worker quotas and a
complete manual accessibility audit remain outstanding. Chief of Staff watchers,
voice/integrations, rich graph canvas and richer campaign workflows are not
implemented. Current verification is in JARVIS_PROGRESS.md and the Phase 9
snapshots. No public deployment or publication is claimed.

## Phase 10 review

Reviewed device permission races, late negotiation/playback results, sign-out, scope
remounts, hidden/offline tabs, peer/session expiry, SDK credential isolation, authority
spoofing, provider output bounds and cache policy. Local cleanup is synchronous and
independent of server availability. Transcripts cannot invoke human-only approvals,
quiz evidence, PC reports or canonical commits. No new model tool/grant exists.

Fixed during review: optional malformed voice settings now fail closed while text
starts; remote hangup errors produce voice.stop_failed rather than claiming success;
recorded WAV duration/format/frame length are validated before external transcription;
SDK negotiation headers are read from the actual typed response; obsolete browser
assertions now check the delivered interface. Speech/transcription use real official
SDK mock transports, not hand-built HTTP. The exact-approval voice delegation test
proves a model-requested fake external write remains paused until a human approves.

No known unresolved critical/high issue in the bounded local single-worker scope.
Live paid interoperability is unverified. Aggregate provider usage/cost enforcement,
crash-time remote reconciliation, production identity/TLS/rate limits and coordinated
multi-worker admission remain Phase 11 work. See VOICE.md and PHASE10_REPORT.md.

## Phase 11 scoped review and fixes

Reviewed quota races/uncertain calls, request/body/peer/origin handling, proxy trust,
DB role grants and owner membership, second-worker recovery, lease loss, client cleanup,
voice creation/stop crash windows, exception privacy, packaging and CI scans.

- Durable row-locked pre-call estimates survive cancellation/restart. Settlement is
  one-use; missing prices deny calls. Unexpected usage is recorded as OVERRUN and its
  result is withheld before tools. Known token usage remains observable.
- Ingress rejects oversized declared/chunked bodies, slow requests, ambiguous security
  headers, foreign origins and request-rate/concurrency overflow before DB audits.
  Spoofed forwarded headers cannot create peer buckets or HTTPS authority.
- Production validates restricted runtime privileges, exact origin/TLS and strong
  bearer configuration. The real role recipe denies audit mutation, DDL and migration
  writes while allowing fake runs/audit inserts. Existing owner-grant inheritance is
  rejected. The operator template requires a new role and never alters existing roles.
- Monitored PostgreSQL session lease prevents a second app from recovering another
  process's runs. Lease loss revokes health and calls shutdown; ExitStack closes all
  resources on startup/shutdown failure. One worker is enforced rather than claiming HA.
- Remote call identifiers/creation intent are durable. Restart cleanup never replays
  creation or audio; unresolved creation requires a human provider-side stop and an
  explicit authenticated acknowledgement. Unknown/failing cleanup blocks local live
  reconnection. No provider ID, audio or credentials enters browser cache/storage.
- WebRTC client data channels can mutate remote generation settings. Production live
  microphone is therefore disabled, preserving text and bounded recorded/speech paths;
  local preview remains. A reservation alone is not advertised as a provider bill cap.
- Production exceptions/validation responses omit private values. CI uses read-only
  permissions and medium/high source/dependency scans. Two narrow B108 annotations
  document private Bubblewrap tmpfs literals; all real kernel tests still run.

No known critical/high issue remains in the bounded single-principal/worker scope.
This is scoped review, not completion of Phase 12 or public deployment approval.
Provider invoice enforcement, operational TLS/backups/monitoring, multi-user identity,
manual live/device testing and full-program acceptance remain pending. See the actual
results/limitations in PHASE11_REPORT.md.
