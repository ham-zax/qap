"""Compiler-grade self-verifying gate for QAP slices and worker loops.

Runs static/layer checks, OpenAPI + TypeScript contract checks, Quant math
borrow-checker invariants, and targeted or full test suites under a process
lock so parallel agents do not exhaust system memory (~7 GB WSL).
"""

from __future__ import annotations

import argparse
import fcntl
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
LOCK_PATH = Path("/tmp/qap-gate-heavy.lock")
TAIL_LINES = 45

_OPENAPI_CHECK_CODE = """
import json, sys
from pathlib import Path
from qap.api.app import create_default_app

disk_path = Path("web/openapi.json")
if not disk_path.is_file():
    print("web/openapi.json is missing.", file=sys.stderr)
    sys.exit(1)
live = json.dumps(create_default_app().openapi(), sort_keys=True)
saved = json.dumps(json.loads(disk_path.read_text(encoding="utf-8")), sort_keys=True)
if live != saved:
    msg = "OpenAPI drift: web/openapi.json does not match FastAPI schema."
    print(msg, file=sys.stderr)
    sys.exit(1)
"""

_PROTOCOL_CHECK_CODE = """
import sys
from pathlib import Path
from qap.experiment.lab_statistics import (
    DEFAULT_SPA_REPLICATES,
    PROOF_PROTOCOL_VERSION,
    check_family_resolution,
)
from qap.policy.lab_strategy_registry import STRATEGY_REGISTRY

if DEFAULT_SPA_REPLICATES < 9_999:
    print("DEFAULT_SPA_REPLICATES must be >= 9999.", file=sys.stderr)
    sys.exit(1)
if PROOF_PROTOCOL_VERSION != "qap.lab.proof.v2":
    print(f"Bad PROOF_PROTOCOL_VERSION: {PROOF_PROTOCOL_VERSION}", file=sys.stderr)
    sys.exit(1)
res = check_family_resolution(
    outer_family_size=1,
    pair_trial_count=1,
    replicates=DEFAULT_SPA_REPLICATES,
    alpha=0.05,
)
if not res.resolvable:
    print("Default SPA replicates cannot resolve a single hypothesis.", file=sys.stderr)
    sys.exit(1)
if not STRATEGY_REGISTRY:
    print("STRATEGY_REGISTRY is empty.", file=sys.stderr)
    sys.exit(1)
rd1 = Path("docs/research/2026-11-16-rd1-research-policy-proposal.md")
if not rd1.is_file():
    print("Missing RD-1 proposal document.", file=sys.stderr)
    sys.exit(1)
text = rd1.read_text(encoding="utf-8")
if "Status: approved" in text:
    required = (
        "## 1. Per-Method Assumptions",
        "## 3. Anchor-Residual Stationarity",
        "## 4. Benchmarks, Multiple Testing",
        "## 5. Attribution Controls",
    )
    missing = [heading for heading in required if heading not in text]
    if missing:
        print(f"Approved RD-1 missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
"""


@dataclass(frozen=True, slots=True)
class GateStep:
    name: str
    command: tuple[str, ...]
    cwd: Path
    hint: str
    timeout_seconds: float = 300.0
    show_tail_on_pass: bool = False


@dataclass(frozen=True, slots=True)
class GateOutcome:
    step: GateStep
    passed: bool
    seconds: float
    output_tail: str


def _tail(text: str, max_lines: int = TAIL_LINES) -> str:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[-max_lines:]
    return f"... ({len(lines) - max_lines} earlier lines omitted)\n" + "\n".join(kept)


def run_step(step: GateStep) -> GateOutcome:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            step.command,
            cwd=step.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=step.timeout_seconds,
            check=False,
        )
        combined = f"{completed.stdout}\n{completed.stderr}".strip()
        passed = completed.returncode == 0
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        combined = (
            f"Timed out after {step.timeout_seconds}s.\n{stdout}\n{stderr}".strip()
        )
        passed = False
    elapsed = time.monotonic() - started
    return GateOutcome(
        step=step,
        passed=passed,
        seconds=elapsed,
        output_tail=_tail(combined),
    )


