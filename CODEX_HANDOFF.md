# JARVIS handoff to Codex

This repository contains the original Graphify project and the JARVIS foundation
created from [the full supplied specification](docs/jarvis/MASTER_SPEC.md).
The checkpoint branch is `jarvis/foundation`, based on Graphify 0.9.77 at
`5c7b84792f453582676548185aaec3824d51dfe2`.

## Open the project in another Codex session

The recommended transfer is the complete branch in your existing repository,
`Mandy3735/graphify`. Once that branch is published, connect/select this repository
in Codex and select `jarvis/foundation` as the starting branch. Paste the contents
of [CODEX_NEXT_PROMPT.md](docs/jarvis/CODEX_NEXT_PROMPT.md) into the task.
Codex receives the source, tests, migrations, dependency locks, original prompt,
licenses, and project history together. Chat history is not required.

If using Codex locally, open a checkout of this branch:

```sh
git clone --branch jarvis/foundation https://github.com/Mandy3735/graphify.git graphify-jarvis
cd graphify-jarvis
```

Publishing is a separate step from preparing this checkpoint. This document does
not establish that a GitHub upload has happened; verify the remote branch and its
commit against the delivery manifest before starting another session.

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

Phases 0–4 are implemented in the independent `apps/jarvis` Python package:
authenticated FastAPI, PostgreSQL/Alembic, Graphify adapter, fake and official
OpenAI Responses providers, durable bounded runs, typed tools, deterministic
policy, exact one-use approvals, cancellation, and audit records.

The foundation suite passed **59 tests including real PostgreSQL**. Application
lint, format, typing, package builds, and HTTP smoke checks passed. Upstream
Graphify regression results were 6,470 passed, 108 skipped, and 9 failures, all
present in the earlier baseline. See progress and baseline documents for the
environment limitations; do not present the upstream suite as fully passing.

The entire JARVIS specification is not complete. Personal memory, full Engineer
edit/test workflow, dedicated Tutor and Game Master workflows, Command Center,
and voice remain pending. The next implementation milestone is **phase 5**.

## Portable offline transfer

The delivery folder contains:

- `JARVIS-foundation.bundle`: self-contained Git history and checkpoint branch.
- `JARVIS-foundation-source.zip`: all tracked source files for manual inspection.
- `JARVIS-foundation.patch`: checkpoint changes against the original parent.
- `CODEX_NEXT_PROMPT.md`: a standalone continuation prompt.
- `manifest.json` and `checksums.json`: checkpoint identity, file inventory,
  verification summary, and SHA-256 checksums.
- Engineering/setup documents and the installable foundation wheel.

Restore the bundle in a fresh local directory:

```sh
git clone --branch jarvis/foundation JARVIS-foundation.bundle graphify-jarvis
cd graphify-jarvis
git status --short
git rev-parse HEAD
```

Compare `HEAD` to `checkpoint_commit` in `manifest.json`. To inspect a bundle
before cloning, run `git bundle list-heads JARVIS-foundation.bundle`.
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
