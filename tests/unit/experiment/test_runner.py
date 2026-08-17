import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from qap.experiment import ExperimentManifest, load_manifest
from qap.experiment.result import ResultStatus
from qap.experiment.runner import (
    DatasetFingerprintMismatchError,
    execute_experiment,
    load_experiment_data,
)
from qap.portfolio._decimal import divide, exact_subtract

D = Decimal
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


def test_data_loader_validates_full_fingerprint_and_exact_window() -> None:
    manifest = load_manifest(MANIFEST_PATH)

    loaded = load_experiment_data(manifest, data_root=REPOSITORY_ROOT)

    assert loaded.aligned.timestamps[0] == manifest.data_window.start
    assert (
        loaded.aligned.timestamps[-1] + loaded.aligned.interval.duration
        == manifest.data_window.end
    )
    assert loaded.data_fingerprints[0].dataset_id == "fixture-btcusdt-1h"
    assert (
        loaded.data_fingerprints[0].fingerprint
        == manifest.data_sources[0].expected_semantic_fingerprint
    )


def test_data_loader_refuses_altered_dataset_before_replay(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    source = REPOSITORY_ROOT / manifest.data_sources[0].relative_path
    destination = tmp_path / manifest.data_sources[0].relative_path
    destination.parent.mkdir(parents=True)
    shutil.copyfile(source, destination)
    text = destination.read_text(encoding="utf-8")
    destination.write_text(text.replace("42050,100", "42051,100", 1), encoding="utf-8")

    with pytest.raises(DatasetFingerprintMismatchError, match="fixture-btcusdt-1h"):
        load_experiment_data(manifest, data_root=tmp_path)


def test_runner_composes_strategy_and_all_declared_controls_on_shared_inputs() -> None:
    manifest = load_manifest(MANIFEST_PATH)

    run = execute_experiment(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )

    expected_roles = {
        "strategy",
        "hodl",
        "matched_contribution",
        "control:periodic-2",
        "control:band-5pct-half",
        "strategy:adverse_cost",
    }
    assert {role.role for role in run.roles} == expected_roles
    flow_ids = tuple(flow.flow_id for flow in manifest.external_inventory_flows())
    for role in run.roles:
        assert role.trace.starting_state == manifest.starting_state()
        assert tuple(flow.flow_id for flow in role.trace.declared_flows) == flow_ids
        assert tuple(flow.flow_id for flow in role.trace.applied_flows) == flow_ids
        assert role.trace.unapplied_flows == ()
        assert role.timestamps == run.role("strategy").timestamps

    strategy = run.role("strategy")
    hodl = run.role("hodl")
    matched = run.role("matched_contribution")
    primary = run.role("control:periodic-2")
    expected_primary = exact_subtract(
        divide(strategy.terminal_value, primary.terminal_value),
        D("1"),
    )
    expected_hodl = exact_subtract(
        divide(strategy.terminal_value, hodl.terminal_value),
        D("1"),
    )
    expected_matched = exact_subtract(
        divide(strategy.terminal_value, matched.terminal_value),
        D("1"),
    )

    assert run.result.primary_metric_value == expected_primary
    assert run.result.strategy_vs_hodl == expected_hodl
    assert run.result.strategy_vs_matched_contribution == expected_matched
    assert run.result.strategy_vs_primary_control == expected_primary
    assert run.result.primary_incremental_benchmark == "periodic-2"
    assert run.result.final_oos_consumed is False
    assert run.result.data_role == manifest.data_role
    assert run.result.research_family_id == manifest.research_family_id
    assert run.provenance.run_timestamp_utc == RUN_AT

    if expected_primary > manifest.success_threshold:
        assert run.result.status is ResultStatus.POSITIVE
    elif expected_primary == manifest.success_threshold:
        assert run.result.status is ResultStatus.NEUTRAL
    else:
        assert run.result.status is ResultStatus.NEGATIVE


def test_result_keeps_exact_role_economics_and_flow_adjusted_diagnostics() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    run = execute_experiment(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )
    strategy = run.role("strategy")
    summary = run.result.role("strategy")

    assert summary.terminal_value == strategy.terminal_value
    assert summary.unitized_terminal_value == strategy.unitized_nav[-1]
    assert summary.terminal_quantities == {
        asset.key: quantity
        for asset, quantity in strategy.trace.ending_state.holdings.items()
    }
    assert summary.fill_count == len(strategy.trace.fills)
    assert summary.external_flow_ids == ("deposit-1",)
    assert summary.fees_value >= D("0")
    assert summary.slippage_value >= D("0")
    assert summary.turnover_value >= D("0")


def test_one_bar_no_trade_experiment_produces_a_neutral_result() -> None:
    import json
    from typing import cast

    raw: object = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("manifest fixture must contain one JSON object")
    data = cast(dict[str, object], raw)
    data["experiment_name"] = "one-bar no-trade"
    data["data_window"] = {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-01T01:00:00Z",
    }
    data["external_flows"] = []
    data["primary_metric"] = "hodl_relative_terminal_wealth"
    policy = cast(dict[str, object], data["policy"])
    policy["config"] = {"schedule": []}
    benchmarks = cast(dict[str, object], data["benchmarks"])
    benchmarks["relationship_alpha_claim"] = False
    benchmarks["primary_incremental_benchmark"] = None
    benchmarks["controls"] = []
    execution = cast(dict[str, object], data["execution"])
    execution["adverse_cost_scenario"] = None
    manifest = ExperimentManifest.model_validate(data)

    run = execute_experiment(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )

    assert run.result.start_timestamp == run.result.terminal_timestamp
    assert run.result.primary_metric_value == D("0")
    assert run.result.status is ResultStatus.NEUTRAL
    assert run.result.incremental_log_relative_to_hodl == ()
