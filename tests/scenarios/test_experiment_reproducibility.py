from datetime import UTC, datetime
from pathlib import Path

from qap.experiment import (
    load_manifest,
    read_run_artifacts,
    run_experiment_to_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, tzinfo=UTC)


def test_same_frozen_inputs_reproduce_same_run_and_economic_artifacts(
    tmp_path: Path,
) -> None:
    manifest = load_manifest(MANIFEST)
    first = run_experiment_to_artifacts(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path / "first",
        run_timestamp=RUN_AT,
    )
    second = run_experiment_to_artifacts(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path / "second",
        run_timestamp=RUN_AT,
    )
    left = read_run_artifacts(first.run_directory)
    right = read_run_artifacts(second.run_directory)

    assert first.run_id == second.run_id
    assert first.manifest.read_bytes() == second.manifest.read_bytes()
    assert first.provenance.read_bytes() == second.provenance.read_bytes()
    assert first.result.read_bytes() == second.result.read_bytes()
    assert first.events.read_bytes() == second.events.read_bytes()
    assert left.performance.equals(right.performance)
    assert left.inventory.equals(right.inventory)
