import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qap.experiment import (
    ExperimentManifest,
    ResultStatus,
    read_run_artifacts,
    run_experiment_to_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, tzinfo=UTC)


def _wealth_destroying_accumulation_manifest() -> ExperimentManifest:
    raw: object = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("manifest fixture must be an object")
    data = cast(dict[str, object], raw)
    data["experiment_name"] = "negative coin accumulation"
    data["primary_metric"] = "hodl_relative_terminal_wealth"
    benchmarks = cast(dict[str, object], data["benchmarks"])
    benchmarks["relationship_alpha_claim"] = False
    benchmarks["primary_incremental_benchmark"] = None
    policy = cast(dict[str, object], data["policy"])
    policy["config"] = {
        "schedule": [
            {
                "as_of": "2024-01-01T03:00:00Z",
                "weights": {"BTC": "1", "USDT": "0"},
            }
        ]
    }
    execution = cast(dict[str, object], data["execution"])
    execution["fee_bps"] = "1000"
    execution["slippage_bps"] = "1000"
    execution["adverse_cost_scenario"] = None
    return ExperimentManifest.model_validate(data)


def test_coin_accumulation_cannot_excuse_owned_wealth_destruction(
    tmp_path: Path,
) -> None:
    paths = run_experiment_to_artifacts(
        _wealth_destroying_accumulation_manifest(),
        data_root=ROOT,
        repository_root=ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    loaded = read_run_artifacts(paths.run_directory)
    strategy = loaded.result.role("strategy")
    hodl = loaded.result.role("hodl")

    assert strategy.terminal_quantities["BTC"] > hodl.terminal_quantities["BTC"]
    assert strategy.terminal_value < hodl.terminal_value
    assert loaded.result.strategy_vs_hodl < 0
    assert loaded.result.status is ResultStatus.NEGATIVE
    assert paths.result.exists()
    assert paths.performance.exists()
    assert paths.events.exists()
