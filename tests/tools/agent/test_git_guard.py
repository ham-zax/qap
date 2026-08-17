import os
import subprocess
from pathlib import Path

import pytest

from tools.agent.git_guard import (
    GitGuardError,
    WriterOwnershipError,
    acquire_writer,
    assert_safe_scope,
    inspect_writer,
    release_writer,
    snapshot_git,
)


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "qap-agent@example.invalid")
    _git(repository, "config", "user.name", "QAP Agent Test")
    (repository / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    (repository / "allowed.txt").write_text("baseline\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "-qm", "baseline")
    return repository


ROOT = Path(__file__).resolve().parents[3]


def test_repository_ignores_local_agent_runtime_state() -> None:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", ".qap-agent/progress.json"],
        cwd=ROOT,
        check=False,
    )

    assert completed.returncode == 0


def test_git_snapshot_records_canonical_worktree_head_branch_and_status(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    (repository / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    snapshot = snapshot_git(repository)

    assert snapshot.worktree_path == repository.resolve()
    assert snapshot.head == _git(repository, "rev-parse", "HEAD")
    assert snapshot.branch in {"main", "master"}
    assert snapshot.changed_paths == ("tracked.txt",)
    assert len(snapshot.status_fingerprint) == 64


def test_scope_preserves_unrelated_preexisting_dirty_file(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    unrelated = repository / "tracked.txt"
    unrelated.write_text("user dirt\n", encoding="utf-8")
    baseline = snapshot_git(repository)

    (repository / "allowed.txt").write_text("planned change\n", encoding="utf-8")
    current = snapshot_git(repository)

    planned = assert_safe_scope(
        baseline=baseline,
        current=current,
        allowed_paths={"allowed.txt"},
    )

    assert planned == ("allowed.txt",)
    assert unrelated.read_text(encoding="utf-8") == "user dirt\n"


def test_scope_rejects_modifying_preexisting_unrelated_dirt(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    unrelated = repository / "tracked.txt"
    unrelated.write_text("user dirt\n", encoding="utf-8")
    baseline = snapshot_git(repository)
    unrelated.write_text("agent touched user dirt\n", encoding="utf-8")

    with pytest.raises(GitGuardError, match="pre-existing dirty path changed"):
        assert_safe_scope(
            baseline=baseline,
            current=snapshot_git(repository),
            allowed_paths={"allowed.txt"},
        )


def test_scope_rejects_unplanned_new_path_and_deletion(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    baseline = snapshot_git(repository)
    (repository / "unexpected.txt").write_text("surprise\n", encoding="utf-8")

    with pytest.raises(GitGuardError, match="unexpected changed path"):
        assert_safe_scope(
            baseline=baseline,
            current=snapshot_git(repository),
            allowed_paths={"allowed.txt"},
        )

    (repository / "unexpected.txt").unlink()
    (repository / "allowed.txt").unlink()
    with pytest.raises(GitGuardError, match="deletion"):
        assert_safe_scope(
            baseline=baseline,
            current=snapshot_git(repository),
            allowed_paths={"allowed.txt"},
        )


def test_second_live_writer_is_blocked_but_inspection_is_read_only(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    first = acquire_writer(
        repository_root=repository,
        writer_id="writer-one",
        owner_pid=os.getpid(),
        note="first",
    )
    lease_path = repository / ".qap-agent/worktree-writer.json"
    before = lease_path.read_bytes()

    observed = inspect_writer(repository)

    assert observed == first
    assert lease_path.read_bytes() == before
    with pytest.raises(WriterOwnershipError, match="writer-one"):
        acquire_writer(
            repository_root=repository,
            writer_id="writer-two",
            owner_pid=os.getpid(),
        )

    release_writer(repository_root=repository, writer_id="writer-one")
    second = acquire_writer(
        repository_root=repository,
        writer_id="writer-two",
        owner_pid=os.getpid(),
    )
    assert second.writer_id == "writer-two"


def test_same_writer_id_cannot_replace_a_different_live_owner_pid(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    sleeper = subprocess.Popen(["sleep", "5"])
    try:
        acquire_writer(
            repository_root=repository,
            writer_id="shared-writer-id",
            owner_pid=sleeper.pid,
        )

        with pytest.raises(WriterOwnershipError, match="shared-writer-id"):
            acquire_writer(
                repository_root=repository,
                writer_id="shared-writer-id",
                owner_pid=os.getpid(),
            )
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=2)


def test_stale_writer_is_replaced_after_process_evidence(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    acquire_writer(
        repository_root=repository,
        writer_id="stale-writer",
        owner_pid=99_999_999,
    )

    replacement = acquire_writer(
        repository_root=repository,
        writer_id="current-writer",
        owner_pid=os.getpid(),
        note="stale owner verified dead",
    )

    assert replacement.writer_id == "current-writer"
    assert replacement.owner_pid == os.getpid()
