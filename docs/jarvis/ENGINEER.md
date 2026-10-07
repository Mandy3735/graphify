# Engineer workflow — phase 6

The 0.3.0 backend implements a bounded Graphify-first change workflow. It supports
small source/document changes in ordinary local Git repositories, with offline
system-Python commands. The original repository is not edited or committed by the
workflow. Its output is a reviewed patch and source/test/graph provenance.

## Enable deliberately

Install Linux Bubblewrap, util-linux (`prlimit`, `setpriv`) and system Python 3.
The host must permit the required user/mount/PID/network/IPC/UTS namespaces and
Bubblewrap's `--disable-userns`, read-only mounts and size-limited tmpfs options.
Do not disable security controls merely to make startup pass.

Set trusted server configuration:

```dotenv
JARVIS_ENGINEER_ENABLED=true
JARVIS_ENGINEER_STATE_DIR=/absolute/private/jarvis-engineer-state
JARVIS_CAPABILITIES=["graph.read","graph.write","workspace.read","memory.read","memory.write","memory.propose","engineer.write","engineer.execute"]
```

The state directory must have mode 0700, be owned by the backend service, contain
no symlink components, and be outside every registered project root. No API body,
model response or repository document can select a host workspace or add grants.
Execution remains off in `.env.example`. All changes stay within the application
boundary; migration 0002 remains current and no new schema revision is needed.

At startup, a real subprocess probe checks different PID/network namespaces,
UID 65534, zero effective capabilities, no-new-privileges, a finite process limit,
a minimal environment, and absence of Git metadata. If the probe fails, text and
memory remain available, but no Engineer/command tools are registered. There is
no host execution fallback. An enabled configuration does not establish readiness.

The trusted Bubblewrap launcher establishes namespaces and drops capabilities
before the inner `setpriv --no-new-privs` / `prlimit` wrapper starts Python.
Setting no-new-privileges before Bubblewrap's executable transition can prevent
Ubuntu AppArmor from granting the launcher the namespace setup permissions.
The probe still requires no-new-privileges and zero capabilities in the worker;
no AppArmor policy or host security setting is disabled.

## Workflow and trust boundaries

1. Bind actor, mode, project and run ID to actual server run context; enforce
   capabilities through the existing PolicyEngine before invoking the workflow.
2. Query the registered project's Graphify index before inspecting source. If
   needed, an authorized non-dry run creates the index. A dry run needs an index.
3. Read bounded eligible tracked files with descriptor-relative no-follow IO.
   Record the original HEAD and a digest of the actual source snapshot, including
   any existing tracked working changes. HEAD alone does not describe dirty files.
4. Validate exact expected hashes for existing edit targets. New targets must be
   absent, including dangling symlinks; duplicate, secret and traversal targets
   are rejected. Record the objective, rationale, criteria and prospective diff.
5. Create a private sanitized Git snapshot repository and a real detached Git
   worktree. This intentionally avoids cloning project history, hooks, configs,
   filters, hidden credentials or `.gitattributes` into executable state. Git runs
   are fixed local commands with a constructed environment and hooks/fsmonitor
   disabled. The private snapshot commit differs from the original repository HEAD.
6. Apply validated text edits only in that private worktree. Produce a real Git
   diff, including new files and end-of-file markers. No source apply, merge,
   repository commit, push or deployment is registered.
7. Export a separate plain-file snapshot, excluding `.git`, for executable tests.
   Mount it read-only in Bubblewrap. Runtime libraries are read-only; environment
   is constructed; host home, workspace, sockets and credentials are absent.
8. Run required commands with bounded output and deadlines. A nonzero exit,
   signal, timeout or output overflow fails verification immediately.
9. Update Graphify for the changed worktree, compute impact for edited paths, and
   retain graph/diff hashes and source locations. Missing resolvable graph nodes
   are explicitly reported, rather than invented.
10. Recheck original HEAD and eligible source bytes, check exact changed paths,
    save the bounded artifact, and remove worktree/snapshot intermediates.

The deterministic review verifies scope, hashes, declared command outcomes and
Graphify impact. It does not certify semantic correctness or substitute for a
human security review. Acceptance criteria are declared requirements; command
exit zero alone does not establish that arbitrary prose criteria were satisfied.
Graph evidence, source rationale, commands and output remain untrusted data.

## Resource limits

