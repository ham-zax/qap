import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "tools/agent/qap_agent.py"


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


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repo"
    plan = repository / "docs/plans/tiny.md"
    plan.parent.mkdir(parents=True)
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "qap-agent@example.invalid")
    _git(repository, "config", "user.name", "QAP Agent Test")
    plan.write_text(
        "# Tiny Plan\n\n"
        "## Section 13.1 — First\n\n**Steps:**\n- [ ] One\n\n"
        "## Section 13.2 — Second\n\n**Steps:**\n- [ ] Two\n",
        encoding="utf-8",
    )
    (repository / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "-qm", "baseline")
    return repository, plan


def _run(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_status_reads_plan_without_creating_progress_state(tmp_path: Path) -> None:
    repository, plan = _repository(tmp_path)

    completed = _run("status", str(plan), cwd=repository)

    assert completed.returncode == 0
    assert "13.1" in completed.stdout
    assert "pending" in completed.stdout
    assert not (repository / ".qap-agent").exists()


def test_section_prints_only_requested_plan_section(tmp_path: Path) -> None:
    repository, plan = _repository(tmp_path)

    completed = _run("section", str(plan), "--section", "13.2", cwd=repository)

    assert completed.returncode == 0
    assert "13.2 — Second" in completed.stdout
    assert "- [ ] Two" in completed.stdout
    assert "13.1" not in completed.stdout


def test_checkpoint_and_verify_record_local_progress(tmp_path: Path) -> None:
    repository, plan = _repository(tmp_path)

    checkpoint = _run(
        "checkpoint",
        str(plan),
        "--section",
        "13.1",
        "--status",
        "in_progress",
        "--writer-id",
        "chatgpt-main",
        "--next-action",
        "run verification",
        cwd=repository,
    )
    assert checkpoint.returncode == 0, checkpoint.stderr

    verification_source = "print('verified')"
    verification_command = (
        f"{shlex.quote(sys.executable)} -c {shlex.quote(verification_source)}"
    )
    verification = _run(
        "verify",
        str(plan),
        "--section",
        "13.1",
        "--timeout",
        "5",
        "--command",
        verification_command,
        cwd=repository,
    )
    assert verification.returncode == 0, verification.stderr
    result = json.loads(verification.stdout)
    assert result["exit_code"] == 0

    progress = json.loads(
        (repository / ".qap-agent/tiny/progress.json").read_text(encoding="utf-8")
    )
    section = progress["sections"]["13.1"]
    assert section["status"] == "in_progress"
    assert section["writer_id"] == "chatgpt-main"
    assert section["verifications"][0]["exit_code"] == 0
    assert (repository / ".qap-agent/tiny/logs").is_dir()


def test_runtime_package_does_not_import_agent_tooling() -> None:
    for path in (ROOT / "src/qap").rglob("*.py"):
        assert "tools.agent" not in path.read_text(encoding="utf-8")


def test_harness_source_has_no_secondary_model_launcher() -> None:
    forbidden = ("codex", "claude", "gemini", "copilot", "openai")
    for path in (ROOT / "tools/agent").glob("*.py"):
        lowered = path.read_text(encoding="utf-8").lower()
        assert not any(token in lowered for token in forbidden), path


def test_cli_exposes_no_secondary_model_configuration(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)

    completed = _run("--help", cwd=repository)

    assert completed.returncode == 0
    lowered = completed.stdout.lower()
    assert "codex" not in lowered
    assert "model" not in lowered
    assert "reviewer" not in lowered
    assert "worker" not in lowered
