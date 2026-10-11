# Copy this prompt into the next Codex task

Continue Graphify → JARVIS from the published branch
`Mandy3735/graphify:jarvis/phase-8-game-master`. Published Phase 8 implementation
commit `84172d3de1fe2a6c5271718c81feab0f8a994dd4` is based on the clean published
Phase 7 tip `d90bec5d9c255d922af3105d6974ca74eaf58271`. Fetch the branch, then check
HEAD, the working tree and source before implementation. Do not regenerate the
project or silently fall back to the older published branch.

Read AGENTS.md, CODEX_HANDOFF.md, JARVIS_PROGRESS.md, JARVIS_PLAN.md,
docs/jarvis/MASTER_SPEC.md, JARVIS_REVIEW.md, THREAT_MODEL.md,
docs/jarvis/UPSTREAM_BOUNDARY.md, docs/jarvis/LOCAL_DEVELOPMENT.md,
docs/jarvis/MEMORY.md, docs/jarvis/ENGINEER.md, docs/jarvis/TUTOR.md and
docs/jarvis/GAME_MASTER.md. MASTER_SPEC.md remains the complete product
specification; progress is the truthful checkpoint, not a full-system completion
claim.

Preserve original Graphify source, CLI, metadata/lock, licenses and skill
generation. Preserve exact one-use approvals, audit, durable cancellation/recovery,
owner/mode/namespace/visibility filtering before context, human memory acceptance,
Engineer's kernel-verified no-host-fallback worker and artifact provenance, and
Tutor's authenticated learner-evidence boundary. Preserve Game Master's trusted
membership lookup, SQL visibility-before-limit, GM-secret exclusion, noncanonical
transcripts, human-default PC rolls, bounded one-use delegation, dice provenance
and human-approved canonical events. Never infer authority from prompts, memory,
Graphify, prose or campaign entries.

Implement phase 9 next: the responsive Command Center/PWA described in the master
specification. Provide an actual runnable frontend, not static mockups. It must use
the existing authenticated APIs and expose clear mode switching and useful
Engineer, Tutor, Game Master, memory/approval and run-state surfaces without
claiming unfinished Chief of Staff or voice behavior. Include loading, empty,
error, cancellation, approval and reconnect states; responsive desktop/mobile
layouts; keyboard navigation, visible focus, semantic labels and reduced-motion
support. Render all model, source, memory, transcript and campaign content as
untrusted text—no unsafe HTML, script or URL execution. Do not place bearer tokens,
GM secrets or player-private data in logs, URLs, persistent browser storage,
service-worker caches or another role's UI state.

Choose a maintainable frontend toolchain inside the JARVIS application boundary,
pin dependencies and document exact local/production build commands. Keep the API
contract explicit and add only narrowly scoped backend endpoints when the UI truly
needs them. Provide a restrictive content-security policy, safe PWA manifest and
service worker behavior, cache only non-sensitive static assets, and make offline
limitations honest. No CDN/runtime dependency or paid service should be required.

First record receiving checks. Add component/contract/accessibility/security tests
and a meaningful offline E2E that exercises authentication, mode switching, a
durable run and at least Tutor and Game Master workflows against fake providers.
Add adversarial tests for HTML/script injection, malicious links, authorization
errors, stale/cross-role state, secret caching/logging and oversized content. Run
the existing application suites against disposable PostgreSQL and PostgreSQL/
pgvector with `JARVIS_TEST_SANDBOX=true`, frontend lint/type/test/build checks, and
appropriate upstream checks. Use scoped Graphify queries for code navigation;
source/tests remain ground truth. After source edits run `graphify update .`.

Review the browser/API trust boundary, authentication handling, caching, role
changes, accessibility and dependency/build output; fix severe findings. Update
progress, review, report, setup, verification snapshots and this continuation
prompt, then commit a reviewable local Phase 9 checkpoint.

Do not publish, merge, deploy or send external communications without authorization.
Chief of Staff projects/watchers, optional voice/integrations and complete
production hardening remain later work; do not imply their completion.
