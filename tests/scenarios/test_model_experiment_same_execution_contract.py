from datetime import UTC, datetime
from pathlib import Path

import pytest

from qap.experiment import ExperimentManifest, execute_experiment, load_manifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def _model_manifest(
    *,
    relationship: dict[str, object],
    policy: dict[str, object],
) -> ExperimentManifest:
    raw = load_manifest(MANIFEST_PATH).model_dump(mode="json")
    raw["experiment_name"] = f"phase10 {relationship['component_id']}"
    raw["relationship"] = relationship
    raw["policy"] = policy
    return ExperimentManifest.model_validate(raw)


def _pair_tilt_config() -> dict[str, object]:
    return {
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "neutral_weights": {"BTC": "0.5", "USDT": "0.5"},
        "neutral_threshold": "0",
        "enter_threshold": "0.000001",
        "maximum_tilt": "0.1",
        "neutral_mode": "neutral_target",
    }


def _pair_tilt_policy(component_id: str) -> dict[str, object]:
    return {"component_id": component_id, "config": _pair_tilt_config()}


@pytest.mark.parametrize(
    ("relationship", "policy"),
    [
        (
            {"component_id": "none", "config": {}},
            {
                "component_id": "slow_momentum_tilt",
                "config": {**_pair_tilt_config(), "lookback_bars": 2},
            },
        ),
        (
            {
                "component_id": "rolling_log_ratio_zscore",
                "config": {
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "window_bars": 3,
                    "min_observations": 3,
                },
            },
            _pair_tilt_policy("evidence_tilt"),
        ),
        (
            {
                "component_id": "cross_sectional_relative_log_return",
                "config": {"window_returns": 2},
            },
            {
                "component_id": "cross_sectional_tilt",
                "config": {
                    "neutral_weights": {"BTC": "0.5", "USDT": "0.5"},
                    "maximum_tilt": "0.1",
                },
            },
        ),
    ],
)
def test_model_strategy_variants_share_the_existing_execution_and_evaluation_contract(
    relationship: dict[str, object],
    policy: dict[str, object],
) -> None:
    manifest = _model_manifest(relationship=relationship, policy=policy)

    run = execute_experiment(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )

    strategy = run.role("strategy")
    hodl = run.role("hodl")
    primary = run.role("control:periodic-2")
    assert strategy.timestamps == hodl.timestamps == primary.timestamps
    assert strategy.trace.starting_state == manifest.starting_state()
    assert strategy.trace.declared_flows == hodl.trace.declared_flows
    assert strategy.trace.applied_flows == hodl.trace.applied_flows
    assert strategy.trace.fills
    assert strategy.fees_value > 0
    assert strategy.slippage_value > 0
    assert strategy.turnover_value > 0
    assert run.result.strategy_vs_primary_control is not None
    assert run.result.primary_incremental_benchmark == "periodic-2"

    for step in strategy.trace.steps:
        fill = step.fill
        if fill is None:
            continue
        assert step.execution_reference_time == step.decision_time
        assert step.execution_reference_price is not None
        assert fill.execution_timestamp == step.decision_time
