# Phase 11 engineering report — 2026-10-14

Phase 11 hardens the delivered Graphify → JARVIS prototype. Repository
`/workspace/graphify`, local branch `jarvis/phase-11-hardening`, receiving published
Phase 10 commit `8aa688a450a4633f55ec677947f3393ee35774d0`. Resolve the final local
commit with `git rev-parse HEAD`. No Phase 11 push, merge, deployment, certificate
issuance or paid model call occurred. My-JARVIS-AI- was not changed.

## Delivered behavior and boundaries

Application **0.8.0** adds bounded HTTP admission before parsing/audits/SQL/provider
work; production exact-origin/HTTPS/strong-bearer/restricted-DB checks; one-process
PostgreSQL lease before recovery, unhealthy-on-loss and reliable cleanup; durable
UTC provider reservations/usage estimates; saved voice call/creation identifiers,
background stop recovery and explicit human reconciliation. Production exception
responses/logging omit private parameters. Authenticated /api/usage and Settings
expose estimates/current-actor call summaries. CI adds read-only permissions,
concurrency control, psql, Bandit medium/high and dependency audits. Reviewed role
SQL and validated/formatted Caddy TLS template make deployment configuration concrete.

Additive migration **0005** stores provider day/call and voice cleanup rows; previous
migrations 0001–0004 remain byte-for-byte unchanged. Role setup runs as an operator,
not application startup. One worker is enforced rather than claiming distributed HA.
Live calls require actual configured model prices or fixed bounded-operation estimates;
missing estimates fail before SDK calls, uncertain attempts remain charged across
restarts, settlement is one-use and unexpected usage is recorded/withheld before tools.
Estimated admission is not an upstream invoice guarantee. Production live microphone
is unavailable because client data-channel generation settings cannot enforce a
backend cost ceiling. Local preview/live-with-estimates, text, reviewed input and
bounded configured speech/transcription remain. No permanent mic/camera monitoring.

No model tool, grant, approval relaxation, canonical mutation route or visibility
change was introduced. Exact approvals, human Tutor evidence, human-default PC rolls,
Game Master secrecy and memory ownership remain authoritative. All existing kernel
isolation/security tests still run. Two source-scan B108 annotations explain private
Bubblewrap tmpfs literals without changing isolation or disabling the rule globally.
Graphify core, CLI/MCP, source/tests/fixtures/root metadata/uv.lock/licenses/generated
skills and original upstream CI remain unchanged. The JARVIS-specific workflow changes.

New files: budgets.py, ingress.py, runtime.py; migration 0005_hardening.py;
test_hardening.py; deploy/runtime-role.sql and deploy/Caddyfile; HARDENING.md,
this report and phase11 verification artifacts. Substantial changes extend existing
configuration/API/lifespan, model/embedding SDK guards, voice lifecycle/journal,
DB models, static headers, UI Settings/voice/error display, PG/device tests and CI.
Application metadata is versioned; locks retain dependency selections. Architecture,
setup, threat model, review, progress, handoff, next prompt and root links are updated.

## Actual checks

