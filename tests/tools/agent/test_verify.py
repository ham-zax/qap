import shlex
import sys
from pathlib import Path

from tools.agent.verify import run_verification


def _python(source: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(source)}"


def test_verification_records_success_command_exit_and_duration(tmp_path: Path) -> None:
    result = run_verification(
        _python("print('green')"),
        cwd=tmp_path,
        timeout_seconds=5,
    )

    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.command.endswith("print('green')'") or "green" in result.command
    assert result.duration_seconds >= 0
    assert result.output_tail.strip() == "green"
    assert result.log_path is None


def test_verification_records_failure_without_raising(tmp_path: Path) -> None:
    result = run_verification(
        _python("import sys; print('red'); sys.exit(7)"),
        cwd=tmp_path,
        timeout_seconds=5,
    )

    assert result.exit_code == 7
    assert result.timed_out is False
    assert result.output_tail.strip() == "red"


def test_verification_timeout_is_explicit(tmp_path: Path) -> None:
    result = run_verification(
        _python("import time; print('start', flush=True); time.sleep(2)"),
        cwd=tmp_path,
        timeout_seconds=0.05,
    )

    assert result.exit_code == 124
    assert result.timed_out is True
    assert "start" in result.output_tail


def test_verification_refuses_known_destructive_git_command(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="destructive Git"):
        run_verification(
            "git reset --hard",
            cwd=tmp_path,
            timeout_seconds=5,
        )


def test_verification_bounds_state_tail_but_preserves_full_log(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    result = run_verification(
        _python("print('x' * 1000)"),
        cwd=tmp_path,
        timeout_seconds=5,
        output_tail_chars=80,
        log_dir=log_dir,
    )

    assert result.exit_code == 0
    assert len(result.output_tail) == 80
    assert result.log_path is not None
    log_path = Path(result.log_path)
    assert log_path.is_file()
    assert len(log_path.read_text(encoding="utf-8")) > len(result.output_tail)
    evidence = result.evidence()
    assert evidence.command == result.command
    assert evidence.exit_code == 0
    assert evidence.output_tail == result.output_tail
