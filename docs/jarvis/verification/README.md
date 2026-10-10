# Recorded foundation verification

These are snapshots from the foundation implementation session, not a promise
about a receiving machine. See JARVIS_PROGRESS.md and UPSTREAM_BASELINE.md for
commands, dependency differences, and environment restrictions.

- `foundation-tests.txt`: final application suite, including local PostgreSQL.
- `upstream-failure-comparison.json`: complete baseline and regression failure
  identifiers. `new_failures` is empty; nine failures remain in regression.

Re-run appropriate checks when continuing implementation. The delivery manifest
records the source checkpoint associated with this snapshot.

## Phase 5 checkpoint

- `phase5-postgres-tests.txt`: 106 passed, one optional-vector skip.
- `phase5-pgvector-tests.txt`: 106 passed, one missing-extension skip.
- `phase5-upstream-comparison.json`: the same nine foundation failure identifiers;
  no new upstream failures (6,470 passed, 108 skipped).
- `phase5-http-smoke.json`: real migrated PostgreSQL/pgvector and loopback HTTP
  memory/provenance/correction/deletion workflow with fake providers.

These snapshots are associated with the phase-5 source checkpoint in its delivery
manifest. No remote CI or paid live-model result is claimed.

## Phase 6 local checkpoint

- `phase6-postgres-tests.txt` and `phase6-pgvector-tests.txt`: each 137 passes and
  one opposite-configuration skip, with real Bubblewrap tests explicitly enabled.
- `phase6-upstream-comparison.json`: 6,472 passes, 108 skips, seven pre-existing
  DNS failures; restricted-run differences and empty new-failure set recorded.
- `phase6-http-smoke.json`: real migrated loopback Engineer workflow, kernel
  readiness, source preservation and authenticated artifact retrieval.

These snapshots record local verification. The Phase 6 branch was subsequently
pushed with user authorization; inspect GitHub Actions for remote results.
No merge, deployment or paid provider claim.
The private delivery manifest and Git HEAD identify the exact local checkpoint.

## Phase 7 local checkpoint

- `phase7-postgres-tests.txt` and `phase7-pgvector-tests.txt`: each 152 passes and
  one opposite-configuration skip, with real Bubblewrap tests explicitly enabled.
- `phase7-http-smoke.json`: authenticated Tutor workflow on a freshly migrated
  PostgreSQL database, including evidence-backed mastery and the model boundary.
- `phase7-upstream-comparison.json`: relevant architecture regression and exact
  preserved-path comparison. A full upstream rerun was not repeated because Phase 7
  does not change the upstream surface; the Phase 6 full regression remains the
  latest full reference.

The local Phase 7 branch was not pushed, merged or deployed. Graphify update and
scoped TutorService navigation succeeded; full scratch logs remain in `work/`.
