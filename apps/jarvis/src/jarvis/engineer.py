"""Graph-first engineering in a private snapshot repository and real Git worktree."""

import asyncio
import difflib
import hashlib
import json
import os
import shutil
from pathlib import Path
from uuid import UUID, uuid4

from jarvis.config import Settings
from jarvis.engineer_schema import ChangeRequest, SandboxRequest
from jarvis.graph import GraphifyKnowledgeProvider
from jarvis.paths import TEXT_SUFFIXES, PathDenied, parts, safe_read, safe_write
from jarvis.sandbox import BubblewrapSandbox, capture
from jarvis.tools import ToolExecutionContext


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EngineerFailure(ValueError):
    """Only trusted application-authored explanations belong in a report."""


def public_report(report: dict, artifact_hash: str) -> dict:
    result = {**report, "artifact_sha256": artifact_hash}
    result["commands"] = [
        {
            **command,
            "argv": [arg[:120] for arg in command["argv"]],
            "argv_sha256": digest(json.dumps(command["argv"]).encode()),
            "output": command["output"][:1000],
            "preview_only": True,
        }
        for command in report["commands"]
    ]
    # Full bounded report is owner-readable through the artifact API. The tool
    # envelope must also fit the registry/model context, including Unicode escapes.
    if len(json.dumps(result)) > 20000:
        keep = {
            "artifact_id",
            "run_id",
            "project_id",
            "workflow_status",
            "source_commit",
            "snapshot_sha256",
            "diff_sha256",
            "source_unchanged",
            "dry_run",
            "failure",
            "artifact_sha256",
        }
        result = {key: value for key, value in result.items() if key in keep}
        result["preview_omitted_for_budget"] = True
        result["commands"] = [
            {key: command[key] for key in ("status", "passed", "exit_code", "output_sha256")}
            for command in report["commands"]
        ]
    return result


def git_env() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "JARVIS snapshot",
        "GIT_AUTHOR_EMAIL": "snapshot@localhost",
        "GIT_COMMITTER_NAME": "JARVIS snapshot",
        "GIT_COMMITTER_EMAIL": "snapshot@localhost",
    }


async def git(root: Path, *args: str) -> str:
    # No shell, hooks, filters, external diff, pager, fsmonitor or network operation.
    result = await capture(
        [
            "/usr/bin/git",
            "--no-pager",
            "--no-replace-objects",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.attributesFile=/dev/null",
            "-C",
            str(root),
            *args,
        ],
        env=git_env(),
        deadline=10,
        limit=512 * 1024,
    )
    if not result["passed"]:
        raise EngineerFailure("Bounded local Git operation failed")
    return result["output"]


async def source_manifest(root: Path) -> tuple[str, dict[str, bytes]]:
    if not (root / ".git").is_dir() or (root / ".git").is_symlink():
        raise PathDenied("Engineer projects require an ordinary local Git repository")
    head = (await git(root, "rev-parse", "--verify", "HEAD")).strip()
    paths = (await git(root, "ls-files", "-z")).split("\0")
    if len(paths) > 1501:
        raise EngineerFailure("Tracked file count exceeds Engineer budget")
    files: dict[str, bytes] = {}
    total = 0
    for path in paths:
        if not path:
            continue
        try:
            parts(path)
        except PathDenied:
            continue
        if Path(path).suffix.lower() not in TEXT_SUFFIXES or path.startswith("graphify-out/"):
            continue
        data = safe_read(root, path, limit=2 * 1024 * 1024)
        total += len(data)
        if total > 32 * 1024 * 1024:
            raise EngineerFailure("Source snapshot exceeds Engineer byte budget")
        files[path] = data
    if not files:
        raise EngineerFailure("No eligible tracked source files")
    return head, files


def export_snapshot(root: Path, files: dict[str, bytes]) -> None:
    root.mkdir(mode=0o755)
    for path, data in files.items():
        safe_write(root, path, data)
        # Export contains only validated plain files. Sandbox mounts it read-only.
        target = root / path
        target.chmod(0o444)
        parent = target.parent
        while parent != root:
            parent.chmod(0o755)
            parent = parent.parent


def assert_new_target(root: Path, path: str) -> None:
    from jarvis.paths import parent_fd

    try:
        with parent_fd(root, path) as (fd, name):
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise PathDenied("New file target must not exist")
    except FileNotFoundError:
        pass  # Only private worktree creation will create new parent directories.


def evidence_summary(evidence: dict) -> dict:
    return {
        "trust": "UNTRUSTED_DATA",
        "text": evidence.get("text", "")[:1600],
        "nodes": evidence.get("nodes", [])[:8],
        "edges": evidence.get("edges", [])[:8],
    }


