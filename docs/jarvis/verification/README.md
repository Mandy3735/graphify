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

Phase 6 is not pushed, merged or deployed; no remote CI or paid provider claim.
The private delivery manifest and Git HEAD identify the exact local checkpoint.
