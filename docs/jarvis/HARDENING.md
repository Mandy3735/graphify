# Phase 11 hardening — application 0.8.0

This checkpoint hardens the single-principal, single-worker prototype. It does not
make the entire master specification complete or authorize public deployment.
Graphify remains unchanged. Apply additive Alembic revision **0005** before startup;
revisions 0001–0004 are immutable. Existing policy, exact approvals, memory ownership,
Tutor evidence, campaign visibility and human PC roll authority remain authoritative.

## HTTP admission and identity

Ingress limits requests before body parsing, authentication audits, SQL or provider
calls. General bodies default to 262,144 bytes; recorded audio alone has a 2,700,000
wire-byte ceiling and its prior 2 MB/120-second PCM WAV validation. Chunked bodies,
Content-Length, ambiguous duplicate security headers and slow-body deadlines are
checked. Sixteen simultaneous HTTP requests/streams are admitted, with 600
authenticated API requests/minute, 30 unauthenticated requests/minute per observed
peer and a 120/minute global unauthenticated ceiling. Peer maps are bounded to 128;
caller-supplied forwarded headers cannot create new buckets. Rate rejection returns
429/Retry-After before DB audit work. Counts use monotonic time and reset on process
restart; durable paid-provider admission is separate. Static assets share the
concurrency/body boundary; API/health requests have rate limits. Use a trusted edge
for stronger distributed flood/connection protection.

Bearer authentication remains one configured principal and stable actor UUID. Tokens
are 32–512 printable, non-space ASCII characters locally, at least 48 in production.
Generate with secrets.token_urlsafe rather than a memorable password; no default
credential is provided. Rotation changes the configured token and restarts the app,
retaining the actor UUID so data ownership does not change. Browser credentials still
stay in tab memory and are cleared on sign-out/pagehide/401. This does not add account
registration, OAuth, passkeys, tenant isolation or multiple principals per deployment.

## Production profile and TLS

Set JARVIS_ENVIRONMENT=production, JARVIS_PUBLIC_ORIGIN to an exact HTTPS origin
without a trailing slash/path, a 48+ character token and a PostgreSQL+asyncpg URL using
a restricted runtime role. Startup rejects unsafe database privileges and stale
schema. Host/origin checks bind to that origin; HTTPS is required in the ASGI scope.
Forwarded headers are not parsed/trusted by application code. Development Swagger,
ReDoc and OpenAPI routes are disabled; local development retains documented APIs.
Production errors omit private exception parameters and input values; HSTS is emitted
on HTTPS responses. Existing CSP/no-store/referrer/device/cache boundaries remain.

A reviewed Caddy TLS-termination template is in apps/jarvis/deploy/Caddyfile. Set
JARVIS_PUBLIC_HOST to the same hostname (and explicit port if needed), provision DNS,
and configure Caddy using the operator's deployment system. Its 3 MB edge body ceiling
is intentionally above the application's audio-wire limit. No certificate was issued
or proxy deployed in this task; Docker caddy adapt --validate passed without network.
Bind the backend to loopback and explicitly trust only the local proxy:

```sh
# From apps/jarvis with operator-managed environment/secrets and completed migrations:
../../.venv/bin/uvicorn jarvis.api:create_app --factory --host 127.0.0.1 --port 8000 \
  --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
```

Do not use a wildcard forwarded-allow-ips or expose the backend listener alongside
the TLS edge. A remote/container proxy needs an explicit trusted address and network
isolation reviewed by its operator. Trust is a server launch decision, never a header,
model message, repository document or voice transcript. Store runtime secrets outside
Git and public/static assets. TLS deployments and live provider calls are operator
work; they were not performed or paid for here.

## Restricted database role

Use separate migration/admin and runtime credentials. Migrate as the owner, then
run the supplied SQL as that trusted owner against the intended database:

```sh
psql -X -v runtime_role=jarvis_runtime_app -f deploy/runtime-role.sql YOUR_DATABASE
```

The script requires a NEW jarvis_runtime_* role and never modifies an existing role.
It creates LOGIN without a password; provision authentication separately through the
operator's secret workflow (e.g. psql's interactive \password), then configure only
that role's URL on the backend. It grants table DML and schema usage, with audit
SELECT/INSERT only and migration-version SELECT only. It grants no ownership, DDL,
TRUNCATE, admin, membership, bypass-RLS or role-creation privilege. CREATE on public
schema and CREATE/TEMPORARY on the current database are revoked from PUBLIC; review
this deliberately database-wide change with other database users before applying it.
Do not apply this setup to a shared production DB blindly. New migrations require
reviewed runtime grants for their new tables; startup never runs migrations or creates
roles. Production requires that the role cannot inherit or SET ROLE to privileged
owners. The smoke test uses the real SQL script and proves fake runs/audit inserts
work while audit mutation, DDL and migration-table writes fail.

## Enforced single-worker lifecycle

