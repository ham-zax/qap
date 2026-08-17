import json
import subprocess
import sys
from pathlib import Path
from typing import cast

from qap.experiment.artifacts import read_run_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = "2026-08-17T06:00:00Z"


def _command(run_root: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "qap.experiment",
        str(MANIFEST_PATH),
        "--data-root",
        str(REPOSITORY_ROOT),
        "--repository-root",
        str(REPOSITORY_ROOT),
        "--run-root",
        str(run_root),
        "--run-timestamp",
        RUN_AT,
    ]


def test_cli_runs_one_manifest_and_reports_compact_result(tmp_path: Path) -> None:
    completed = subprocess.run(
        _command(tmp_path),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    raw: object = json.loads(completed.stdout)
    assert isinstance(raw, dict)
    payload = cast(dict[str, object], raw)
    assert payload["status"] == "negative"
    assert isinstance(payload["primary_metric_value"], str)
    run_directory = Path(cast(str, payload["run_directory"]))
    loaded = read_run_artifacts(run_directory)
    assert loaded.result.run_id == payload["run_id"]
    assert loaded.result.status.value == payload["status"]


def test_cli_refuses_to_overwrite_the_same_run_directory(tmp_path: Path) -> None:
    first = subprocess.run(
        _command(tmp_path),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    second = subprocess.run(
        _command(tmp_path),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert first.returncode == 0
    assert second.returncode == 1
    assert "will not be overwritten" in second.stderr
