import os
import subprocess
from pathlib import Path

import pytest

from tools.agent.git_guard import (
    WriterOwnershipError,
    acquire_writer,
    assert_safe_scope,
    release_writer,
    snapshot_git,
)
from tools.agent.plan import parse_plan
from tools.agent.state import checkpoint_section, load_progress
from tools.agent.verify import run_verification


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


def _toy_repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "toy"
    plan_path = repository / "docs/plans/toy.md"
    plan_path.parent.mkdir(parents=True)
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "qap-agent@example.invalid")
    _git(repository, "config", "user.name", "QAP Agent Dry Run")
    (repository / ".gitignore").write_text("/.qap-agent/\n", encoding="utf-8")
    (repository / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    plan_path.write_text(
        "# Toy Approved Plan\n\n"
        "## Section 13.1 — First slice\n\n"
        "**Steps:**\n- [ ] Create first.txt\n\n"
        "## Section 13.2 — Repair slice\n\n"
        "**Steps:**\n- [ ] Create second.txt with fixed content\n",
        encoding="utf-8",
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-qm", "baseline")
    return repository, plan_path


def test_toy_repository_sequential_dry_run(tmp_path: Path) -> None:
    repository, plan_path = _toy_repository(tmp_path)
    plan = parse_plan(plan_path)
    unrelated = repository / "tracked.txt"
    unrelated.write_text("unrelated user dirt\n", encoding="utf-8")

    first_writer = acquire_writer(
        repository_root=repository,
        writer_id="direct-agent-session-1",
        owner_pid=os.getpid(),
        note="toy slice one",
    )
    with pytest.raises(WriterOwnershipError):
        acquire_writer(
            repository_root=repository,
            writer_id="second-writer",
            owner_pid=os.getpid(),
        )

    baseline_one = snapshot_git(repository)
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="in_progress",
        baseline_head=baseline_one.head,
        baseline_status_fingerprint=baseline_one.status_fingerprint,
        worktree_path=first_writer.worktree_path,
        branch=first_writer.branch,
        writer_id=first_writer.writer_id,
        writer_note=first_writer.note,
        next_action="create and verify first.txt",
    )
    (repository / "first.txt").write_text("first\n", encoding="utf-8")
    scope_one = assert_safe_scope(
        baseline=baseline_one,
        current=snapshot_git(repository),
        allowed_paths={"first.txt"},
    )
    assert scope_one == ("first.txt",)
    first_verification = run_verification(
        'test "$(cat first.txt)" = first',
        cwd=repository,
        timeout_seconds=5,
        log_dir=repository / ".qap-agent/toy/logs",
    )
    assert first_verification.exit_code == 0
    _git(repository, "add", *scope_one)
    _git(repository, "commit", "-qm", "first slice")
    first_commit = _git(repository, "rev-parse", "HEAD")
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="complete",
        commit_hash=first_commit,
        verifications=(first_verification.evidence(),),
        next_action="continue to 13.2",
    )
    release_writer(repository_root=repository, writer_id=first_writer.writer_id)

    resumed = load_progress(repository_root=repository, plan=plan)
    assert resumed is not None
    assert resumed.sections["13.1"].commit_hash == first_commit
    assert resumed.sections["13.2"].status == "pending"

    second_writer = acquire_writer(
        repository_root=repository,
        writer_id="direct-agent-session-2",
        owner_pid=os.getpid(),
        note="explicit handoff after slice one",
    )
    baseline_two = snapshot_git(repository)
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.2",
        status="in_progress",
        baseline_head=baseline_two.head,
        baseline_status_fingerprint=baseline_two.status_fingerprint,
        worktree_path=second_writer.worktree_path,
        branch=second_writer.branch,
        writer_id=second_writer.writer_id,
        writer_note=second_writer.note,
        next_action="repair failing verification",
    )
    second = repository / "second.txt"
    second.write_text("broken\n", encoding="utf-8")
    verification_command = 'test "$(cat second.txt)" = fixed'
    failed = run_verification(
        verification_command,
        cwd=repository,
        timeout_seconds=5,
        log_dir=repository / ".qap-agent/toy/logs",
    )
    assert failed.exit_code != 0
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.2",
        status="in_progress",
        verifications=(failed.evidence(),),
        note="verification failed; repair required",
    )
    with pytest.raises(ValueError, match="passing verification"):
        checkpoint_section(
            repository_root=repository,
            plan=plan,
            section_id="13.2",
            status="complete",
            commit_hash="not-yet-valid",
        )

    second.write_text("fixed\n", encoding="utf-8")
    passed = run_verification(
        verification_command,
        cwd=repository,
        timeout_seconds=5,
        log_dir=repository / ".qap-agent/toy/logs",
    )
    assert passed.exit_code == 0
    scope_two = assert_safe_scope(
        baseline=baseline_two,
        current=snapshot_git(repository),
        allowed_paths={"second.txt"},
    )
    assert scope_two == ("second.txt",)
    _git(repository, "add", *scope_two)
    _git(repository, "commit", "-qm", "repair slice")
    second_commit = _git(repository, "rev-parse", "HEAD")
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.2",
        status="complete",
        commit_hash=second_commit,
        verifications=(failed.evidence(), passed.evidence()),
        note="same command repaired and reverified",
        next_action="none",
    )
    release_writer(repository_root=repository, writer_id=second_writer.writer_id)

    final = load_progress(repository_root=repository, plan=plan)
    assert final is not None
    assert all(section.status == "complete" for section in final.sections.values())
    assert final.sections["13.2"].commit_hash == second_commit
    assert unrelated.read_text(encoding="utf-8") == "unrelated user dirt\n"
    assert _git(repository, "status", "--short") == "M tracked.txt"
    assert _git(repository, "remote") == ""
    assert len(_git(repository, "log", "--format=%H").splitlines()) == 3