Each PostgreSQL application process holds a session advisory lease before run recovery.
A second worker cannot start on that database. A monitored lease is retained across
commits; losing it marks the runtime unhealthy, rejects API work and invokes active
run/voice shutdown. Checks occur every two seconds with a three-second DB deadline.
ExitStack closes clients, workers, lease and pool even on startup/shutdown exceptions.
SQLite is allowed only for local/unit fixtures and has no cross-process lease; do not
run multiple local SQLite workers. Direct internal Engine test instances bypass the
HTTP application lease deliberately; they are not alternate public server entrypoints.
This enforces one worker rather than implementing distributed coordination.

## Durable provider admission and estimates

Before live reasoning/embedding calls, configure actual model prices in
JARVIS_PRICING as {model: [input_USD_per_million, output_USD_per_million]}.
Unpriced live calls are denied before the SDK/network. Reasoning reserves a conservative
UTF-8 input/schema/framing estimate plus configured output maximum, then settles from
returned token usage. Unknown usage retains the upper estimate. Embeddings retain
the conservative input estimate. Prices and the budget must be finite/nonnegative.

Configure upper per-operation estimates in JARVIS_PROVIDER_OPERATION_COSTS using
keys speech:<model>, transcription:<model> and realtime:<model>. They are USD per
bounded operation, not hardcoded provider prices. Estimate speech for 4,000 characters,
transcription for the maximum admitted two-minute capture, and local realtime for
the configured maximum session duration. Keep estimates/prices current with provider
billing. Missing estimates deny calls. JARVIS_PROVIDER_DAILY_BUDGET_USD defaults to 25.
Fake providers require no price or paid service and do not consume this ledger.

Migration 0005 stores UTC-day totals and actor-scoped provider call IDs, kind/model,
reserved/charged integer micro-USD, usage/state and timestamps, never prompts/audio/
credentials. A transaction locks the day row and reserves before external work; races
cannot oversubscribe the configured estimate budget. Failures, cancellation and crash
retain the full reservation; restarting does not reset it. Settlement is one-use.
Unexpected usage above a reservation is recorded as OVERRUN and its result is withheld
from tools. GET /api/usage and Settings show global day estimates plus only the current
actor's latest 30 call summaries. Existing per-run model usage/fallback/cost remains.

This is a durable **admission estimate**, not a guarantee about a provider invoice or
an upstream service's behavior. SDK timeouts, output limits and fixed-operation caps
reduce exposure, but provider-side account billing limits remain necessary. UTC daily
buckets are not a rolling 24-hour window; retention/archival of ledger rows is operator
work. Unknown reservations are intentionally not auto-refunded or replayed. Operators
can reconcile actual invoices in trusted administrative workflows; models/API callers
have no quota-reset tool.

## Voice reconciliation and production microphone boundary

Voice call creation records CREATING before an external call and persists known
provider call IDs. Stop records success or STOP_FAILED. Startup performs bounded
background cleanup of known IDs, never recreating a session or replaying audio;
404/410 hangup means the remote call is already absent. This remains independent of
text startup. An interrupted creation with no returned ID becomes UNRESOLVED. Local
live capture is blocked while its actor has pending cleanup. An operator must verify
remote calls have stopped using the provider's controls, then explicitly acknowledge
POST /api/voice/sessions/{id}/reconcile with {"remote_stopped": true}. It is an
authenticated human-only endpoint with no model tool or automatic transcript action.
Saved provider IDs never enter browser responses; status exposes local IDs/states.

Live WebRTC data channels can change generation settings remotely. The backend cannot
prove a hard generation-cost ceiling from the Phase 10 browser transport, so production
mode disables **live microphone transport** and microphone permission. Local live mode
remains available with configured estimates; fake preview still works. Production
text, reviewed input, configured bounded recorded-audio transcription and explicit
owned-result speech remain usable. Their quotas and prior visibility/approval controls
still apply. Reconnect is explicit. This limitation must be resolved with a verifiable
provider-side authority/billing boundary before enabling production live microphone.

## Checks and remaining scope

The separate JARVIS CI workflow has read-only GitHub permissions, cancellation of
superseded checks, dual PostgreSQL/pgvector jobs, real Bubblewrap tests, production
frontend/browser/build and medium/high Bandit plus hashed-lock pip-audit scans.
Two B108 annotations explain private kernel tmpfs mount/home literals; the rule is not
globally disabled and runtime isolation tests still run. Dependency audits are
point-in-time observations. Nine low-severity source findings (assert/import/process
API use) remain reviewed implementation details, not suppressed wholesale.

Full master-spec completion, Chief of Staff projects/watchers/integrations, multi-user
identity, HA/multiple workers, operational TLS/certificate/backup/restore monitoring,
provider billing enforcement, manual hardware/live-browser testing and full-program
Phase 12 adversarial acceptance remain separate work. Use PHASE11_REPORT.md for
actual results and commands. No public deployment, live paid call or publication was
performed by this Phase 11 task.

## Phase 12 update

Application 0.9.0 keeps migration 0005. Public response slots (four) no longer consume
authenticated concurrency. GET/HEAD declared bodies and public unsupported methods
are rejected; safe methods never await an inbound body. Other API writes retain the
byte/deadline gates. Phase 12 review/remediation is complete within supported scope;
production and deferred product limitations in JARVIS_REVIEW.md still apply.
