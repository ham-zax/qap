from datetime import UTC, datetime
from pathlib import Path

from qap.experiment import (
    ExperimentManifest,
    read_run_artifacts,
    run_experiment_to_artifacts,
)
from qap.experiment.result import ResultStatus

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 9, 30, tzinfo=UTC)


def _final_oos_rolling_manifest() -> ExperimentManifest:
    from qap.experiment import load_manifest

    raw = load_manifest(MANIFEST).model_dump(mode="json")
    raw["experiment_name"] = "phase10 final oos rolling relationship"
    raw["data_role"] = "final_oos"
    raw["relationship"] = {
        "component_id": "rolling_log_ratio_zscore",
        "config": {
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "window_bars": 3,
            "min_observations": 3,
        },
    }
    raw["policy"] = {
        "component_id": "evidence_tilt",
        "config": {
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "neutral_weights": {"BTC": "0.5", "USDT": "0.5"},
            "neutral_threshold": "0",
            "enter_threshold": "0.000001",
            "maximum_tilt": "0.1",
            "neutral_mode": "neutral_target",
        },
    }
    return ExperimentManifest.model_validate(raw)


def test_negative_model_final_oos_is_a_completed_consumed_research_result(
    tmp_path: Path,
) -> None:
    manifest = _final_oos_rolling_manifest()

    paths = run_experiment_to_artifacts(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    loaded = read_run_artifacts(paths.run_directory)

    assert loaded.result.status is ResultStatus.NEGATIVE
    assert loaded.result.primary_metric_value < 0
    assert (
        loaded.result.strategy_vs_primary_control == loaded.result.primary_metric_value
    )
    assert loaded.result.final_oos_consumed is True
    assert loaded.commitment is not None
    assert loaded.commitment.execution_status == "completed"
    assert loaded.commitment.consumed is True
    assert loaded.commitment.consumed_at is not None
