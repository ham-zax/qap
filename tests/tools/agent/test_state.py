from pathlib import Path

import pytest

from tools.agent.plan import parse_plan
from tools.agent.state import (
    ProgressStateError,
    VerificationEvidence,
    checkpoint_section,
    load_progress,
)


def _plan(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    plan = repository / "docs/plans/tiny.md"
    plan.parent.mkdir(parents=True)
    (repository / ".git").mkdir()
    plan.write_text(
        "# Tiny Plan\n\n"
        "## Section 13.1 — First\n\n**Steps:**\n- [ ] One\n\n"
        "## Section 13.2 — Second\n\n**Steps:**\n- [ ] Two\n",
        encoding="utf-8",
    )
    return plan


def test_checkpoint_persists_atomic_json_and_markdown_and_resumes(
    tmp_path: Path,
) -> None:
    plan = parse_plan(_plan(tmp_path))
    repository = plan.repository_root

    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="in_progress",
        baseline_head="abc123",
        baseline_status_fingerprint="status-hash",
        worktree_path=str(repository.resolve()),
        branch="main",
        writer_id="chatgpt-main",
        writer_note="sole writer",
        note="parser RED complete",
        next_action="implement parser",
    )

    progress = load_progress(repository_root=repository, plan=plan)
    assert progress is not None
    section = progress.sections["13.1"]
    assert section.status == "in_progress"
    assert section.writer_id == "chatgpt-main"
    assert section.baseline_head == "abc123"
    assert section.started_at is not None
    assert section.ended_at is None
    state_root = repository / ".qap-agent/tiny"
    assert (state_root / "progress.json").is_file()
    assert (state_root / "progress.md").is_file()
    assert not tuple(state_root.glob("*.tmp"))
    assert "13.1" in (state_root / "progress.md").read_text(encoding="utf-8")


def test_complete_requires_passing_verification_and_commit(tmp_path: Path) -> None:
    plan = parse_plan(_plan(tmp_path))
    repository = plan.repository_root
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="in_progress",
        baseline_head="abc123",
        baseline_status_fingerprint="status-hash",
        worktree_path=str(repository.resolve()),
        branch="main",
        writer_id="chatgpt-main",
    )

    with pytest.raises(ProgressStateError, match="passing verification"):
        checkpoint_section(
            repository_root=repository,
            plan=plan,
            section_id="13.1",
            status="complete",
            commit_hash="deadbeef",
        )

    with pytest.raises(ProgressStateError, match="commit"):
        checkpoint_section(
            repository_root=repository,
            plan=plan,
            section_id="13.1",
            status="complete",
            verifications=(
                VerificationEvidence(
                    command="pytest",
                    exit_code=0,
                    duration_seconds=0.1,
                    output_tail="ok",
                ),
            ),
        )


def test_failed_verification_cannot_mark_section_complete(tmp_path: Path) -> None:
    plan = parse_plan(_plan(tmp_path))
    repository = plan.repository_root
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="in_progress",
        baseline_head="abc123",
        baseline_status_fingerprint="status-hash",
        worktree_path=str(repository.resolve()),
        branch="main",
        writer_id="chatgpt-main",
    )

    with pytest.raises(ProgressStateError, match="passing verification"):
        checkpoint_section(
            repository_root=repository,
            plan=plan,
            section_id="13.1",
            status="complete",
            commit_hash="deadbeef",
            verifications=(
                VerificationEvidence(
                    command="pytest",
                    exit_code=1,
                    duration_seconds=0.2,
                    output_tail="failed",
                ),
            ),
        )


def test_repaired_verification_command_can_complete_after_prior_failure(
    tmp_path: Path,
) -> None:
    plan = parse_plan(_plan(tmp_path))
    repository = plan.repository_root
    checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="in_progress",
        baseline_head="abc123",
        baseline_status_fingerprint="status-hash",
        worktree_path=str(repository.resolve()),
        branch="main",
        writer_id="chatgpt-main",
    )
    failed = VerificationEvidence(
        command="pytest",
        exit_code=1,
        duration_seconds=0.2,
        output_tail="failed",
    )
    repaired = VerificationEvidence(
        command="pytest",
        exit_code=0,
        duration_seconds=0.2,
        output_tail="passed",
    )

    completed = checkpoint_section(
        repository_root=repository,
        plan=plan,
        section_id="13.1",
        status="complete",
        commit_hash="deadbeef",
        verifications=(failed, repaired),
    )

    assert completed.sections["13.1"].status == "complete"


def test_corrupt_state_fails_closed_without_mutation(tmp_path: Path) -> None:
    plan = parse_plan(_plan(tmp_path))
    repository = plan.repository_root
    state_root = repository / ".qap-agent/tiny"
    state_root.mkdir(parents=True)
    progress_path = state_root / "progress.json"
    progress_path.write_text("{not-json", encoding="utf-8")
    before = progress_path.read_bytes()

    with pytest.raises(ProgressStateError, match="corrupt"):
        load_progress(repository_root=repository, plan=plan)

    assert progress_path.read_bytes() == before
