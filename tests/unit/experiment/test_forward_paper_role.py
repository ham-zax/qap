from datetime import UTC, datetime
from pathlib import Path

from qap.experiment import ExperimentManifest, execute_experiment, load_manifest
from qap.experiment.manifest import DataRole

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"


def test_forward_paper_is_distinct_from_final_oos_commitment_semantics() -> None:
    raw = load_manifest(MANIFEST).model_dump(mode="json")
    raw["experiment_name"] = "forward paper role boundary"
    raw["data_role"] = "forward_paper"
    manifest = ExperimentManifest.model_validate(raw)

    run = execute_experiment(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_timestamp=datetime(2026, 8, 17, 12, tzinfo=UTC),
    )

    assert manifest.data_role is DataRole.FORWARD_PAPER
    assert run.result.data_role is DataRole.FORWARD_PAPER
    assert run.result.final_oos_consumed is False
