# JARVIS handoff to Codex

This repository contains the original Graphify project and the JARVIS foundation
created from [the full supplied specification](docs/jarvis/MASTER_SPEC.md).
The current published checkpoint branch is `jarvis/phase-6-engineer`, based on
`5f622c094f0a023a0cbcfc0f39850f9866621b78` (published phase 5), preserving
Graphify 0.9.77 at
`5c7b84792f453582676548185aaec3824d51dfe2`. The foundation was published on
`jarvis/foundation`; the published phase-5 handoff branch is
`jarvis/phase-5-memory` in `Mandy3735/graphify`.

## Open the project in another Codex session

The complete Phase 6 handoff is
[`Mandy3735/graphify:jarvis/phase-6-engineer`](https://github.com/Mandy3735/graphify/tree/jarvis/phase-6-engineer).
Its implementation commit is `dd69e080b8bd4b7aed72b2df07c54a8c879c5f93`.
The older `jarvis/phase-5-memory` branch does not contain the Engineer implementation.

For local Codex, open this repository and select `jarvis/phase-6-engineer`. For
another cloud session, select `Mandy3735/graphify` and `jarvis/phase-6-engineer`
in Codex. Alternatively restore `work/phase6-delivery/JARVIS-phase6.bundle`
and verify HEAD against that directory's manifest before continuing. Source/tests,
locks, original specification, migrations and history are included; chat history
is unnecessary. Use the continuation prompt for Phase 7 in this checkout.

The receiving phase-5 commit is `5f622c094f0a023a0cbcfc0f39850f9866621b78`.
Resolve current local HEAD with `git rev-parse HEAD`. Delivery manifests identify
specific snapshots, not subsequent commits. The user authorized the Phase 6 push
on 2026-10-07, and GitHub's branch ref was verified against the implementation SHA.

## Read these files first

1. `AGENTS.md` and this guide.
2. `JARVIS_PROGRESS.md`: implemented scope, measured checks, limitations, next phase.
3. `JARVIS_PLAN.md`: phases and acceptance criteria.
4. `docs/jarvis/MASTER_SPEC.md`: the complete original product specification.
5. `docs/jarvis/LOCAL_DEVELOPMENT.md`: install, migrate, run, and test commands.
6. `docs/jarvis/ENGINEER.md`, `JARVIS_REVIEW.md`, `THREAT_MODEL.md`, and
   `docs/jarvis/UPSTREAM_BOUNDARY.md`.

`JARVIS_ENGINEERING_REPORT.md` contains the detailed engineering record. The
portable `docs/jarvis/verification/` snapshots retain the foundation test result
and the upstream failure comparison; full session logs remain scratch files.

## What has been delivered

Phases 0–6 are implemented in the independent `apps/jarvis` Python package:
authenticated FastAPI, PostgreSQL/Alembic, Graphify adapter, fake and official
OpenAI Responses providers, durable bounded runs, typed tools, deterministic
policy, exact one-use approvals, cancellation, audit records, and structured
personal memory with provenance, filtered retrieval, ContextBuilder and inspector
APIs, plus kernel-isolated small Engineer changes, tests, actual Git patches,
graph update/impact and owner/run-scoped artifacts. Optional pgvector and
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

The entire JARVIS specification is not complete. Engineer scope/limits are in
docs/jarvis/ENGINEER.md. Dedicated Tutor and Game Master workflows, Command Center,
and voice remain pending. Dedicated inspector UI and campaign membership/sharing
remain later phases. The next implementation milestone is **phase 7**.

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
