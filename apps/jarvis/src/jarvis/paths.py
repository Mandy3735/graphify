"""Bounded descriptor-relative IO. Fail closed on platforms without no-follow support."""

import os
import secrets
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

BLOCKED = {"id_rsa", "id_ed25519", "credentials", "secrets", "secrets.json"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ts", ".js"}


class PathDenied(ValueError):
    pass


def parts(path: str, *, internal: bool = False) -> tuple[str, ...]:
    if (
        not path
        or "\\" in path
        or ":" in path
        or "\x00" in path
        or PurePosixPath(path).is_absolute()
    ):
        raise PathDenied("Relative workspace path required")
    segments = tuple(path.split("/"))
    if any(p in {"", ".", ".."} for p in segments):
        raise PathDenied("Traversal or empty path component rejected")
    if not internal and any(p.startswith(".") or p.lower() in BLOCKED for p in segments):
        raise PathDenied("Sensitive or hidden path rejected")
    if not internal and any(p.lower().endswith((".pem", ".key", ".p12")) for p in segments):
        raise PathDenied("Credential file rejected")
    return segments


@contextmanager
def parent_fd(root: Path, path: str, *, internal: bool = False, create: bool = False):
    segments = parts(path, internal=internal)
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise PathDenied("Secure descriptor-relative filesystem access requires POSIX")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in segments[:-1]:
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd, segments[-1]
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise PathDenied("Unsafe or unavailable workspace path") from exc
    finally:
        os.close(fd)


def safe_read(root: Path, path: str, *, limit: int = 65536, internal: bool = False) -> bytes:
    import stat

    with parent_fd(root, path, internal=internal) as (directory, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit or info.st_nlink != 1:
                raise PathDenied("File is not regular or exceeds byte limit")
            data = stream.read(limit + 1)
            if len(data) > limit:
                raise PathDenied("File exceeds byte limit")
            return data


def safe_write(root: Path, path: str, data: bytes) -> None:
    # Atomic same-directory rename with trusted descriptor; no symlink following.
    with parent_fd(root, path, internal=True, create=True) as (directory, name):
        temporary = f"jarvis-tmp-{secrets.token_hex(12)}"
        fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.rename(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
