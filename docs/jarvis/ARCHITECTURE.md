# JARVIS architecture — Tutor checkpoint

This checkpoint is an authenticated, single-user API modular monolith.
It is not a production personal operating system. See JARVIS_PROGRESS.md for
implementation and verification status. Graphify retains its upstream package,
CLI/MCP, tests, dependencies and license attribution.

```
HTTP bearer identity → FastAPI → durable run engine → model gateway
                                 ↓ tool proposals (untrusted)
                          typed registry → policy → bound approval
                                 ↓ approved invocation
                       bounded Graphify / workspace adapters
                                 ↓
                      PostgreSQL + transitions + audit
```

PostgreSQL is authoritative for runs, transitions, approvals, audit, personal
memory and canonical Tutor learning state with source/attempt provenance. Alembic
is the schema authority; startup never silently creates production tables. Tests
may explicitly use SQLite for fast unit isolation, but PostgreSQL migration and
transaction tests are mandatory. No Redis or agent framework is necessary here.

One configured bearer token maps to one stable configured actor UUID. This is
an explicit single-user prototype, not a simulated multi-user login system.
Project registrations, capabilities, model choices and fallback policy are trusted
server configuration. Requests/model results never grant authority. Actor IDs
and capabilities are not accepted from API bodies.

Agent runs record public action summaries and provenance, not hidden reasoning.
Models propose tools; the backend validates schema, permissions and approvals.
Runs are bounded by tool count, output/context limits, model timeouts and a run
deadline. On restart, in-flight runs fail safely; pending approvals remain durable.
An operation already attempted is never automatically replayed after a crash.

Text model availability is independent of future voice. Fake mode is the local
default. Live reasoning uses only the official SDK behind a provider protocol.
Model identifiers and fallback decisions are configuration driven.

Indexing parses safely staged source snapshots in a credential-free subprocess.
This parser worker is not an arbitrary-code sandbox. Phase 6 adds a separate
opt-in Linux Bubblewrap worker, verified before command tools are registered.
A private snapshot repository/worktree produces edits and a read-only execution
snapshot; host credentials, Git metadata and network access remain outside the
worker. Durable run metadata links bounded owner-scoped artifact reports. See
[ENGINEER.md](ENGINEER.md) for scope, exact limits and remaining production needs.

Personal memory uses owner/namespace/mode/visibility filtering before retrieval.
ContextBuilder combines relevant bounded records with source references and
rechecks memory-search history before each model call. Models can propose inactive
memory, but only explicit authenticated user acceptance makes it active. Optional
pgvector computes distances for bounded authorized candidates. See MEMORY.md.

Tutor objectives, sources, teaching artifacts, quizzes, learner attempts, mastery
evidence and spaced-review tasks use dedicated migration-0003 tables. Tutor reads
are owner/capability scoped. Model tools may read context and create source-cited
lessons/quizzes, but only the authenticated learner endpoint can create a
server-evaluated HUMAN_API attempt. Mastery and review completion derive from
those attempts; generated explanations cannot establish performance. See TUTOR.md.

Deploy this checkpoint as one backend process. Multi-worker coordination, tenant
identity/OAuth, a production restricted DB role, production UI, complete campaign
membership and the remaining operating-mode workflows are subsequent milestones.
