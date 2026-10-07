"""Linux Bubblewrap isolation. No shell, host fallback, or inherited environment."""

import asyncio
import hashlib
import json
import os
import signal
import time
from pathlib import Path

from jarvis.config import Settings
from jarvis.engineer_schema import Command


class SandboxUnavailable(ValueError):
    pass


async def capture(
    argv: list[str], *, env: dict[str, str], deadline: float, limit: int, cwd: Path | None = None
) -> dict:
    """Drain bounded merged output; kill the entire session on every interrupted path."""
    started = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True,
    )
    output = bytearray()
    status = "EXITED"
    try:
        async with asyncio.timeout(deadline):
            assert process.stdout is not None
            while block := await process.stdout.read(min(4096, limit + 1)):
                output.extend(block)
                if len(output) > limit:
                    status = "OUTPUT_LIMIT"
                    break
            if status == "EXITED":
                await process.wait()
    except TimeoutError:
        status = "TIMEOUT"
    finally:
        # Even an exited leader can leave grandchildren holding the output pipe.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.wait()
    data = bytes(output[:limit])
    return {
        "status": status,
        "exit_code": process.returncode,
        "output": data.decode(errors="replace"),
        "output_sha256": hashlib.sha256(data).hexdigest(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "passed": status == "EXITED" and process.returncode == 0,
    }


class BubblewrapSandbox:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ready = False

    def argv(self, source: Path, command: Command) -> list[str]:
        required = [
            "/usr/bin/bwrap",
            "/usr/bin/prlimit",
            "/usr/bin/setpriv",
            "/usr/bin/python3",
            "/usr/bin",
            "/usr/lib",
            "/lib",
        ]
        if not all(Path(p).exists() for p in required):
            raise SandboxUnavailable("Bubblewrap, prlimit, setpriv and system Python are required")
        cfg = self.settings
        argv = [
            "/usr/bin/prlimit",
            f"--as={cfg.sandbox_memory_mb * 1024 * 1024}",
            "--cpu=5",
            "--fsize=4194304",
            "--nofile=64",
            "--core=0",
            "--",
            "/usr/bin/bwrap",
            "--unshare-all",
            "--unshare-user",
            "--disable-userns",
            "--die-with-parent",
            "--new-session",
            "--uid",
            "65534",
            "--gid",
            "65534",
            "--cap-drop",
            "ALL",
        ]
        for runtime in ["/usr/bin", "/usr/lib", "/lib", "/lib64"]:
            if Path(runtime).exists():
                argv.extend(["--ro-bind", runtime, runtime])
        argv.extend(
            [
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--size",
                "16777216",
                "--tmpfs",
                "/tmp",
                "--ro-bind",
                str(source),
                "/workspace",
                "--chdir",
                "/workspace",
                "--remount-ro",
                "/",
                "--remount-ro",
                "/dev",
                "--remount-ro",
                "/proc",
                "--clearenv",
                "--setenv",
                "PATH",
                "/usr/bin",
                "--setenv",
                "LANG",
                "C.UTF-8",
                "--setenv",
                "HOME",
                "/tmp",
                "--setenv",
                "PYTHONDONTWRITEBYTECODE",
                "1",
                "--setenv",
                "PYTHONHASHSEED",
                "0",
                "--",
                # Let the trusted launcher enter its AppArmor profile before
                # making no-new-privileges irreversible for the worker.
                "/usr/bin/setpriv",
                "--no-new-privs",
                "/usr/bin/prlimit",
                f"--nproc={cfg.sandbox_processes}",
                "--",
                "/usr/bin/python3",
                *command.argv[1:],
            ]
        )
        return argv

    async def _run(self, source: Path, command: Command) -> dict:
        return await capture(
            self.argv(source, command),
            env={"LANG": "C.UTF-8"},
            deadline=self.settings.sandbox_timeout,
            limit=self.settings.sandbox_output_bytes,
        )

    async def probe(self, source: Path) -> None:
        # A real kernel probe, not merely detection of an installed executable.
        code = (
            "import os,json,resource; "
            "s=dict(l.split(':',1) for l in open('/proc/self/status') if ':' in l); "
            "print(json.dumps({'uid':os.getuid(),'caps':int(s['CapEff'],16),"
            "'nnp':int(s['NoNewPrivs']),'host_visible':os.path.exists('/workspace/.git'),"
            "'env':sorted(os.environ),'nproc':resource.getrlimit(resource.RLIMIT_NPROC)[1],"
            "'net':os.readlink('/proc/self/ns/net'),'pid':os.readlink('/proc/self/ns/pid')}))"
        )
        try:
            result = await self._run(
                source, Command(argv=["python3", "-c", code], purpose="Verify kernel isolation")
            )
            evidence = json.loads(result["output"])
            if (
                not result["passed"]
                or evidence["uid"] != 65534
                or evidence["caps"] != 0
                or evidence["nnp"] != 1
                or evidence["host_visible"]
                or evidence["nproc"] != self.settings.sandbox_processes
                or evidence["net"] == os.readlink("/proc/self/ns/net")
                or evidence["pid"] == os.readlink("/proc/self/ns/pid")
                or not set(evidence["env"])
                <= {
                    "PATH",
                    "LANG",
                    "HOME",
                    "PWD",
                    "PYTHONDONTWRITEBYTECODE",
                    "PYTHONHASHSEED",
                    "LC_CTYPE",
                }
            ):
                raise SandboxUnavailable("Kernel isolation probe failed")
        except (OSError, ValueError, KeyError) as exc:
            raise SandboxUnavailable("Kernel isolation unavailable; execution disabled") from exc
        self.ready = True

    async def run(self, source: Path, command: Command) -> dict:
        if not self.ready:
            raise SandboxUnavailable("Verified OS sandbox required; no host execution fallback")
        result = await self._run(source, command)
        return {
            "argv": command.argv,
            "purpose": command.purpose,
            **result,
            "isolation": "bubblewrap:user,mount,pid,network,ipc,uts;no-new-privileges",
        }