| Check | Observed result |
|---|---|
| Receiving Phase 10 | 163 backend passed, 29 DB/kernel skips; lint/format/types; 33 frontend tests/build/types passed |
| Final PostgreSQL + real isolation | **217 passed, 1 skipped** (47.53 s); all 13 real kernel tests ran |
| Final PostgreSQL/pgvector + real isolation | **217 passed, 1 skipped** (47.35 s); all 13 real kernel tests ran |
| Targeted hardening/voice | **35 passed** (5.68 s) |
| Frontend components/device/cache/security | **35 passed** |
| Production Chromium | **5 passed** (15.4 s), including voice, text, Tutor, GM secrecy, memory and mobile axe |
| JARVIS Ruff lint/format/Pyright | Passed; zero type errors/warnings |
| Frontend TypeScript/ESLint/Prettier/build | Passed |
| Python dependency audit / npm audit | Zero known/reported vulnerabilities |
| Bandit medium/high | Zero; nine low reviewed findings; two narrow private-tmpfs annotations |
| Wheel/sdist | 0.8.0 built; hardening modules/UI in wheel; migration/deploy templates in sdist |
| Caddy adaptation/validation | Passed offline; formatting applied; no deployment/certificate issued |
| Upstream Graphify suite | 6,470 passed, 108 skipped, 9 baseline failure identifiers (160.66 s) |
| Upstream Ruff lint | Passed |
| Upstream formatter | Existing drift: 413 would reformat, 159 formatted using explicit graphify/tests paths |
| Upstream Pyright | Existing issues/dependencies: 618 errors, 4 warnings using explicit interpreter |
| Relevant upstream docs | 38 passed, 1 warning (0.38 s) |
| Graph update/navigation | 20,004 nodes, 42,350 edges, 1,054 communities; scoped query/explain succeeded |

Final PG suites run with JARVIS_TEST_SANDBOX=true and separate disposable databases.
Migration upgrade/downgrade/upgrade, metadata parity, exact approval/races, persistence,
GM/Tutor/memory, budget race/restart/settlement, second-process/lost-lease rejection and
real restricted-role smoke pass. The real role script allows fake runs/audit inserts
and denies audit rewrite/deletion/truncation, DDL and migration-table writes. No
sandbox/security check was weakened or skipped to avoid a host restriction.

The unchanged root still has ignore-without-VCS, no-Git hooks and seven DNS-dependent
URL/fetch failures; identifiers are in phase11-verification.json. Root formatter/type
issues are separate from application checks. Explicit paths/interpreter and available
optional dependencies differ from the original baseline's 430-format/639-type counts;
source preservation was verified. No root-wide formatting/refactor was attempted.

Initial checks caught voice input-validation ordering, test formatting/import mistakes
and a read-only pip-audit home cache. Ordering was fixed, fixtures corrected and a
workspace cache used. Bandit initially flagged the worker's private /tmp mount/home;
narrow annotations document the actual kernel boundary, tested by all 13 probes.
Later review fixed unhealthy lease reporting on /health and unconditional voice-SDK
closure when journaling fails; affected complete suites were rerun successfully.
Raw receiving/intermediate/final logs are in ignored work/phase11. Portable measured
outputs and scan JSON are in docs/jarvis/verification/phase11-*.

## Exact principal commands

From repository root (runtime skill/network/proxy policy inspected before network work):

```sh
git status --short
git branch --show-current
git log -3 --oneline
git switch -c jarvis/phase-11-hardening
.venv/bin/graphify query 'Engine ModelRouter VoiceService Database recover close' --budget 1500
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock info --format '{{.ServerVersion}}'
docker --host=unix:///var/run/docker.sock run -d --name jarvis-phase11-db -p 127.0.0.1:55432:5432 -e POSTGRES_USER=jarvis -e POSTGRES_PASSWORD=jarvis-test-only -e POSTGRES_DB=jarvis_test pgvector/pgvector:pg17
docker --host=unix:///var/run/docker.sock exec jarvis-phase11-db psql -U jarvis -d jarvis_test -c 'CREATE DATABASE jarvis_vector_test;'
.venv/bin/bandit -r apps/jarvis/src -ll
.venv/bin/pip-audit --disable-pip --no-deps --cache-dir /workspace/.cache/pip-audit -r apps/jarvis/requirements.lock --format json
PATH=/workspace/graphify/.venv/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/ -q
.venv/bin/ruff check graphify tests
.venv/bin/ruff format --check graphify tests
.venv/bin/pyright --pythonpath .venv/bin/python
.venv/bin/python -m pytest tests/test_architecture_doc.py -q
.venv/bin/python -m build --no-isolation apps/jarvis
.venv/bin/graphify update .
.venv/bin/graphify query 'RuntimeGuard ProviderBudget Ingress' --budget 900
.venv/bin/graphify explain 'apps/jarvis/src/jarvis/budgets.py::ProviderBudget'
git diff --exit-code 8aa688a -- graphify tests pyproject.toml uv.lock LICENSE LICENSE-MIT NOTICE
git diff --check
```

