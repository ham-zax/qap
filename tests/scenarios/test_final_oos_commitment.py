import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from qap.experiment import (
    ExperimentManifest,
    HoldoutAlreadyCommittedError,
    read_run_artifacts,
    run_experiment_to_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, tzinfo=UTC)


def _manifest_data() -> dict[str, object]:
    value: object = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("manifest fixture must be an object")
    return cast(dict[str, object], value)


def test_final_oos_is_committed_consumed_and_not_reusable(tmp_path: Path) -> None:
    data = _manifest_data()
    data["data_role"] = "final_oos"
    data["experiment_name"] = "scenario final holdout"
    manifest = ExperimentManifest.model_validate(data)

    paths = run_experiment_to_artifacts(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    loaded = read_run_artifacts(paths.run_directory)

    assert loaded.commitment is not None
    assert loaded.commitment.execution_status == "completed"
    assert loaded.commitment.consumed is True
    assert loaded.result.final_oos_consumed is True

    sibling_data = deepcopy(data)
    sibling_data["experiment_name"] = "scenario sibling after consumption"
    sibling_data["parent_run_id"] = paths.run_id
    with pytest.raises(HoldoutAlreadyCommittedError):
        run_experiment_to_artifacts(
            ExperimentManifest.model_validate(sibling_data),
            data_root=ROOT,
            repository_root=ROOT,
            run_root=tmp_path,
            run_timestamp=RUN_AT,
        )
