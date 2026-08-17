"""Bounded verification command execution with recoverable local evidence."""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from tools.agent.state import VerificationEvidence

_TIMEOUT_EXIT_CODE = 124


@dataclass(frozen=True, slots=True)
class VerificationResult:
    command: str
    exit_code: int
    duration_seconds: float
    output_tail: str
    timed_out: bool
    log_path: str | None = None

    def evidence(self) -> VerificationEvidence:
        return VerificationEvidence(
            command=self.command,
            exit_code=self.exit_code,
            duration_seconds=self.duration_seconds,
            output_tail=self.output_tail,
            log_path=self.log_path,
        )


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=1)
    except ProcessLookupError, subprocess.TimeoutExpired:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=1)


def _write_log(log_dir: Path, *, command: str, output: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    identity = hashlib.sha256(
        f"{time.time_ns()}\0{command}".encode("utf-8")
    ).hexdigest()[:16]
    path = log_dir / f"verify-{identity}.log"
    path.write_text(output, encoding="utf-8")
    return path


def run_verification(
    command: str,
    *,
    cwd: str | Path,
    timeout_seconds: float,
    output_tail_chars: int = 4_000,
    log_dir: str | Path | None = None,
) -> VerificationResult:
    """Run one explicit reviewed command and capture bounded completion evidence."""

    if not command.strip():
        raise ValueError("verification command must be a non-empty string")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if output_tail_chars <= 0:
        raise ValueError("output_tail_chars must be positive")
    working_directory = Path(cwd).resolve()
    started = time.monotonic()
    process = subprocess.Popen(
        ["bash", "-lc", command],
        cwd=working_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        start_new_session=True,
    )
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout_seconds)
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_group(process)
        output, _ = process.communicate()
        exit_code = _TIMEOUT_EXIT_CODE
    duration = time.monotonic() - started
    full_output = output or ""
    log_path: str | None = None
    if log_dir is not None:
        log_path = str(
            _write_log(Path(log_dir).resolve(), command=command, output=full_output)
        )
    return VerificationResult(
        command=command,
        exit_code=exit_code,
        duration_seconds=duration,
        output_tail=full_output[-output_tail_chars:],
        timed_out=timed_out,
        log_path=log_path,
    )


__all__ = ["VerificationResult", "run_verification"]