class EngineerService:
    def __init__(self, settings: Settings, graph: GraphifyKnowledgeProvider):
        self.cfg, self.graph = settings, graph
        self.sandbox = BubblewrapSandbox(settings)
        self.lock = asyncio.Lock()  # One workflow owns its subprocesses and staging at a time.
        if settings.engineer_state_dir is None or not settings.engineer_state_dir.is_absolute():
            raise EngineerFailure("Engineer requires an explicit absolute private state directory")
        state = settings.engineer_state_dir
        if state.resolve() != state:
            raise PathDenied("Engineer state directory may not contain symlinks")
        for root in settings.project_roots.values():
            if state.is_relative_to(root) or root.is_relative_to(state):
                raise PathDenied("Engineer state and registered source roots must be disjoint")
        state.mkdir(mode=0o700, parents=True, exist_ok=True)
        if state.stat().st_uid != os.getuid() or state.stat().st_mode & 0o077:
            raise PathDenied("Engineer state must be owned by the service with mode 0700")
        self.state = state

    async def check_backend(self) -> None:
        probe = self.state / f"probe-{uuid4()}"
        probe.mkdir(mode=0o755)
        try:
            await self.sandbox.probe(probe)
        finally:
            probe.rmdir()

    def scope(self, project_id: str, context: ToolExecutionContext) -> Path:
        if context.request.mode.value != "ENGINEER" or not context.run_id:
            raise PathDenied("Actual ENGINEER run context required")
        if context.request.project_id != project_id:
            raise PathDenied("Engineer tools are bound to the run's project")
        return self.graph.root(project_id)

    def artifact(self, artifact_id: str, actor_id: str) -> dict:
        identifier = str(UUID(artifact_id))
        result = json.loads(safe_read(self.state, f"{identifier}/report.json", limit=180000))
        if result["actor_id"] != actor_id:
            raise KeyError("Artifact not found")
        return result

    def artifacts_for_run(self, run_id: str, actor_id: str) -> list[dict]:
        identifier = str(UUID(run_id))
        reports = []
        for job in sorted(self.state.iterdir()):
            try:
                report = self.artifact(job.name, actor_id)
            except (ValueError, FileNotFoundError, KeyError):
                continue
            if report["run_id"] == identifier:
                reports.append(
                    {
                        "artifact_id": report["artifact_id"],
                        "workflow_status": report["workflow_status"],
                    }
                )
        return reports

    def _job(self, context: ToolExecutionContext, project: str) -> tuple[Path, dict]:
        # Fail closed before accumulating unbounded retained artifacts/orphaned jobs.
        if len(list(self.state.iterdir())) >= 128:
            raise EngineerFailure(
                "Engineer artifact retention limit reached; operator cleanup required"
            )
        identifier = str(uuid4())
        job = self.state / identifier
        job.mkdir(mode=0o700)
        return job, {
            "artifact_id": identifier,
            "actor_id": context.actor.id,
            "run_id": context.run_id,
            "project_id": project,
            "workflow_status": "FAILED",
            "commands": [],
        }

    def _save(self, job: Path, report: dict) -> dict:
        body = json.dumps(report, sort_keys=True, ensure_ascii=True).encode()
        if len(body) > 180000:
            raise EngineerFailure("Artifact exceeds retention budget")
        safe_write(job, "report.json", body)
        return public_report(report, digest(body))

    async def change(self, request: ChangeRequest, context: ToolExecutionContext) -> dict:
        root = self.scope(request.project_id, context)
        async with self.lock:
            job, report = self._job(context, request.project_id)
            try:
                # Query the original graph before targeted source inspection.
                if not self.graph.health(request.project_id)["indexed"]:
                    if request.dry_run:
                        raise EngineerFailure("Dry run requires an existing Graphify index")
                    await self.graph.update_project(request.project_id)
                report["evidence"] = evidence_summary(
                    self.graph.query(request.project_id, request.objective, 300)
                )
                head, sources = await source_manifest(root)
                report["source_commit"] = head
                report["snapshot_sha256"] = digest(
                    json.dumps({p: digest(b) for p, b in sources.items()}, sort_keys=True).encode()
                )
                if len({edit.path for edit in request.edits}) != len(request.edits):
                    raise EngineerFailure("Duplicate edit paths rejected")
                proposed = dict(sources)
                plan, patch = [], ""
                for edit in request.edits:
                    old = sources.get(edit.path)
                    if old is None:
                        if edit.expected_sha256 is not None or (root / edit.path).exists():
                            raise EngineerFailure("New file must be absent with no expected hash")
                        assert_new_target(root, edit.path)
                        old = b""
                    elif edit.expected_sha256 != digest(old):
                        raise EngineerFailure("Expected source hash does not match snapshot")
                    new = edit.content.encode()
                    old_text = old.decode("utf-8")
                    proposed[edit.path] = new
                    patch += "".join(
                        difflib.unified_diff(
                            old_text.splitlines(True),
                            edit.content.splitlines(True),
                            fromfile=f"a/{edit.path}",
                            tofile=f"b/{edit.path}",
                        )
                    )
                    plan.append(
                        {
                            "path": edit.path,
                            "reason": edit.reason,
                            "before_sha256": digest(old),
                            "after_sha256": digest(new),
                        }
                    )
                if len(patch.encode()) > 8000:
                    raise EngineerFailure("Patch exceeds review budget")
                report.update(
                    objective=request.objective,
                    plan=plan,
                    acceptance_criteria=request.acceptance_criteria,
                    diff=patch,
                    diff_sha256=digest(patch.encode()),
                    dry_run=request.dry_run,
                )
                if request.dry_run:
                    report.update(
                        workflow_status="DRY_RUN",
                        tests="NOT_RUN",
                        review="Proposed diff only; no edits or execution",
                    )
                    return self._save(job, report)
                if not self.sandbox.ready:
                    raise EngineerFailure("Verified OS sandbox required before edits or execution")
                # A sanitized snapshot repository avoids project hooks/config/filter execution.
                control = job / "control"
                export_snapshot(control, sources)
                await git(control, "init", "--quiet")
                await git(control, "add", "--all")
                await git(control, "commit", "--quiet", "-m", "Authorized source snapshot")
                worktree = job / "worktree"
                await git(control, "worktree", "add", "--quiet", "--detach", str(worktree), "HEAD")
                report["worktree_baseline"] = (await git(control, "rev-parse", "HEAD")).strip()
                for edit in request.edits:
                    safe_write(worktree, edit.path, edit.content.encode())
                    if edit.path not in sources:
                        await git(worktree, "add", "--intent-to-add", "--", edit.path)
                actual_patch = await git(worktree, "diff", "--no-ext-diff", "--no-textconv")
                if len(actual_patch.encode()) > 8000:
                    raise EngineerFailure("Git diff exceeds review budget")
                report["diff"] = actual_patch
                report["diff_sha256"] = digest(actual_patch.encode())
                # Git metadata never enters executable test snapshots.
                execution = job / "execution"
                export_snapshot(execution, proposed)
                for command in request.commands:
                    result = await self.sandbox.run(execution, command)
                    report["commands"].append(result)
                    if not result["passed"]:
                        report["failure"] = "A required command failed or exceeded its budget"
                        return self._save(job, report)
                updated = GraphifyKnowledgeProvider({"change": worktree}, self.graph.timeout)
                report["graph_after"] = await updated.update_project("change")
                report["graph_sha256"] = digest(
                    safe_read(worktree, "graphify-out/graph.json", limit=32 * 1024 * 1024)
                )
                report["impact"] = []
                for edit in request.edits:
                    try:
                        impact = updated.impact("change", edit.path)
                        report["impact"].append(
                            {
                                "path": edit.path,
                                "affected_count": impact["affected_count"],
                                "nodes": impact["nodes"][:4],
                            }
                        )
                    except ValueError:
                        report["impact"].append(
                            {"path": edit.path, "status": "NO_RESOLVABLE_GRAPH_NODE"}
                        )
                current_head, current_sources = await source_manifest(root)
                if current_head != head or current_sources != sources:
                    raise EngineerFailure(
                        "Source changed during workflow; result needs reconciliation"
                    )
                names = await git(worktree, "diff", "--name-only", "-z", "--no-ext-diff")
                names += await git(worktree, "ls-files", "--others", "--exclude-standard", "-z")
                actual = {p for p in names.split("\0") if p and not p.startswith("graphify-out/")}
                if actual != {edit.path for edit in request.edits}:
                    raise EngineerFailure("Worktree diff does not match proposed paths")
                report.update(
                    workflow_status="VERIFIED",
                    source_unchanged=True,
                    review="Exact scoped diff, source hashes, bounded commands and impact checked; "
                    "semantic correctness and security still require human review",
                )
                return self._save(job, report)
            except asyncio.CancelledError:
                report.update(workflow_status="CANCELLED", failure="Human or deadline cancellation")
                self._save(job, report)
                raise
            except Exception as exc:
                # No raw OS/Git/provider errors or host paths enter user/model output.
                report["failure"] = (
                    str(exc) if isinstance(exc, EngineerFailure) else type(exc).__name__
                )
                return self._save(job, report)
            finally:
                for name in ["control", "worktree", "execution"]:
                    shutil.rmtree(job / name, ignore_errors=True)

    async def run_command(self, request: SandboxRequest, context: ToolExecutionContext) -> dict:
        root = self.scope(request.project_id, context)
        async with self.lock:
            job, report = self._job(context, request.project_id)
            try:
                head, sources = await source_manifest(root)
                report["source_commit"] = head
                execution = job / "execution"
                export_snapshot(execution, sources)
                result = await self.sandbox.run(execution, request.command)
                report["commands"] = [result]
                report["workflow_status"] = "VERIFIED" if result["passed"] else "FAILED"
                return self._save(job, report)
            except asyncio.CancelledError:
                report["workflow_status"] = "CANCELLED"
                self._save(job, report)
                raise
            except Exception as exc:
                report["failure"] = (
                    str(exc) if isinstance(exc, EngineerFailure) else type(exc).__name__
                )
                return self._save(job, report)
            finally:
                shutil.rmtree(job / "execution", ignore_errors=True)
