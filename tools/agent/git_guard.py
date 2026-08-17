"""Git scope snapshots and cooperative one-writer ownership for QAP worktrees."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast


class GitGuardError(RuntimeError):
    """Raised when repository changes exceed the reviewed implementation scope."""


class WriterOwnershipError(GitGuardError):
    """Raised when another live writer owns the same Git worktree."""


@dataclass(frozen=True, slots=True)
class GitPathState:
    path: str
    status: str
    content_fingerprint: str

    @property
    def deleted(self) -> bool:
        return "D" in self.status


@dataclass(frozen=True, slots=True)
class GitSnapshot:
    worktree_path: Path
    branch: str
    head: str
    status_porcelain: str
    status_fingerprint: str
    paths: tuple[GitPathState, ...]

    @property
    def changed_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.paths)


@dataclass(frozen=True, slots=True)
class WriterLease:
    writer_id: str
    owner_pid: int
    worktree_path: str
    branch: str
    head: str
    acquired_at: str
    note: str | None = None


def _git(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise GitGuardError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.rstrip("\n")


def _path_from_porcelain(line: str) -> tuple[str, str]:
    if len(line) < 4:
        raise GitGuardError(f"unexpected git status entry: {line!r}")
    status = line[:2]
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return status, path


def _path_fingerprint(worktree: Path, relative_path: str, status: str) -> str:
    path = worktree / relative_path
    digest = hashlib.sha256(b"QAP-GIT-PATH\x00")
    digest.update(status.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(relative_path.encode("utf-8"))
    digest.update(b"\x00")
    if path.is_symlink():
        digest.update(b"symlink\x00")
        digest.update(os.readlink(path).encode("utf-8"))
    elif path.is_file():
        digest.update(b"file\x00")
        digest.update(path.read_bytes())
    elif path.exists():
        digest.update(b"other\x00")
    else:
        digest.update(b"absent\x00")
    return digest.hexdigest()


def snapshot_git(repository_root: str | Path) -> GitSnapshot:
    """Capture canonical worktree identity and exact current dirty-path fingerprints."""

    requested = Path(repository_root).resolve()
    worktree = Path(_git(requested, "rev-parse", "--show-toplevel")).resolve()
    head = _git(worktree, "rev-parse", "HEAD")
    branch = _git(worktree, "branch", "--show-current") or "(detached)"
    status = _git(
        worktree,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    entries: list[GitPathState] = []
    for line in status.splitlines():
        if not line:
            continue
        path_status, relative_path = _path_from_porcelain(line)
        entries.append(
            GitPathState(
                path=relative_path,
                status=path_status,
                content_fingerprint=_path_fingerprint(
                    worktree, relative_path, path_status
                ),
            )
        )
    entries.sort(key=lambda item: item.path)
    status_fingerprint = hashlib.sha256(status.encode("utf-8")).hexdigest()
    return GitSnapshot(
        worktree_path=worktree,
        branch=branch,
        head=head,
        status_porcelain=status,
        status_fingerprint=status_fingerprint,
        paths=tuple(entries),
    )


def assert_safe_scope(
    *,
    baseline: GitSnapshot,
    current: GitSnapshot,
    allowed_paths: set[str] | frozenset[str],
    allowed_deletions: set[str] | frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    """Return planned changed paths or fail if current mutations escape the baseline."""

    if baseline.worktree_path != current.worktree_path:
        raise GitGuardError("Git snapshots refer to different worktrees")
    allowed = frozenset(allowed_paths)
    deletions = frozenset(allowed_deletions)
    before = {item.path: item for item in baseline.paths}
    after = {item.path: item for item in current.paths}

    for path, prior in before.items():
        observed = after.get(path)
        if observed is None:
            if path not in allowed:
                raise GitGuardError(f"pre-existing dirty path changed: {path}")
            continue
        changed = (
            observed.status != prior.status
            or observed.content_fingerprint != prior.content_fingerprint
        )
        if changed and path not in allowed:
            raise GitGuardError(f"pre-existing dirty path changed: {path}")

    planned: list[str] = []
    for path, observed in after.items():
        prior = before.get(path)
        changed = prior is None or (
            observed.status != prior.status
            or observed.content_fingerprint != prior.content_fingerprint
        )
        if not changed:
            continue
        if path not in allowed:
            raise GitGuardError(f"unexpected changed path: {path}")
        if observed.deleted and path not in deletions:
            raise GitGuardError(f"unexpected deletion: {path}")
        planned.append(path)

    for path, prior in before.items():
        if path in after:
            continue
        if path in allowed:
            planned.append(path)
        elif prior.path not in allowed:
            raise GitGuardError(f"pre-existing dirty path changed: {path}")
    return tuple(sorted(set(planned)))


def _lease_path(repository_root: Path) -> Path:
    return repository_root.resolve() / ".qap-agent" / "worktree-writer.json"


def _lease_from_object(value: object) -> WriterLease:
    if not isinstance(value, dict):
        raise WriterOwnershipError("writer lease is corrupt")
    raw = cast(dict[str, object], value)
    writer_id = raw.get("writer_id")
    owner_pid = raw.get("owner_pid")
    worktree_path = raw.get("worktree_path")
    branch = raw.get("branch")
    head = raw.get("head")
    acquired_at = raw.get("acquired_at")
    note = raw.get("note")
    if not isinstance(writer_id, str) or not writer_id:
        raise WriterOwnershipError("writer lease has invalid writer_id")
    if not isinstance(owner_pid, int) or isinstance(owner_pid, bool) or owner_pid <= 0:
        raise WriterOwnershipError("writer lease has invalid owner_pid")
    git_identity = (worktree_path, branch, head)
    if not all(isinstance(item, str) and item for item in git_identity):
        raise WriterOwnershipError("writer lease has invalid Git identity")
    if not isinstance(acquired_at, str) or not acquired_at:
        raise WriterOwnershipError("writer lease has invalid acquisition time")
    if note is not None and not isinstance(note, str):
        raise WriterOwnershipError("writer lease has invalid note")
    return WriterLease(
        writer_id=writer_id,
        owner_pid=owner_pid,
        worktree_path=cast(str, worktree_path),
        branch=cast(str, branch),
        head=cast(str, head),
        acquired_at=acquired_at,
        note=note,
    )


def inspect_writer(repository_root: str | Path) -> WriterLease | None:
    """Inspect current writer ownership without mutating the lease."""

    path = _lease_path(Path(repository_root))
    if not path.is_file():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WriterOwnershipError("writer lease is corrupt") from exc
    return _lease_from_object(raw)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _write_lease(path: Path, lease: WriterLease) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".worktree-writer.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "writer_id": lease.writer_id,
                    "owner_pid": lease.owner_pid,
                    "worktree_path": lease.worktree_path,
                    "branch": lease.branch,
                    "head": lease.head,
                    "acquired_at": lease.acquired_at,
                    "note": lease.note,
                },
                handle,
                sort_keys=True,
                indent=2,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def acquire_writer(
    *,
    repository_root: str | Path,
    writer_id: str,
    owner_pid: int,
    note: str | None = None,
) -> WriterLease:
    """Acquire/refresh cooperative ownership when no different live writer exists."""

    if not writer_id:
        raise ValueError("writer_id must be non-empty")
    if isinstance(owner_pid, bool) or owner_pid <= 0:
        raise ValueError("owner_pid must be positive")
    root = Path(repository_root).resolve()
    current = inspect_writer(root)
    if (
        current is not None
        and current.writer_id != writer_id
        and _pid_alive(current.owner_pid)
    ):
        raise WriterOwnershipError(
            f"worktree is owned by live writer {current.writer_id} "
            f"(pid {current.owner_pid})"
        )
    snapshot = snapshot_git(root)
    lease = WriterLease(
        writer_id=writer_id,
        owner_pid=owner_pid,
        worktree_path=str(snapshot.worktree_path),
        branch=snapshot.branch,
        head=snapshot.head,
        acquired_at=datetime.now(UTC).isoformat(),
        note=note,
    )
    _write_lease(_lease_path(root), lease)
    return lease


def release_writer(*, repository_root: str | Path, writer_id: str) -> None:
    """Release cooperative ownership only for the current recorded writer."""

    root = Path(repository_root).resolve()
    current = inspect_writer(root)
    if current is None:
        return
    if current.writer_id != writer_id:
        raise WriterOwnershipError(
            f"cannot release writer {current.writer_id} as {writer_id}"
        )
    _lease_path(root).unlink(missing_ok=True)


__all__ = [
    "GitGuardError",
    "GitPathState",
    "GitSnapshot",
    "WriterLease",
    "WriterOwnershipError",
    "acquire_writer",
    "assert_safe_scope",
    "inspect_writer",
    "release_writer",
    "snapshot_git",
]
