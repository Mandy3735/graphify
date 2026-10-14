# Phase 12 engineering report — 2026-10-14

Reviewed published Phase 11 `6d0b05acdc7db62256cf8134e4990dd62a390000` and created
local `jarvis/phase-12-adversarial-review`. Application **0.9.0**, unchanged Alembic
revision **0005**. Resolve the final checkpoint with `git rev-parse HEAD`.
No Phase 12 push, merge, deployment, outbound message or paid provider call occurred.
My-JARVIS-AI- remains untouched.

## Review outcome

Three high and three medium findings were fixed. Public slow-body/response work
cannot consume authenticated HTTP slots. Conventional credential configs are
excluded from workspace reads, Graphify staging and tracked Engineer snapshots.
Campaign scenes are refreshed after retrieval awaits; historical scene outputs
are reauthorized, while changed-state derived model/tool content is withheld using
a durable fingerprint/history cutoff. Older runs lacking a fingerprint fail closed
on their first resumed model context. Hidden active-location IDs are filtered.
Microphone setup and capture share a local 120-second deadline. Sign-out clears
credentials and aborts requests before isolated resource cleanup callbacks.

[JARVIS_REVIEW.md](../../JARVIS_REVIEW.md) records trigger, severity, reproduction,
remediation, tests and remaining risks; it reconciles every master E2E scenario
against actual evidence. Architecture, upstream mergeability, authorization/audit,
injection, secrets, sandbox, model/fallback/cost, database/async lifecycle, GM state,
frontend/cache/device/accessibility and deployment boundaries were reviewed.
No identified critical/high finding remains open within supported scope.

Nine regression cases failed on receiving code before fixes. Eleven final backend
adversarial cases and three new browser component/device cases cover the findings.
The focused GM/adversarial suite also checks derived secret arguments/prose, later
context builds and legacy runs. Existing exact-approval, kernel, role, transaction,
model and frontend regressions remain in the complete suites.

## Verification

Final measured results are in `verification/phase12-verification.json` and matching
text/JSON snapshots. Raw receiving, failing reproduction and intermediate logs
are retained in ignored `work/phase12`. Counts and elapsed times in the verification
artifact are observed local results, not GitHub CI results.

| Check | Final observed outcome |
|---|---|
| PostgreSQL + real kernel isolation | 228 passed, 1 opposite-vector-configuration skip |
| PostgreSQL/pgvector + real kernel isolation | 228 passed, 1 opposite-vector-configuration skip |
| Focused adversarial + GM suite | 30 passed |
| Frontend component/device/security/cache | 38 passed |
| Production Chromium | 5 passed, including mobile axe and mode/identity/GM secrecy |
| JARVIS Ruff lint/format and Pyright | Pass; zero type errors/warnings |
| Frontend TypeScript/ESLint/Prettier/build | Pass |
| Python/npm dependency audit | Zero reported vulnerabilities |
| Bandit | Zero medium/high; nine reviewed low findings; two inherited private-tmpfs annotations |
| Application wheel/sdist | 0.9.0 built; Python module/frontend parity and migration/deployment membership checked |
| Caddy template | Offline adaptation/validation passed; no infrastructure deployed |
| Graphify upstream suite | 6,470 passed, 108 skipped, nine unchanged baseline failure identifiers |
| Upstream Ruff lint | Pass |
| Upstream formatter / types | Existing drift: 413 files would reformat, 159 formatted; 618 type errors, 4 warnings |
| Graph synchronization | 20,050 nodes, 42,476 edges, 1,062 communities; scoped query/explain/one-hop impact passed |
| Preserved boundary | No change to Graphify core/tests, root metadata/lock/licenses, app Python dependency lock or migrations 0001–0005 |

Both full database runs enable `JARVIS_TEST_SANDBOX=true`, exercising all 13 real
kernel tests rather than skipping unsupported namespaces. PostgreSQL integration
checks migration upgrade/downgrade/upgrade and metadata parity, durable approval/
memory/Tutor/GM/quota races, real restricted-role permissions, lease ownership/loss
and restart recovery. Disposable ordinary/vector databases are separate.

