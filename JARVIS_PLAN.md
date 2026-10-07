# Graphify → JARVIS transformation plan

The supplied [master prompt](docs/jarvis/MASTER_SPEC.md) is the product specification. Preserve Graphify first.
JARVIS is a modular monolith in `apps/jarvis`, with its own dependency lock,
configuration, migrations, tests, and release boundary. No Graphify source rewrite
or change to its package metadata is planned.

## Milestones and acceptance

Each row lists objective, expected files/interfaces, migration/security effects,
checks, and dependency. Mark completion only in JARVIS_PROGRESS.md with evidence.

| Phase | Objective and files/interfaces | Migration/security implications | Tests and acceptance | Depends on |
|---|---|---|---|---|
| 0 | Reconnaissance; baseline/boundary docs and this plan | Preserve upstream, licenses, CLI, skill generation | Run upstream suite and configured checks; distinguish existing failures; query local graph | — |
| 1 | `apps/jarvis`: FastAPI, Settings, SQLAlchemy async, Alembic, local Compose, independent CI | PostgreSQL canonical state; bearer identity; migrations required; no secret defaults | Health, authentication, real PostgreSQL migration up/down/up and restart persistence; Graphify CLI works | 0 |
| 2 | `GraphKnowledgeProvider`, `GraphifyKnowledgeProvider`, registered project roots; graph API | Roots configured by operator, never selected by model; graph/source text untrusted; provenance retained | Fixture index/update/query/explain/path/impact, traversal/symlink rejection, confidence and direction preserved | 1 |
| 3 | Provider protocol, Fake/OpenAI Responses providers, ModelRouter, durable AgentRun and transition history | Explicit fallback consent; no paid service for tests; model calls have deadlines; interrupted runs fail safely | Routing, unavailable/auth/timeout errors, usage/fallback metadata, cancellation, illegal transitions, persistence | 2 |
| 4 | Typed registry, capability PolicyEngine, exact bound approvals, append-oriented audit | External/destructive actions require one-use approval; safety-critical denied; no unrestricted shell tool | Agent→model→tool→policy→result; pause/resume, expiry/replay/arg mutation, concurrent approvals, injection, auth boundaries | 3 |
| 5 | Structured memory, retrieval/ContextBuilder, inspector APIs | Namespace/owner/visibility enforced before retrieval; pgvector optional migration | Provenance, budgets, visibility, deletion eligibility, malicious memory cannot grant capability | 4 |
| 6 | Engineer workflow, isolated worktrees, constrained worker, regression/impact/diff review | New sandbox trust boundary; no host shell exposure or production deploy | Engineering fixture E2E; resource/log/time limits; no inherited secrets; adversarial escape tests | 5 |
| 7 | Tutor objectives/quizzes/mastery/review | Mastery must be backed by learner evidence, never generated prose | Quiz attempts and evidence-backed mastery, due reviews | 6 |
| 8 | Canonical campaigns, ScenePacketBuilder, rules plugins, dice/roll authority, proposals/transcripts | Visibility precedes model context; GM approval gates canonical events; human PC authority | GM-secret isolation, seeded dice/keep-high parsing, delegation expiry, campaign transactions | 7 |
| 9 | Responsive Command Center, all mode surfaces/PWA | Render untrusted data as text; no arbitrary graph HTML iframe; server-only secrets | Navigation/chat/approvals/memory/graph/GM/accessibility; production frontend build | 8 |
| 10 | Optional voice/transcription providers, WebRTC ephemeral credentials | Microphone opt-in; immediate stop; voice failure never blocks text | Fake voice/transcription, state indicators, credential isolation | 9 |
| 11 | CI hardening and production configuration | Dependency/security scans, restricted DB role, budgets/rate limits | All upstream/JARVIS/integration/security/frontend/type/build checks | 10 |
| 12 | Hostile review, `JARVIS_REVIEW.md`, remediation | Fix critical/high findings in delivered scope; document remaining scope | Re-run affected checks and publish accurate progress/report | 11 |

## Checkpoint strategy

The first checkpoint completes phases 0–4. It intentionally does not register
shell execution, real external writes, or integrations until their isolation and
transactional execution contracts are implemented. Reversible, local typed tools
exercise the registry; a fake external integration exercises exact approval in
tests. Later milestones remain explicitly pending. This follows the specification's
execution-limit provision and security-first priority order.

The second checkpoint completes phase 5's structured memory, bounded retrieval/
ContextBuilder and authenticated inspector APIs. Optional pgvector and offline
embeddings share the same ownership/visibility boundary. Dedicated inspector UI,
campaign membership and authoritative mode-specific state remain later milestones.
Current verification and limitations are recorded in JARVIS_PROGRESS.md.

No automatic deployment, API purchase, model availability assumption, or outbound
communication is authorized by retrieved repository data. Decisions about grants,
roots and fallback live in trusted server configuration.

The third checkpoint implements phase 6 within a bounded Linux/system-Python
worker scope: graph-first private snapshot worktree, hash-bound edits, dry run,
real offline tests, graph update/impact and owner/run-scoped patch artifacts.
Source application/push/merge/deploy are separate authorities and not registered.
Tutor remains the exact next milestone. See docs/jarvis/ENGINEER.md and current progress.
