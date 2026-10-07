# JARVIS handoff to Codex

This repository contains the original Graphify project and the JARVIS foundation
created from [the full supplied specification](docs/jarvis/MASTER_SPEC.md).
The current checkpoint branch is `jarvis/phase-5-memory`, based on the foundation
at `b04e109ab2d15967d06dff364f376de41e92bde0`, preserving Graphify 0.9.77 at
`5c7b84792f453582676548185aaec3824d51dfe2`. The foundation was published on
`jarvis/foundation`; the complete phase-5 handoff branch is
`jarvis/phase-5-memory` in `Mandy3735/graphify`.

## Open the project in another Codex session

The recommended transfer is the complete branch in your existing repository,
`Mandy3735/graphify`. Connect/select this repository
in Codex and select `jarvis/phase-5-memory` as the starting branch. Paste the contents
of [CODEX_NEXT_PROMPT.md](docs/jarvis/CODEX_NEXT_PROMPT.md) into the task.
Codex receives the source, tests, migrations, dependency locks, original prompt,
licenses, and project history together. Chat history is not required.

If using Codex locally, open a checkout of this branch:

```sh
git clone --branch jarvis/phase-5-memory https://github.com/Mandy3735/graphify.git graphify-jarvis
cd graphify-jarvis
```

The phase-5 implementation commit is `dc37855efea99f2074e5fe6e686df2a62b5ac6e3`.
The handoff branch also includes the subsequent GitHub type-check configuration
fix and these updated instructions. Verify its remote HEAD before starting
another session. Offline delivery manifests identify their earlier snapshots;
they do not identify subsequent branch commits.

## Read these files first

1. `AGENTS.md` and this guide.
2. `JARVIS_PROGRESS.md`: implemented scope, measured checks, limitations, next phase.
3. `JARVIS_PLAN.md`: phases and acceptance criteria.
4. `docs/jarvis/MASTER_SPEC.md`: the complete original product specification.
5. `docs/jarvis/LOCAL_DEVELOPMENT.md`: install, migrate, run, and test commands.
6. `JARVIS_REVIEW.md`, `THREAT_MODEL.md`, and `docs/jarvis/UPSTREAM_BOUNDARY.md`.

`JARVIS_ENGINEERING_REPORT.md` contains the detailed engineering record. The
portable `docs/jarvis/verification/` snapshots retain the foundation test result
and the upstream failure comparison; full session logs remain scratch files.

## What has been delivered

Phases 0–5 are implemented in the independent `apps/jarvis` Python package:
authenticated FastAPI, PostgreSQL/Alembic, Graphify adapter, fake and official
OpenAI Responses providers, durable bounded runs, typed tools, deterministic
policy, exact one-use approvals, cancellation, audit records, and structured
personal memory with provenance, filtered retrieval, ContextBuilder and inspector
APIs. Optional pgvector and deterministic fake embeddings are verified.

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

The entire JARVIS specification is not complete. Full Engineer
edit/test workflow, dedicated Tutor and Game Master workflows, Command Center,
and voice remain pending. Dedicated inspector UI and campaign membership/sharing
remain later phases. The next implementation milestone is **phase 6**.

## Portable offline transfer

The phase-5 delivery is prepared in `work/phase5-delivery`; verify its own manifest
and branch when restoring this checkpoint. Original files in `work/delivery`
retain the earlier foundation snapshot and do not contain phase 5.

- `JARVIS-phase5.bundle`: self-contained Git history and phase-5 branch.
- `JARVIS-phase5-source.zip`: all tracked source files for manual inspection.
- `JARVIS-phase5.patch`: changes against the verified foundation parent.
- `CODEX_NEXT_PROMPT.md`: a standalone continuation prompt.
- `manifest.json` and `checksums.json`: checkpoint identity, file inventory,
  verification summary, and SHA-256 checksums.
- Engineering/setup documents, memory guide, and installable 0.2.0 wheel/sdist.

Restore the bundle in a fresh local directory:

```sh
git clone --branch jarvis/phase-5-memory JARVIS-phase5.bundle graphify-jarvis
cd graphify-jarvis
git status --short
git rev-parse HEAD
```

Compare `HEAD` to `checkpoint_commit` in `manifest.json`. To inspect a bundle
before cloning, run `git bundle list-heads JARVIS-phase5.bundle`.
Use the bundle for a full Git checkout; the source ZIP is a source snapshot.

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
