# JARVIS handoff to Codex

This repository contains the original Graphify project and the JARVIS foundation
created from [the full supplied specification](docs/jarvis/MASTER_SPEC.md).
The current published checkpoint branch is `jarvis/phase-7-tutor`, based on published
Phase 6 tip `b5c613ffae1163b30e5b8c9897afec6abce175ea`, preserving
Graphify 0.9.77 at
`5c7b84792f453582676548185aaec3824d51dfe2`. The foundation was published on
`jarvis/foundation`; the published phase-5 handoff branch is
`jarvis/phase-5-memory` in `Mandy3735/graphify`.

## Open the project in another Codex session

The preceding complete Phase 6 handoff is
[`Mandy3735/graphify:jarvis/phase-6-engineer`](https://github.com/Mandy3735/graphify/tree/jarvis/phase-6-engineer).
Its implementation commit is `dd69e080b8bd4b7aed72b2df07c54a8c879c5f93`.
The complete Tutor handoff is
[`Mandy3735/graphify:jarvis/phase-7-tutor`](https://github.com/Mandy3735/graphify/tree/jarvis/phase-7-tutor).
Its implementation commit is `6d35a7bf22b17b299150ae8731082ac19c41f90d`.
The older `jarvis/phase-5-memory` branch does not contain Engineer or Tutor.

For local Codex, open this repository and select `jarvis/phase-7-tutor`. Another
cloud session should use the published Phase 7 branch and verify its HEAD before
continuing. The older verified Phase 6 bundle remains in `work/phase6-delivery`;
it is not a Phase 7 handoff. Use the continuation prompt for Phase 8.

The receiving Phase 6 commit is `b5c613ffae1163b30e5b8c9897afec6abce175ea`.
Resolve current local HEAD with `git rev-parse HEAD`. Existing delivery manifests
identify older snapshots. The user authorized the Phase 6 push on 2026-10-07 and
the Phase 7 push on 2026-10-10. No merge or deployment is authorized or claimed.

## Read these files first

1. `AGENTS.md` and this guide.
2. `JARVIS_PROGRESS.md`: implemented scope, measured checks, limitations, next phase.
3. `JARVIS_PLAN.md`: phases and acceptance criteria.
4. `docs/jarvis/MASTER_SPEC.md`: the complete original product specification.
5. `docs/jarvis/LOCAL_DEVELOPMENT.md`: install, migrate, run, and test commands.
6. `docs/jarvis/ENGINEER.md`, `docs/jarvis/TUTOR.md`, `JARVIS_REVIEW.md`, `THREAT_MODEL.md`, and
   `docs/jarvis/UPSTREAM_BOUNDARY.md`.

`JARVIS_ENGINEERING_REPORT.md` contains the detailed engineering record. The
portable `docs/jarvis/verification/` snapshots retain the foundation test result
and the upstream failure comparison; full session logs remain scratch files.

## What has been delivered

Phases 0–7 are implemented in the independent `apps/jarvis` Python package:
authenticated FastAPI, PostgreSQL/Alembic, Graphify adapter, fake and official
OpenAI Responses providers, durable bounded runs, typed tools, deterministic
policy, exact one-use approvals, cancellation, audit records, and structured
personal memory with provenance, filtered retrieval, ContextBuilder and inspector
APIs, plus kernel-isolated small Engineer changes, tests, actual Git patches,
graph update/impact and owner/run-scoped artifacts, plus canonical source-grounded
Tutor objectives, teaching artifacts, quizzes, human attempts, evidence-backed
mastery and spaced reviews. Optional pgvector and
deterministic fake embeddings are verified.

The receiving foundation suite passed **59 tests including real PostgreSQL**.
The phase-5 suite passed **106 tests, 1 configuration-specific skip** on each of
ordinary PostgreSQL and PostgreSQL/pgvector. Application
lint, format, typing, package builds, and HTTP smoke checks passed. Upstream
Graphify regression results were 6,470 passed, 108 skipped, and 9 failures, all
present in the earlier baseline. See progress and baseline documents for the
environment limitations; do not present the upstream suite as fully passing.

The 2026-10-07 publication check repeated GitHub's installation commands in a
fresh checkout. Explicitly configuring Pyright's Graphify source path fixed the
nine missing-import errors seen in the foundation workflow. Lint, format, typing,
wheel/sdist builds, and both PostgreSQL suites passed in that fresh environment.

Phase 6 passed **137 tests, one configuration-specific skip** on each database
configuration with real kernel tests explicitly enabled in the fresh workflow
dependency environment. Lint/format/types, package builds and real HTTP smoke
passed. Authorized upstream regression passed 6,472 tests with 108 skips and
seven existing DNS failures; there were no new failure identifiers. These measured
results are local; check the branch's GitHub Actions for remote verification.

Phase 7 passed **152 tests, one configuration-specific skip** on each of ordinary
PostgreSQL and PostgreSQL/pgvector with real kernel tests enabled. Ruff, format and
Pyright, the 0.4.0 package build, migrated PostgreSQL API smoke, relevant upstream
checks and Graphify synchronization/query/explain passed. These are local results
published with the Phase 7 source; remote CI status must be checked separately.

The entire JARVIS specification is not complete. Engineer scope/limits are in
docs/jarvis/ENGINEER.md; Tutor scope/limits are in docs/jarvis/TUTOR.md. Game Master,
Command Center and voice remain pending. Dedicated inspector UI and campaign
membership/sharing remain later phases. The next implementation milestone is **phase 8**.

## Portable offline transfer

The phase-6 delivery is prepared in `work/phase6-delivery`. Earlier files in
`work/phase5-delivery` and `work/delivery` retain their prior snapshots and do not
contain Phase 6.

- `JARVIS-phase6.bundle`: complete Git history and the local Engineer branch.
- `JARVIS-phase6-source.zip`: tracked source snapshot.
- `JARVIS-phase6.patch`: changes against the receiving phase-5 handoff.
- `manifest.json` and `SHA256SUMS`: exact commit, file inventory and checksums.
- Updated handoff/prompt/Engineer/setup/report documents and 0.3.0 wheel/sdist.

Restore in a fresh local directory:

```sh
git clone --branch jarvis/phase-6-engineer JARVIS-phase6.bundle graphify-jarvis
cd graphify-jarvis
git status --short
git rev-parse HEAD
```

Compare HEAD to `checkpoint_commit` in the manifest. Inspect bundle heads with
`git bundle list-heads JARVIS-phase6.bundle` before cloning if needed.

The delivery intentionally excludes virtual environments, caches, databases,
generated graphs, `.env` credentials, and transient worker state. Recreate those
from the checked-in setup instructions. Existing chat attachments are represented
by the preserved master specification; no attachment pointer is required.

## Continue safely

Preserve the original Graphify source, CLI, package metadata, locks, licenses and
skill-generation behavior. Keep JARVIS changes within its application boundary
unless an explicit integration requirement calls for an additive upstream change.
Recheck actual tests in the receiving environment, use fake providers by default,
and keep authorization/owner filtering ahead of model context construction.
Update progress, review, migrations and meaningful tests at each checkpoint.
