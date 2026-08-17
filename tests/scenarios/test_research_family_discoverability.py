import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qap.experiment import (
    ExperimentManifest,
    discover_family_runs,
    load_manifest,
    read_run_artifacts,
    run_experiment_to_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, tzinfo=UTC)


def test_family_history_discovers_root_before_declared_child(tmp_path: Path) -> None:
    root_run = run_experiment_to_artifacts(
        load_manifest(MANIFEST),
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    raw: object = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("manifest fixture must be an object")
    data = cast(dict[str, object], raw)
    data["experiment_name"] = "declared child"
    data["parent_run_id"] = root_run.run_id
    child_run = run_experiment_to_artifacts(
        ExperimentManifest.model_validate(data),
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )

    family = discover_family_runs(tmp_path, "family-two-asset-v1")

    assert family == (root_run.run_directory, child_run.run_directory)
    assert read_run_artifacts(family[1]).result.parent_run_id == root_run.run_id
