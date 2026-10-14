# Next task — Phase 12 adversarial review

Continue from local jarvis/phase-11-hardening; inspect HEAD/status and read the handoff,
progress/plan/review/threat model, complete MASTER_SPEC, upstream boundary, local setup,
HARDENING.md, VOICE.md and PHASE11_REPORT.md. Phase 11 is local unless explicitly pushed
later; published Phase 10 is 8aa688a. Do not regenerate or fall back to upstream v8.

Act as a hostile senior reviewer of all delivered scope: Graphify coupling/mergeability,
authorization/exact approvals, secret handling, injection, workers, model fallback and
budget assumptions, DB role/migrations/transactions/lease loss, HTTP/async lifecycle,
voice crash reconciliation, Game Master visibility, audit bypasses, frontend/cache/device
accessibility, deployment/proxy trust and test gaps. Compare claimed milestones against
actual master acceptance and distinguish deferred product scope from security defects.

Fix every critical/high issue found within supported scope. Never enable production
live microphone without a verifiable remote generation/cost authority boundary. Do not
weaken upstream or kernel/security checks to fit environment restrictions. Preserve
immutable migrations and canonical ownership/state/policy contracts; use additive
changes. Run targeted and appropriate full dual-DB/pgvector/kernel/backend/frontend/
browser/upstream/type/scan/package regressions, synchronize Graphify, document actual
results/remaining risks in JARVIS_REVIEW.md/progress/report and make a local checkpoint.
Do not pay for provider calls, publish, merge, deploy or send communications without
user authorization. The task is adversarial review, not autonomous production release.
