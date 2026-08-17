# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Never, cast

import pyarrow as pa
import pytest

from qap.experiment import load_manifest
from qap.experiment.artifacts import (
    ArtifactError,
    HoldoutAlreadyCommittedError,
    RunAlreadyExistsError,
    discover_family_runs,
    read_run_artifacts,
    run_experiment_to_artifacts,
    write_run_artifacts,
)
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.runner import (
    ExperimentRun,
    PreparedExperiment,
    execute_experiment,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


def _manifest_data() -> dict[str, object]:
    value: object = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("manifest fixture must be an object")
    return cast(dict[str, object], value)


def test_completed_run_writes_versioned_exact_readable_artifacts(
    tmp_path: Path,
) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    run = execute_experiment(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )

    paths = write_run_artifacts(run, run_root=tmp_path)
    loaded = read_run_artifacts(paths.run_directory)

    assert paths.run_directory.name == run.provenance.run_id
    assert paths.manifest.exists()
    assert paths.provenance.exists()
    assert paths.result.exists()
    assert paths.performance.exists()
    assert paths.inventory.exists()
    assert paths.events.exists()
    assert loaded.manifest == run.manifest
    assert loaded.provenance == run.provenance
    assert loaded.result == run.result
    assert loaded.result.status.value == "negative"
    assert loaded.performance.num_rows == len(run.role("strategy").trace.steps)
    assert loaded.inventory.num_rows == (
        len(run.roles) * len(run.role("strategy").trace.steps) * len(manifest.basket)
    )
    assert loaded.events
    assert loaded.performance.schema.metadata is not None
    assert (
        loaded.performance.schema.metadata[b"qap_schema"]
        == b"qap.experiment.performance.v1"
    )
    financial_fields = [
        field for field in loaded.performance.schema if field.name != "timestamp"
    ]
    assert all(field.type == pa.string() for field in financial_fields)
    raw_result = json.loads(paths.result.read_text(encoding="utf-8"))
    assert isinstance(raw_result["primary_metric_value"], str)
    assert isinstance(raw_result["roles"][0]["terminal_value"], str)

    with pytest.raises(RunAlreadyExistsError, match=run.provenance.run_id):
        write_run_artifacts(run, run_root=tmp_path)


def test_same_semantic_run_is_reproducible_across_separate_roots(
    tmp_path: Path,
) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    first = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path / "first",
        run_timestamp=RUN_AT,
    )
    second = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path / "second",
        run_timestamp=RUN_AT,
    )
    first_loaded = read_run_artifacts(first.run_directory)
    second_loaded = read_run_artifacts(second.run_directory)

    assert first.run_id == second.run_id
    assert first_loaded.manifest == second_loaded.manifest
    assert first_loaded.provenance == second_loaded.provenance
    assert first_loaded.result == second_loaded.result
    assert first_loaded.performance.equals(second_loaded.performance)
    assert first_loaded.inventory.equals(second_loaded.inventory)
    assert first.events.read_bytes() == second.events.read_bytes()


def test_final_oos_commitment_exists_before_replay_and_blocks_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.experiment.artifacts as artifacts

    data = _manifest_data()
    data["data_role"] = "final_oos"
    data["experiment_name"] = "final holdout"
    manifest = ExperimentManifest.model_validate(data)
    real_execute = artifacts.execute_prepared_experiment
    observed: list[bool] = []

    def checking_execute(prepared: PreparedExperiment) -> ExperimentRun:
        path = tmp_path / prepared.provenance.run_id / "commitment.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["execution_status"] == "committed"
        assert raw["consumed"] is False
        observed.append(True)
        return real_execute(prepared)

    monkeypatch.setattr(artifacts, "execute_prepared_experiment", checking_execute)
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    commitment = json.loads(paths.commitment.read_text(encoding="utf-8"))

    assert observed == [True]
    assert commitment["execution_status"] == "completed"
    assert commitment["consumed"] is True
    registry_files = tuple((tmp_path / ".final-oos-commitments").glob("*.json"))
    assert len(registry_files) == 1
    registry_commitment = json.loads(registry_files[0].read_text(encoding="utf-8"))
    assert registry_commitment["execution_status"] == "completed"
    assert registry_commitment["consumed"] is True
    assert read_run_artifacts(paths.run_directory).result.final_oos_consumed is True

    sibling_data = deepcopy(data)
    sibling_data["experiment_name"] = "same holdout sibling"
    sibling_data["parent_run_id"] = paths.run_id
    sibling = ExperimentManifest.model_validate(sibling_data)
    with pytest.raises(HoldoutAlreadyCommittedError, match="family-two-asset-v1"):
        run_experiment_to_artifacts(
            sibling,
            data_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )


