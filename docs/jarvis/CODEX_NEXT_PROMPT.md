# Copy this prompt into the next Codex task

Continue Graphify → JARVIS from the published branch
`Mandy3735/graphify:jarvis/phase-6-engineer` or its verified Git bundle checkout.
The implementation commit is `dd69e080b8bd4b7aed72b2df07c54a8c879c5f93`;
later handoff commits may follow it. The published `jarvis/phase-5-memory`
branch is the preceding memory checkpoint. Check branch, HEAD, working tree and
source before implementing; do not regenerate the project.

Read AGENTS.md, CODEX_HANDOFF.md, JARVIS_PROGRESS.md, JARVIS_PLAN.md,
docs/jarvis/MASTER_SPEC.md, JARVIS_REVIEW.md, THREAT_MODEL.md,
docs/jarvis/UPSTREAM_BOUNDARY.md, docs/jarvis/LOCAL_DEVELOPMENT.md,
docs/jarvis/MEMORY.md and docs/jarvis/ENGINEER.md. MASTER_SPEC.md remains the full
original specification. Phase 6 delivers a bounded Linux/system-Python workflow,
not unrestricted project execution or a full personal operating system.

Preserve original Graphify source, CLI, root metadata/lock, licenses and skill
generation. Preserve the separate JARVIS application's exact one-use approvals,
owner/mode/namespace/visibility filtering before context, human memory acceptance,
race-safe correction/deletion, durable cancellation/recovery and audit. Engineer
execution is disabled by default, verified by a real kernel probe, uses a private
snapshot/worktree and read-only offline worker, and has no host fallback. Preserve
resource/time/output limits, failure status, source/diff/graph provenance and
artifact owner checks. Migration 0002 remains current; use additive new migrations.

Implement phase 7 next: a complete Tutor workflow with persisted learning
objectives, source-grounded teaching/explanations/worked examples/Socratic prompts,
quizzes, human learner attempts, answer evaluation, mastery evidence and scheduled
spaced-review tasks. Mastery requires actual learner performance, never generated
prose, a model's own answer, or an explanation alone. Keep canonical learning state
separate from generic memory. Model proposals cannot fabricate human attempts or
grant their own authority. Retain references to learning sources and attempt/
evaluation evidence; apply owner/capability boundaries before reads and grading.

First record the receiving checks. Add a meaningful offline Tutor E2E: objective,
source-backed lesson, quiz, learner response, evaluation, evidence-backed mastery,
and due review. Test incorrect answers, explanations without attempts, fabricated
model mastery/attempts, retries and duplicate submissions, ownership, prompt
injection, source provenance and review scheduling. Use fake providers by default.
Run existing application suites with both disposable PostgreSQL configurations,
JARVIS_TEST_SANDBOX=true on supported Linux, plus relevant upstream checks. Explicit
kernel-test opt-in must fail when isolation is unavailable; do not hide that with
a skip. Record unsupported environment constraints honestly. No paid-service test
dependency or assumption that any configured live model exists.

Use scoped Graphify queries for navigation; source/tests remain ground truth.
After source edits run graphify update . as AGENTS.md requires. Review permissions,
learner-evidence integrity, persistence/races and retrieval boundaries; fix serious
findings. Update progress/review/report/setup and the continuation prompt, then
commit a reviewable local Tutor checkpoint. Do not publish, merge, deploy or send
external communications without authorization. Chief of Staff/watchers,
Game Master, frontend/PWA, voice/integrations and production hardening remain later
work; do not imply their completion by adding labels or placeholders.