| Boundary | Enforced limit |
|---|---|
| Source snapshot | At most 1,500 tracked entries, 32 MiB total, 2 MiB/file; supported non-secret text suffixes |
| Proposed edits | 1–4 files, 4,000 characters of replacement text/file, review diff at most 8,000 bytes |
| Commands | 1–3; literal `python3` argv, 16 arguments, 6,000 JSON characters total/command |
| Filesystem | Read-only private root/source/runtime/proc/dev; writable private `/tmp` capped at 16 MiB |
| Memory | Configured per-process address-space cap: 256 MiB default, 64–512 MiB allowed |
| Processes | Per-isolated-user process cap: 24 default, 8–48 allowed; applied after namespace setup |
| CPU/file/descriptors | 5 CPU seconds/process, 4 MiB/file, 64 descriptors, no core dumps |
| Wall/output | 15 seconds and 8 KiB merged output/command by default; hard setting bounds |
| Concurrency/retention | One workflow per service; at most 128 retained jobs, 180,000 bytes/report |

The process/address-space caps are not an aggregate cgroup memory quota. Runtime
mounts expose trusted system binaries/libraries, not application site-packages.
The current worker supports standard-library Python tests such as `unittest`.
Project dependency installation, other language runtimes and network access are
not enabled. Tests requiring unavailable dependencies fail honestly. Linux shares
the host kernel; production kernel hardening and defense in depth remain phase 11.

The whole run retains the existing deadline, context/tool budgets, owner filtering,
cancellation and audit controls. Worker/descendant cleanup uses process-group
termination and Bubblewrap's PID namespace / die-with-parent contracts. Interrupted
runs are not replayed after restart. Operator cleanup is required for orphaned jobs
and retained artifacts; hitting the retention cap refuses new work. No background
purge or multi-worker deployment is claimed.

## API and model tools

All endpoints require the existing bearer authentication.

| Endpoint / tool | Purpose |
|---|---|
| GET `/api/engineer/status` | Configured versus kernel-verified availability |
| POST `/api/engineer/changes` | Start a durable ENGINEER run with a typed change |
| GET `/api/engineer/artifacts/{id}` | Owner-scoped full bounded report |
| GET `/api/engineer/artifacts?run_id={uuid}` | Discover artifacts, including cancellation reports |
| `engineer.change` | Same full workflow through policy and actual-run context |
| `sandbox.run_command`, `sandbox.run_tests` | Offline bounded Python command on an eligible source snapshot |
| `filesystem.read` | Source preview, exact full-read SHA-256 and preview-truncation flag |

`engineer.change` needs engineer.write, engineer.execute, graph.read, graph.write
and workspace.read, including for dry-run proposals. Sandbox tools need
engineer.execute and workspace.read. Tools require ENGINEER mode and the actual
run's project ID. There are no actor/capability/host-path/approval fields in inputs.
Direct authenticated tool requests bind their project to the run server-side.

Example request (replace the hash with `filesystem.read`'s actual SHA-256):

```json
{
  "project_id": "fixture",
  "objective": "Fix core.py addition used by app.py",
  "acceptance_criteria": ["Two plus three returns five", "Configured tests pass"],
  "edits": [{
    "path": "core.py",
    "content": "def add(a, b):\n    return a + b\n",
    "expected_sha256": "REPLACE_WITH_ACTUAL_64_CHARACTER_SHA256",
    "reason": "Replace subtraction with addition"
  }],
  "commands": [{
    "argv": ["python3", "-m", "unittest", "discover", "-v"],
    "purpose": "Fixture regression tests"
  }],
  "dry_run": false
}
```

Dry-run results say `DRY_RUN` and `NOT_RUN`; no edit or command is executed.
`VERIFIED` means the declared command/scope/impact checks succeeded. Failed
verification makes the durable run FAILED, preserving the failure report instead
of letting a model declare success. Cancellation reports say CANCELLED. Source
changes during execution cause failure requiring reconciliation.

Reports bind actor/run/project, source HEAD, snapshot digest, edit hashes, actual
Git diff/hash, command arguments/outcomes/captured-output hashes, Graphify evidence
and impact. Full reports retain bounded captured output; model envelopes use
explicit previews and may omit detail to fit the registry budget. The artifact
SHA-256 hashes the full stored JSON, not the preview. Report files live only in the
private state directory. AgentRun metadata/messages retain the execution envelope;
the existing database/audit records remain authoritative for run status.

## Verification

From apps/jarvis, after normal installation and creation of disposable `_test`
databases, add `JARVIS_TEST_SANDBOX=true` to the existing test commands. Explicit
opt-in means unavailable kernel isolation fails the suite, rather than silently
skipping escape tests. Without opt-in, real-kernel cases skip; validation/dry-run
cases still run. CI installs the Linux runtime and opts in for both database jobs.
Current local results and remote/publication limitations are in JARVIS_PROGRESS.md.