def test_final_oos_holdout_reservation_is_atomic_for_concurrent_siblings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.experiment.artifacts as artifacts

    first_data = _manifest_data()
    first_data["data_role"] = "final_oos"
    first_data["experiment_name"] = "concurrent final holdout first"
    second_data = deepcopy(first_data)
    second_data["experiment_name"] = "concurrent final holdout second"
    first_manifest = ExperimentManifest.model_validate(first_data)
    second_manifest = ExperimentManifest.model_validate(second_data)
    real_execute = artifacts.execute_prepared_experiment
    entered = Event()
    release = Event()

    def blocking_execute(prepared: PreparedExperiment) -> ExperimentRun:
        entered.set()
        if not release.wait(timeout=30):
            raise TimeoutError("concurrent final-OOS test did not release replay")
        return real_execute(prepared)

    monkeypatch.setattr(artifacts, "execute_prepared_experiment", blocking_execute)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(
            run_experiment_to_artifacts,
            first_manifest,
            data_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )
        assert entered.wait(timeout=30)
        second_future = executor.submit(
            run_experiment_to_artifacts,
            second_manifest,
            data_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )
        try:
            with pytest.raises(
                HoldoutAlreadyCommittedError,
                match="family-two-asset-v1",
            ):
                second_future.result(timeout=30)
        finally:
            release.set()
        first_paths = first_future.result(timeout=30)

    assert first_paths.commitment.exists()
    registry_files = tuple((tmp_path / ".final-oos-commitments").glob("*.json"))
    assert len(registry_files) == 1


def test_failed_final_oos_execution_is_marked_consumed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.experiment.artifacts as artifacts

    data = _manifest_data()
    data["data_role"] = "final_oos"
    data["experiment_name"] = "failing final holdout"
    manifest = ExperimentManifest.model_validate(data)

    def fail_after_commitment(prepared: PreparedExperiment) -> Never:
        commitment = tmp_path / prepared.provenance.run_id / "commitment.json"
        assert commitment.exists()
        raise RuntimeError("deliberate replay failure")

    monkeypatch.setattr(artifacts, "execute_prepared_experiment", fail_after_commitment)
    with pytest.raises(RuntimeError, match="deliberate replay failure"):
        run_experiment_to_artifacts(
            manifest,
            data_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )

    run_directories = [
        path
        for path in tmp_path.iterdir()
        if path.is_dir() and path.name.startswith("run-")
    ]
    assert len(run_directories) == 1
    commitment = json.loads(
        (run_directories[0] / "commitment.json").read_text(encoding="utf-8")
    )
    assert commitment["execution_status"] == "failed"
    assert commitment["consumed"] is True
    assert (run_directories[0] / "failure.json").exists()


def test_family_and_parent_runs_are_discoverable(tmp_path: Path) -> None:
    first_manifest = load_manifest(MANIFEST_PATH)
    first = run_experiment_to_artifacts(
        first_manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    sibling_data = _manifest_data()
    sibling_data["experiment_name"] = "sibling development run"
    sibling_data["parent_run_id"] = first.run_id
    sibling_manifest = ExperimentManifest.model_validate(sibling_data)
    second = run_experiment_to_artifacts(
        sibling_manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )

    discovered = discover_family_runs(tmp_path, "family-two-asset-v1")

    assert discovered == (first.run_directory, second.run_directory)
    assert read_run_artifacts(second.run_directory).result.parent_run_id == first.run_id


def test_reader_rejects_tampered_parquet_schema_metadata(tmp_path: Path) -> None:
    import pyarrow.parquet as pq

    manifest = load_manifest(MANIFEST_PATH)
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    table = pq.read_table(paths.performance)
    metadata = dict(table.schema.metadata or {})
    metadata[b"qap_schema"] = b"qap.experiment.performance.tampered"
    pq.write_table(table.replace_schema_metadata(metadata), paths.performance)

    with pytest.raises(ValueError, match="unexpected artifact table schema"):
        read_run_artifacts(paths.run_directory)


def test_reader_requires_completed_final_oos_commitment(tmp_path: Path) -> None:
    data = _manifest_data()
    data["data_role"] = "final_oos"
    data["experiment_name"] = "reader commitment validation"
    manifest = ExperimentManifest.model_validate(data)
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )

    paths.commitment.unlink()

    with pytest.raises(ArtifactError, match="commitment"):
        read_run_artifacts(paths.run_directory)
