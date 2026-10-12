# JARVIS handoff — Phase 9 local checkpoint

Continue from local branch `jarvis/phase-9-user-experience`; inspect
`git status --short` and `git rev-parse HEAD`. Its receiving published Phase 8 tip
is `6aa47924e5f93e0337a0deb6e9af96f55c9685fe` at
[Mandy3735/graphify:jarvis/phase-8-game-master](https://github.com/Mandy3735/graphify/tree/jarvis/phase-8-game-master).
The Phase 9 task creates a local reviewable commit; it does not push, merge or
publish. Another cloud session must receive that commit/branch explicitly rather
than assume the published Phase 8 branch contains the UI.

Read AGENTS.md, JARVIS_PROGRESS.md, JARVIS_PLAN.md, JARVIS_REVIEW.md,
THREAT_MODEL.md, docs/jarvis/MASTER_SPEC.md, UPSTREAM_BOUNDARY.md,
LOCAL_DEVELOPMENT.md, USER_EXPERIENCE.md, MEMORY.md, ENGINEER.md, TUTOR.md and
GAME_MASTER.md. Progress records measured checks and remaining limitations;
the complete specification remains authoritative for future scope.

Phases 0–9 are bounded to the independent `apps/jarvis` package. Graphify source,
CLI/MCP, root dependencies/lock, tests, licenses and skill generation are preserved.
The backend has durable fake/OpenAI-configurable runs, tools/policy/exact approvals,
owner/visibility/provenance memory, opt-in kernel Engineer isolation, human-evidence
Tutor and explicit membership/visibility/roll/proposal Game Master boundaries.
Phase 9 adds a runnable responsive same-origin Command Center/PWA, all specified
routes, useful mode-specific workflows, literal rendering, tab-memory credentials,
static-only cache, browser/security/accessibility tests and production bundle.
Only session summaries (member) and proposal history (GM-only) are new API reads.

Build the frontend before packaging or serving the UI: `npm ci && npm run build`
inside `apps/jarvis/frontend`; then run the migrated API using the local-development
instructions. Node is needed only for development/builds. Fake mode needs no paid
key. The Python wheel includes built UI assets. Reload/sign-out needs a new token;
API/private data are never available offline. Product deployment remains a
single-user, single-worker local prototype.

Local Phase 9 checks: 176 tests passed with one opposite-vector skip on each
PostgreSQL configuration, real kernel tests enabled; 24 frontend tests; 4 production
Chromium E2E scenarios; mobile axe no violations; lint/format/types/build/npm audit,
package assets and relevant upstream/graph checks. See portable verification for
observed outputs rather than treating earlier phase counts as current.

Next is Phase 10 optional voice. Preserve every authority and secrecy boundary,
including browser cache/token behavior, human-default PC rolls and canonical
approval. Production identity/TLS/rate limits, Chief of Staff watchers/integrations,
rich campaign workflows and full-program hardening remain later work. No live paid
provider, external effect, deployment or publication has been performed here.
