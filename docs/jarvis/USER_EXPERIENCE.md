# Command Center / PWA — Phase 9

The runnable React/TypeScript interface is in `apps/jarvis/frontend`. It uses the
existing same-origin bearer-authenticated backend, fake models by default, and
ships inside the Python wheel after building. There is no CDN, hosted font,
separate frontend service, runtime Node requirement, or browser model key.

## Build and run

Install the backend, migrate PostgreSQL and configure `.env` as described in
[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md). Node 22.12+ and npm are required
for development/building (the pinned Vite toolchain requires that Node version).
From the repository root:

```sh
cd apps/jarvis/frontend
npm ci
npm run build
cd ..
../../.venv/bin/uvicorn jarvis.api:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`, enter your configured server bearer token, and connect.
No token is embedded in the bundle. The application keeps it only in memory,
clears the password field immediately, aborts pending requests at sign-out,
expires the session on 401 and clears/hides the page before history restoration.
Reloading requires authentication again. For development, start the API at port
8000 and run `npm run dev` in `frontend`; Vite at port 5173 proxies `/api` and
`/health`. The production security-header checks apply to FastAPI serving the
built application, not Vite's development server. Keep both on loopback.

Build the application before packaging:

```sh
# From repository root, after npm ci / npm run build above
.venv/bin/python -m build --no-isolation apps/jarvis
```

The wheel includes `jarvis/web` and its hashed JS/CSS assets. Source distributions
include built assets when built this way. Frontend source and lock are maintained
in Git; generated output is ignored. An unbuilt source checkout returns a clear
503 at UI routes while its backend APIs remain available.

## Surfaces and API contracts

All requests use `Authorization` headers, `credentials: omit`, `cache: no-store`
and redirect rejection. No credential enters URLs or any persistent browser store.
API JSON is bounded to 2 MB before parsing; untrusted text displays cap at 32,000
characters and clearly indicate truncation. No HTML/Markdown parser, dynamic
iframe, external links, URL fetch, hidden reasoning, eval or script insertion is
used. JSON examples are submitted through existing strict server schemas.
TypeScript core wire views are in `frontend/src/contracts.ts`; OpenAPI remains
server-authoritative for the dedicated memory, learning and campaign schemas.

| Surface | Contract and scope |
|---|---|
| `/`, `/chat`, `/missions` | `/api/chat`, `/api/runs`, owner-scoped run detail/cancel; bounded status polling/reconnect; mode-isolated UI; steps, result, tool activity, model/fallback/usage/cost and evidence |
| `/projects` | Operator-registered `/api/projects`; goals/watchers clearly marked pending |
| `/approvals` | Pending/history `/api/approvals`; exact operation, fingerprint, expiry; explicit approve/reject endpoint; no editable operation on approval |
| `/memory` | Namespace/mode scoped lists/search/create/correction/delete/export and human proposal acceptance; provenance, retrieval reasons, revision and eligibility; scoped cursor pages |
| `/engineer`, `/engineer/graph` | Sandbox readiness, registered project selector, graph query/health/path/explain/impact/update; scoped chat; explicit bounded isolated ChangeRequest JSON; owner-scoped patch/test/impact artifacts |
| `/tutor` | Source-backed objectives, cited lessons/quizzes, human attempts, mastery evidence and due reviews; model teaching chat retains objective scope |
| `/gm`, `/gm/:id`, `/gm/:id/session` | Membership-filtered campaign/scene, sessions, visibility labels, GM controls, NPC/PC rolls/report/delegation, non-canonical text transcripts and exact human decisions on structured canonical proposals |
| `/settings` | Safe server model/memory configuration, actor ID, grants and tool contracts; read-only operator configuration; microphone off and voice/integrations pending |

Two additive read endpoints support durable cockpit navigation: campaign session
summaries (campaign membership required) and campaign proposal history (GM-only;
changes may contain secrets). Membership is checked before queries; there is no
new model tool, migration, role selection, policy grant or canonical write path.