def build_steps(args: argparse.Namespace) -> list[GateStep]:
    if args.full and (args.skip_invariants or args.skip_openapi or args.skip_web):
        raise ValueError(
            "--full cannot be combined with --skip-invariants, "
            "--skip-openapi, or --skip-web."
        )
    steps: list[GateStep] = [
        GateStep(
            name="ruff_check",
            command=("uv", "run", "ruff", "check", "."),
            cwd=ROOT,
            hint="Fix lint/import-order errors reported by ruff.",
        ),
        GateStep(
            name="ruff_format",
            command=("uv", "run", "ruff", "format", "--check", "."),
            cwd=ROOT,
            hint="Run `uv run ruff format .` on edited Python files.",
        ),
        GateStep(
            name="source_size",
            command=("uv", "run", "python", "scripts/check_source_size.py"),
            cwd=ROOT,
            hint="Keep hand-written modules below 500 lines (hard fail above 700).",
        ),
        GateStep(
            name="import_layers",
            command=("uv", "run", "lint-imports"),
            cwd=ROOT,
            hint="Respect .importlinter package layer direction.",
        ),
        GateStep(
            name="pyright",
            command=("uv", "run", "pyright", "src", "tests", "scripts"),
            cwd=ROOT,
            hint="Fix strict Pyright type errors before proceeding.",
        ),
    ]
    if not args.skip_openapi:
        steps.append(
            GateStep(
                name="openapi_sync",
                command=("uv", "run", "python", "-c", _OPENAPI_CHECK_CODE),
                cwd=ROOT,
                hint=(
                    "Regenerate contract files: "
                    "`uv run python scripts/export_openapi.py web/openapi.json "
                    "&& pnpm --dir web generate:api`."
                ),
            )
        )
    if not args.skip_web:
        steps.append(
            GateStep(
                name="web_typecheck",
                command=("pnpm", "--pm-on-fail=ignore", "--dir", "web", "typecheck"),
                cwd=ROOT,
                hint="Fix TypeScript errors in web/ or regenerate schema.d.ts.",
            )
        )
    if not args.skip_invariants:
        steps.append(
            GateStep(
                name="quant_invariants",
                command=("uv", "run", "pytest", "-q", "tests/invariants"),
                cwd=ROOT,
                hint=(
                    "A mathematical invariant failed (causality/no-lookahead, "
                    "price-scale invariance, spot conservation, or synthetic recovery)."
                ),
            )
        )
    steps.extend(
        [
            GateStep(
                name="regression_checks",
                command=(
                    "uv",
                    "run",
                    "pytest",
                    "-q",
                    "tests/unit/experiment/test_live_paper_runner.py",
                    "tests/unit/experiment/test_live_paper_candles.py",
                    "tests/unit/test_run_lab_trials.py",
                ),
                cwd=ROOT,
                hint=(
                    "Fix regressions in partial-fill recovery, neutral-signal "
                    "cancellation, tradable remainders, metadata round-trips, "
                    "candle timing, or declared-versus-executed research settings."
                ),
                timeout_seconds=300.0,
            ),
            GateStep(
                name="research_protocol",
                command=("uv", "run", "python", "-c", _PROTOCOL_CHECK_CODE),
                cwd=ROOT,
                hint="Fix research protocol / bootstrap / registry consistency.",
            ),
        ]
    )
    if args.pytest:
        steps.append(
            GateStep(
                name="pytest_targets",
                command=("uv", "run", "pytest", "-q", *args.pytest),
                cwd=ROOT,
                hint="Fix failing targeted Python unit/contract tests.",
                timeout_seconds=600.0,
            )
        )
    if args.vitest is not None:
        vitest_cmd = [
            "pnpm",
            "--pm-on-fail=ignore",
            "--dir",
            "web",
            "vitest",
            "run",
            *args.vitest,
        ]
        steps.append(
            GateStep(
                name="vitest_targets",
                command=tuple(vitest_cmd),
                cwd=ROOT,
                hint="Fix failing Vitest component/API tests in web/.",
                timeout_seconds=300.0,
            )
        )
    if args.full:
        steps.extend(
            [
                GateStep(
                    name="pytest_full",
                    command=("uv", "run", "pytest", "-q", "--durations=15"),
                    cwd=ROOT,
                    hint="Fix regressions in the full Python test suite.",
                    timeout_seconds=900.0,
                    show_tail_on_pass=True,
                ),
                GateStep(
                    name="engine_parity",
                    command=(
                        "uv",
                        "run",
                        "python",
                        "scripts/engine_parity.py",
                        "--max-bars",
                        "200",
                    ),
                    cwd=ROOT,
                    hint="Accounting parity diverged from independent bt oracle.",
                    timeout_seconds=300.0,
                ),
                GateStep(
                    name="web_vitest_full",
                    command=("pnpm", "--pm-on-fail=ignore", "--dir", "web", "test"),
                    cwd=ROOT,
                    hint="Fix regressions in the full Vitest suite.",
                    timeout_seconds=300.0,
                ),
                GateStep(
                    name="web_build",
                    command=("pnpm", "--pm-on-fail=ignore", "--dir", "web", "build"),
                    cwd=ROOT,
                    hint="Fix Vite production bundle errors.",
                    timeout_seconds=300.0,
                ),
            ]
        )
    return steps


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run compiler-style QAP verification gates."
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run fast static, contract, and invariant checks (default).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run fast gates plus full pytest, engine parity, vitest, and vite build.",
    )
    parser.add_argument(
        "--pytest",
        nargs="+",
        default=[],
        metavar="PATH",
        help="Targeted pytest file or directory paths to execute.",
    )
    parser.add_argument(
        "--vitest",
        nargs="*",
        default=None,
        metavar="PATH",
        help="Run Vitest (optionally scoped to paths inside web/).",
    )
    parser.add_argument(
        "--skip-invariants",
        action="store_true",
        help="Skip tests/invariants (only for pre-S1 infrastructure slices).",
    )
    parser.add_argument(
        "--skip-openapi",
        action="store_true",
        help="Skip OpenAPI in-memory sync check.",
    )
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="Skip web TypeScript check.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on the first failing gate.",
    )
    parser.add_argument(
        "--no-lock",
        action="store_true",
        help="Do not acquire /tmp/qap-gate-heavy.lock (for self-tests only).",
    )
    args = parser.parse_args(argv)
    if args.full and (args.skip_invariants or args.skip_openapi or args.skip_web):
        parser.error(
            "--full cannot be combined with --skip-invariants, "
            "--skip-openapi, or --skip-web."
        )
    return args


