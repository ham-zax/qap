"""Unit tests for the compiler-style QAP verification gate."""

from __future__ import annotations

import io
import runpy
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
GATE: dict[str, Any] = runpy.run_path(
    str(ROOT / "scripts/qap_gate.py"), run_name="qap_gate_test"
)


def test_build_steps_includes_core_and_optional_gates() -> None:
    parse_args = GATE["parse_args"]
    build_steps = GATE["build_steps"]

    default_steps = build_steps(parse_args([]))
    names = [step.name for step in default_steps]
    assert names == [
        "ruff_check",
        "ruff_format",
        "source_size",
        "import_layers",
        "pyright",
        "openapi_sync",
        "web_typecheck",
        "quant_invariants",
    ]

    scoped = build_steps(
        parse_args(
            [
                "--skip-invariants",
                "--pytest",
                "tests/test_smoke.py",
                "--vitest",
                "src/app.test.tsx",
            ]
        )
    )
    scoped_names = [step.name for step in scoped]
    assert "quant_invariants" not in scoped_names
    assert "pytest_targets" in scoped_names
    assert "vitest_targets" in scoped_names


def test_execute_reports_pass_and_fail_with_hints() -> None:
    gate_step_cls = GATE["GateStep"]
    execute = GATE["_execute"]

    passing = gate_step_cls(
        name="ok_step",
        command=(sys.executable, "-c", "print('ok')"),
        cwd=ROOT,
        hint="never shown",
    )
    failing = gate_step_cls(
        name="bad_step",
        command=(sys.executable, "-c", "import sys; print('boom'); sys.exit(2)"),
        cwd=ROOT,
        hint="Fix boom in foo.py.",
    )

    buffer = io.StringIO()
    code = execute([passing, failing], fail_fast=False, stream=buffer)
    output = buffer.getvalue()
    assert code == 1
    assert "[PASS] ok_step" in output
    assert "[FAIL] bad_step" in output
    assert "boom" in output
    assert "HINT: Fix boom in foo.py." in output
    assert "passed=1 failed=1" in output


def test_execute_fail_fast_stops_after_first_error() -> None:
    gate_step_cls = GATE["GateStep"]
    execute = GATE["_execute"]

    failing = gate_step_cls(
        name="first_bad",
        command=(sys.executable, "-c", "import sys; sys.exit(1)"),
        cwd=ROOT,
        hint="Fix first.",
    )
    skipped = gate_step_cls(
        name="never_runs",
        command=(sys.executable, "-c", "print('ran')"),
        cwd=ROOT,
        hint="Fix second.",
    )

    buffer = io.StringIO()
    code = execute([failing, skipped], fail_fast=True, stream=buffer)
    output = buffer.getvalue()
    assert code == 1
    assert "[FAIL] first_bad" in output
    assert "never_runs" not in output