Mode/path/session/namespace changes remount scoped surfaces, clear prior results
and ignore obsolete asynchronous responses. Sign-out replaces the entire private
workspace. A closed client ignores late errors, preventing an old identity's 401
from terminating a new session. Refresh clears private scene data before reads,
and a denied response cannot retain the earlier scene. This does not implement
production multi-user identity; browser E2E uses an explicitly test-only two-token
ASGI host to exercise the same existing actor/membership service boundaries.

## PWA and accessibility

The manifest and build-generated service worker are same-origin. Its finite cache
allowlist contains only the empty public shell, icon, manifest and hashed JS/CSS.
It never intercepts API, health, authenticated requests, writes, URLs with queries,
or cross-origin requests. No runtime response populates a cache. Old application
static caches are cleaned on activation; service-worker updates use the normal
browser lifecycle. Offline permits the sign-in shell; private data, model runs,
rolls and decisions need the backend. It queues no actions offline.

For the product UI/assets/API, FastAPI applies a restrictive CSP without
unsafe-inline/unsafe-eval, no-store,
no-referrer, nosniff, frame denial and disabled microphone/camera/geolocation.
Production remote deployment still needs the existing TLS/identity/DB hardening;
Phase 9 does not make the single-process prototype production-ready. Optional
FastAPI developer docs retain their pre-existing Swagger/ReDoc asset policy;
the product frontend does not use those CDN assets. No-store/device/frame headers
still apply to the developer docs.

Responsive desktop/mobile layouts use native labels/forms/buttons, semantic
navigation/headings, current-page indication, a skip link, route-title focus,
visible keyboard focus, loading/status/alert messages and reduced-motion support.
The mobile Command Center passes the automated axe check; this is not a claim
of a complete manual accessibility audit. Graph evidence is a text/source explorer,
not the unsafe upstream graph HTML embedded in an iframe. Advanced graph canvas,
rich campaign maps/initiative, token-by-token output and microphone input remain
outside this checkpoint.

## Verification

From `apps/jarvis/frontend`, after installing the backend and `npm ci`:

```sh
npm run check
npm run format:check
npm run build
npm run test
npm audit --audit-level=high
npx playwright install --with-deps chromium
npm run e2e
```

Where a compatible system Chromium is already installed, use
`JARVIS_CHROMIUM=/usr/bin/chromium npm run e2e`. The test host owns a disposable
SQLite database, uses fake providers, disables access logging/traces and never
loads development `.env`. Its synthetic tokens are test fixtures. Browser E2E
covers sign-in/401, navigation, durable fake runs, offline static shell, Tutor
human mastery, GM canonical proposals/session/dice/player secrecy, memory text
injection/correction/deletion and mobile accessibility. Component/security tests
cover exact approvals/cancellation/reconnect, denied access, stale state, late
identity responses, credential storage, byte bounds and production worker policy.
Backend authority/security suites remain independent and include real disposable
PostgreSQL/pgvector and opt-in Linux isolation tests. See progress/verification
snapshots for commands and results actually observed.

## Phase 10 update

The earlier Phase 9 microphone-off/pending descriptions are historical. Conversation
now has optional voice, reviewed transcripts and explicit completed-answer playback.
Devices remain off by default. Live configuration permits only same-origin microphone;
camera/geolocation stay denied. Blob audio playback is the only CSP addition.
Scope changes/sign-out/offline/hidden tabs stop devices immediately. API/token/audio
cache and storage boundaries remain unchanged. See [VOICE.md](VOICE.md).

## Phase 11 update

Settings now shows provider admission estimates and usage from authenticated /api/usage.
Rate/budget errors are displayed as request limits. Voice controls show when capture
is unavailable or waiting for remote cleanup, without prompting for the microphone.
Production realtime capture remains disabled; reviewed input/text stay usable. Private
API/audio/token data remains excluded from storage and service-worker caches.