def _execute(steps: list[GateStep], *, fail_fast: bool, stream: TextIO) -> int:
    started = time.monotonic()
    passed_count = 0
    failed_count = 0
    for step in steps:
        print(f"[RUN ] {step.name} ...", file=stream, flush=True)
        outcome = run_step(step)
        if outcome.passed:
            passed_count += 1
            print(
                f"[PASS] {step.name} ({outcome.seconds:.2f}s)", file=stream, flush=True
            )
            if step.show_tail_on_pass and outcome.output_tail:
                print(outcome.output_tail, file=stream, flush=True)
            continue
        failed_count += 1
        cmd_str = " ".join(step.command)
        print(
            f"[FAIL] {step.name} ({outcome.seconds:.2f}s) -> {cmd_str}",
            file=stream,
            flush=True,
        )
        if outcome.output_tail:
            print(outcome.output_tail, file=stream, flush=True)
        print(f"HINT: {step.hint}\n", file=stream, flush=True)
        if fail_fast:
            break
    total = time.monotonic() - started
    print(
        f"QAP_GATE SUMMARY: passed={passed_count} failed={failed_count} "
        f"total_seconds={total:.2f}",
        file=stream,
        flush=True,
    )
    return 0 if failed_count == 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    steps = build_steps(args)
    if args.no_lock:
        return _execute(steps, fail_fast=args.fail_fast, stream=sys.stdout)
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_started = time.monotonic()
    print(f"[LOCK] acquiring {LOCK_PATH} ...", flush=True)
    with LOCK_PATH.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        lock_waited = time.monotonic() - lock_started
        print(f"[LOCK] acquired {LOCK_PATH} (waited {lock_waited:.2f}s)", flush=True)
        return _execute(steps, fail_fast=args.fail_fast, stream=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
