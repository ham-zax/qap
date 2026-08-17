# pyright: reportPrivateUsage=false

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from qap.experiment.artifacts import run_experiment_to_artifacts
from qap.experiment.manifest import ExperimentManifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


def _final_manifest(
    *, name: str, parent_run_id: str | None = None
) -> ExperimentManifest:
    raw = cast(
        dict[str, object],
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    raw = deepcopy(raw)
    raw["data_role"] = "final_oos"
    raw["experiment_name"] = name
    raw["parent_run_id"] = parent_run_id
    return ExperimentManifest.model_validate(raw)


def test_registry_reservation_failure_leaves_recoverable_non_consumed_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.experiment.artifacts as artifacts

    manifest = _final_manifest(name="reservation failure")
    real_reserve = artifacts._reserve_holdout_registry
    observed_prelude: list[Path] = []
    attempts = 0

    def fail_once(
        run_root: Path,
        commitment: artifacts.FinalOosCommitment,
    ) -> Path:
        nonlocal attempts
        attempts += 1
        run_directory = run_root / commitment.run_id
        assert (run_directory / "manifest.json").is_file()
        assert (run_directory / "provenance.json").is_file()
        assert (run_directory / "commitment.json").is_file()
        observed_prelude.append(run_directory)
        if attempts == 1:
            raise OSError("deliberate registry publication failure")
        return real_reserve(run_root, commitment)

    monkeypatch.setattr(artifacts, "_reserve_holdout_registry", fail_once)

    with pytest.raises(OSError, match="registry publication failure"):
        run_experiment_to_artifacts(
            manifest,
            data_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )

    failed_run = observed_prelude[0]
    failed_commitment = json.loads(
        (failed_run / "commitment.json").read_text(encoding="utf-8")
    )
    assert failed_commitment["execution_status"] == "reservation_failed"
    assert failed_commitment["consumed"] is False
    assert (failed_run / "failure.json").is_file()
    assert not tuple((tmp_path / ".final-oos-commitments").glob("*.json"))

    retry_manifest = _final_manifest(
        name="reservation retry",
        parent_run_id=failed_run.name,
    )
    retried = run_experiment_to_artifacts(
        retry_manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    retry_commitment = json.loads(retried.commitment.read_text(encoding="utf-8"))
    assert retry_commitment["execution_status"] == "completed"
    assert retry_commitment["consumed"] is True