Offline proxy validation uses the public template only:

```sh
docker --host=unix:///var/run/docker.sock run --rm --network none -e JARVIS_PUBLIC_HOST=jarvis.example -v /workspace/graphify/apps/jarvis/deploy/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2.10-alpine caddy adapt --config /etc/caddy/Caddyfile --validate
```

From apps/jarvis:

```sh
../../.venv/bin/python -m pytest -q
../../.venv/bin/python -m pytest tests/test_hardening.py tests/test_voice.py -q
JARVIS_TEST_PSQL=/tmp/jarvis-phase11-psql JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-test-only@127.0.0.1:55432/jarvis_test ../../.venv/bin/python -m pytest tests/test_postgres.py -q
JARVIS_TEST_PSQL=/tmp/jarvis-phase11-psql JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-test-only@127.0.0.1:55432/jarvis_test JARVIS_TEST_SANDBOX=true ../../.venv/bin/python -m pytest -q
JARVIS_TEST_PSQL=/tmp/jarvis-phase11-psql JARVIS_TEST_DATABASE_URL=postgresql+asyncpg://jarvis:jarvis-test-only@127.0.0.1:55432/jarvis_vector_test JARVIS_TEST_PGVECTOR=true JARVIS_TEST_SANDBOX=true ../../.venv/bin/python -m pytest -q
../../.venv/bin/ruff check .
../../.venv/bin/ruff format --check .
../../.venv/bin/pyright
```

The session's trusted psql wrapper maps the disposable container's host port to
internal 5432 and invokes its installed psql with test-only PGPASSWORD. CI uses its
installed native psql; no Docker-specific test implementation replaces the real SQL.
These are synthetic test credentials, not operational secrets. No actual secrets
were printed/discovered. Source formatting was limited to the JARVIS application.

From apps/jarvis/frontend:

```sh
npm run check
npm run format:check
npm run build
npm run test
npm audit --audit-level=high
JARVIS_CHROMIUM=/usr/bin/chromium npm run e2e
```

Python scripts checked wheel/sdist membership, preserved-source/migration parity,
copied measured outputs and updated documents. Root tool results remain recorded;
JARVIS checks passed. The existing environment/dependency locks were reused and
no paid provider or external-write integration was called.

## Scope, demos and next milestone

Phases 0–11 are complete within their explicit prototype bounds. Full Phase 12 hostile
review, deferred Chief of Staff workflows/integrations, rich campaign/graph features,
manual device/live SDK testing, operational identity/TLS/backups/monitoring and
provider billing/HA/retention still require work. The master definition of done is not
complete. This task supplies configuration templates and tested single-principal
runtime controls; it does not claim a deployed production personal operating system.

Model choice remains configuration-driven: fake/OpenAI reasoning/fallback/utility
and independently configured embeddings/voice/transcription/speech. Fake mode needs
no key or prices. Live calls need configured prices/estimates; the production profile
keeps live microphone off pending a verifiable provider-side cost authority. Schema
0005 and restricted-role/TLS setup instructions are in HARDENING.md.

Existing DEMO A Code Intelligence, B bounded Engineer, C Chief of Staff text/memory
and fake exact-approval subset, D Tutor and E Game Master remain in LOCAL_DEVELOPMENT.md.
For hardening, inspect Settings/provider estimates, submit a fake run, review the real
role/lease/quota tests and optional fake voice preview in VOICE.md. These demos do not
claim dedicated Chief of Staff projects/checkpoints/watchers were implemented.
Next recommended task: Phase 12 adversarial review using CODEX_NEXT_PROMPT.md.
