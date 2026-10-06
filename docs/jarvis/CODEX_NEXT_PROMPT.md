# Copy this prompt into the next Codex task

Continue the Graphify → JARVIS project from branch `jarvis/foundation` in
`Mandy3735/graphify` (or its restored Git bundle checkout). This is an existing
implementation. Begin by checking the branch, commit, working tree, and source
files; do not regenerate the project from scratch.

Read `AGENTS.md`, `CODEX_HANDOFF.md`, `JARVIS_PROGRESS.md`, `JARVIS_PLAN.md`,
`docs/jarvis/MASTER_SPEC.md`, `JARVIS_REVIEW.md`, `THREAT_MODEL.md`,
`docs/jarvis/UPSTREAM_BOUNDARY.md`, and `docs/jarvis/LOCAL_DEVELOPMENT.md`.
The full original prompt is preserved in MASTER_SPEC.md. Treat it as the product
specification and the progress file as the truthful implementation checkpoint.

Phases 0–4 are delivered in `apps/jarvis`; 59 foundation tests, including real
PostgreSQL, passed. Dedicated modes/UI/voice are not finished. Preserve Graphify's
existing functionality, package metadata, lock, CLI, licenses and skill generation.
Keep the independent JARVIS package, secure tool registry, bounded run engine,
one-use approval binding, model fallback consent, and audit guarantees intact.
Do not fix unrelated upstream formatting/type issues as part of this milestone.

Implement phase 5 next: structured personal memory in PostgreSQL, explicit memory
classes, owner/namespace/visibility filtering BEFORE retrieval/model context,
provenance and correction/deletion eligibility, bounded relevance/token budgets,
a ContextBuilder, and authenticated memory inspector APIs. Keep personal memory
separate from Graphify's code knowledge graph. Add pgvector only behind explicit
configuration and preserve an offline retrieval path with deterministic fake
embeddings. Follow the master specification's exact phase-5 requirements.

First run the current application checks and record the receiving environment's
baseline. Implement necessary migrations and meaningful tests for isolation,
provenance, context budgets, deletion/correction behavior, and malicious memory
that attempts to grant capabilities. Run existing JARVIS tests and real local
PostgreSQL integration tests using a disposable `_test` database, plus appropriate
upstream regression checks. Keep fake providers as the default; paid model calls
and external integrations require their own configured credentials/authorization.

Use scoped Graphify queries for source questions when the graph is available;
source and tests remain the ground truth. Regenerate/update the local Graphify
graph after code edits as AGENTS.md requires. Review the changed security boundary,
fix high-severity findings, and update JARVIS_PROGRESS.md, JARVIS_REVIEW.md and the
engineering report with actual results and the next task. Do not claim pending
milestones are complete. Commit a reviewable phase-5 checkpoint; do not deploy,
merge, or publish to an external service without authorization.