Upstream failures remain the two repository-environment cases
`test_graphifyignore_hermetic_without_vcs` and `test_no_git_repo_raises`, plus seven
DNS-dependent URL/fetch cases. The exact identifiers are retained in the artifact.
No root-wide formatter/type refactor or weakening of upstream/security tests occurred.
Initial local script path mistakes were corrected. Context changes initially introduced
an extra router argument and optional-type errors; targeted tests/types caught them,
and final complete checks passed. Review then caught persistent/legacy history cutoff
cases; final suites were rerun after fixes. No failing result is presented as passing.

## Reproducible commands

From `/workspace/graphify/apps/jarvis`:

```sh
../../.venv/bin/ruff check .
../../.venv/bin/ruff format --check .
../../.venv/bin/pyright
../../.venv/bin/python -m pytest -q tests/test_adversarial.py tests/test_game_master.py
JARVIS_TEST_PSQL=/tmp/jarvis-phase12-psql JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-test-only@127.0.0.1:55432/jarvis_test JARVIS_TEST_SANDBOX=true ../../.venv/bin/python -m pytest -q
JARVIS_TEST_PSQL=/tmp/jarvis-phase12-psql JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-test-only@127.0.0.1:55432/jarvis_vector_test JARVIS_TEST_PGVECTOR=true JARVIS_TEST_SANDBOX=true ../../.venv/bin/python -m pytest -q
```

The session's trusted psql wrapper invokes the disposable container's real psql,
mapping host port 55432 to container 5432. CI uses native psql. Test credentials are
synthetic. Real namespace probes run through the permitted host execution path;
command restrictions are not worked around by disabling application isolation.

From `apps/jarvis/frontend`:

```sh
npm run check
npm run format:check
npm run test
npm run build
npm audit --json
JARVIS_CHROMIUM=/usr/bin/chromium npm run e2e
```

From repository root:

```sh
PATH=/workspace/graphify/.venv/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/ -q
.venv/bin/ruff check graphify tests
.venv/bin/ruff format --check graphify tests
.venv/bin/pyright --pythonpath .venv/bin/python
.venv/bin/bandit -r apps/jarvis/src -ll
.venv/bin/pip-audit --disable-pip --no-deps --cache-dir /workspace/.cache/pip-audit -r apps/jarvis/requirements.lock --format json
.venv/bin/python -m build --no-isolation apps/jarvis
.venv/bin/graphify update .
.venv/bin/graphify query 'ContextBuilder Ingress credential_config GameMasterService' --budget 1200
.venv/bin/graphify explain 'apps/jarvis/src/jarvis/context.py::ContextBuilder'
git diff --exit-code 6d0b05a -- graphify tests pyproject.toml uv.lock LICENSE LICENSE-MIT NOTICE apps/jarvis/requirements.lock apps/jarvis/migrations
git diff --check
```

Graph update is AST-only and paid-call-free. Query/explain and a scoped graph
neighbor check identify Engine/API/scene/path callers. Optional upstream extractor
warnings remain visible in the graph log. Python archive inspection verifies module
and public asset parity plus migration/deployment-template membership. Offline
Caddy validation uses the same network-disabled public template command recorded
in PHASE11_REPORT.md. No dependency selections changed.

## Supported scope and next work

Phase 12 review/remediation is complete within documented prototype bounds.
The full master product remains incomplete. Dedicated Chief of Staff projects/tasks/
checkpoints/watchers and outbound integrations, richer graph/campaign features,
production identity/TLS/backups/monitoring, invoice ceilings, HA/retention, manual
accessibility and live SDK/device validation require separately scoped work.
Filename exclusion does not detect arbitrary secret literals. Owner-retained history
is not retroactively erased by campaign revocation. Snapshot revalidation cannot
recall already sent data. Production live microphone remains disabled until remote
generation/cost authority is enforceable; fake/text/reviewed/recorded input remains.
Next work follows the user's instruction; no additional phase number is invented.
