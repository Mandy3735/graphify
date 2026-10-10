# Policy and approval contract

Every registered tool has a strict input/output schema, risk, required capability
set, timeout and idempotency declaration. Unknown model tool names are rejected.
Capability checks precede approval. READ_ONLY and REVERSIBLE_WRITE are allowed
only within their concrete registered scope. EXTERNAL_WRITE and DESTRUCTIVE
require explicit human approval. SAFETY_CRITICAL is denied in this prototype.

An approval binds normalized validated arguments (including defaults), tool
definition/risk/capabilities, target, actor, run, expiry and random nonce through
a SHA-256 operation digest. Consume a pending approval with a conditional atomic
update in the same transaction as the run state transition and audit event.
One approval is one invocation; mutation, replay, expiration and another run
cannot reuse it. Rejection cancels the paused run.

Model proposals, repository instructions, graph nodes, source comments and tool
results are untrusted data. They cannot change these deterministic checks.
Exact approval data is displayed via authenticated API responses. No capability
grant/policy mutation/audit deletion tool exists.

Approval consumption precedes any side effect. If a non-idempotent effect or
process fails afterward, do not automatically retry it: report failure and require
human reconciliation. Claiming exactly-once delivery to a remote service without
its idempotency support would be incorrect. No real external integration is
registered at this checkpoint; fake integrations verify the contract in tests.

Phase 6 adds opt-in engineer.write and engineer.execute grants. Engineer tools
remain ENGINEER-only, bind the actual run/project/actor, and operate only on
private snapshots/worktrees. Kernel readiness is required before registration.
No source apply, repository commit, push, merge, deployment or external-write
adapter is registered. Declared command failure makes the run FAILED. See
[ENGINEER.md](ENGINEER.md) for the enforced execution boundary.

Phase 7 adds `tutor.read`, `tutor.write` and `tutor.attempt`. Tutor model tools are
TUTOR-only and bound to the actual run/objective. They can inspect grounded context
and create source-cited teaching material or quizzes. No attempt, grading, mastery
or review-completion model tool exists. The authenticated human endpoint creates
server-stamped attempts; deterministic service code alone evaluates them and
derives mastery/review state. See [TUTOR.md](TUTOR.md).
