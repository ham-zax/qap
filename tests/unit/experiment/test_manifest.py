from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from pydantic import ValidationError

from qap.experiment.manifest import (
    DataRole,
    ExperimentManifest,
    PrimaryMetric,
    UniverseMode,
)


def valid_manifest_data() -> dict[str, object]:
    return {
        "schema_version": "qap.experiment.manifest.v1",
        "experiment_name": "two-asset dummy",
        "description": "Deterministic Phase 07 fixture.",
        "research_family_id": "family-two-asset-v1",
        "parent_run_id": None,
        "basket": ["btc", "usdt"],
        "starting_quantities": {"BTC": "1", "USDT": "1000"},
        "universe_mode": "declared_fixed_basket",
        "analysis_anchor": "USDT",
        "instruments": [
            {
                "instrument_id": "btc-usdt",
                "venue": "fixture",
                "venue_symbol": "BTCUSDT",
                "base_asset": "BTC",
                "quote_asset": "USDT",
            }
        ],
        "interval": "1h",
        "data_window": {
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-01T12:00:00Z",
        },
        "data_sources": [
            {
                "dataset_id": "fixture-btcusdt-1h",
                "instrument_id": "btc-usdt",
                "relative_path": "tests/fixtures/market/BTCUSDT_1h.csv",
                "expected_semantic_fingerprint": "a" * 64,
            }
        ],
        "relationship": {"component_id": "none", "config": {}},
        "policy": {
            "component_id": "scheduled_target",
            "config": {
                "schedule": [
                    {
                        "as_of": "2024-01-01T02:00:00Z",
                        "weights": {"BTC": "0.25", "USDT": "0.75"},
                    }
                ]
            },
        },
        "execution": {
            "execution_instrument_id": "btc-usdt",
            "numeraire_asset": "USDT",
            "fee_bps": "10",
            "slippage_bps": "5",
            "minimum_rebalance_notional": "1",
            "base_step": None,
            "adverse_cost_scenario": {
                "fee_bps": "20",
                "slippage_bps": "10",
            },
        },
        "external_flows": [
            {
                "flow_id": "deposit-1",
                "effective_time": "2024-01-01T03:00:00Z",
                "asset": "USDT",
                "quantity_delta": "100",
            }
        ],
        "benchmarks": {
            "relationship_alpha_claim": True,
            "primary_incremental_benchmark": "periodic-2",
            "controls": [
                {
                    "kind": "periodic_fixed_weight",
                    "control_id": "periodic-2",
                    "cadence_bars": 2,
                },
                {
                    "kind": "band_partial",
                    "control_id": "band-5pct-half",
                    "band_width": "0.05",
                    "partial_correction_fraction": "0.5",
                },
            ],
        },
        "data_role": "development",
        "primary_metric": "primary_control_relative_terminal_wealth",
        "success_threshold": "0",
        "random_seed": 7,
    }


def test_complete_manifest_is_frozen_normalized_and_domain_convertible() -> None:
    manifest = ExperimentManifest.model_validate(valid_manifest_data())

    assert manifest.data_role is DataRole.DEVELOPMENT
    assert manifest.universe_mode is UniverseMode.DECLARED_FIXED_BASKET
    assert (
        manifest.primary_metric
        is PrimaryMetric.PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH
    )
    assert manifest.basket == ("BTC", "USDT")
    assert manifest.starting_quantities == {
        "BTC": Decimal("1"),
        "USDT": Decimal("1000"),
    }
    assert manifest.data_window.start == datetime(2024, 1, 1, tzinfo=UTC)
    assert manifest.data_window.end == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert manifest.starting_state().holdings == {
        manifest.asset("BTC"): Decimal("1"),
        manifest.asset("USDT"): Decimal("1000"),
    }
    assert manifest.execution.cost_model().fee_bps == Decimal("10")
    assert manifest.external_inventory_flows()[0].quantity_delta == Decimal("100")

    with pytest.raises(ValidationError, match="frozen"):
        manifest.experiment_name = "mutated"  # type: ignore[misc]


def test_point_in_time_universe_fails_closed_until_eligibility_replay_exists() -> None:
    data = valid_manifest_data()
    data["universe_mode"] = "point_in_time_investable"

    with pytest.raises(ValidationError, match="eligibility-aware replay"):
        ExperimentManifest.model_validate(data)


def test_manifest_rejects_unknown_fields_recursively() -> None:
    data = valid_manifest_data()
    data["unexpected"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ExperimentManifest.model_validate(data)

    nested = valid_manifest_data()
    execution = deepcopy(nested["execution"])
    assert isinstance(execution, dict)
    execution["hidden_business_setting"] = "1"
    nested["execution"] = execution
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ExperimentManifest.model_validate(nested)


@pytest.mark.parametrize(
    "case",
    ["duplicate_basket", "missing_start", "negative_start"],
)
def test_manifest_rejects_invalid_basket_or_starting_inventory(case: str) -> None:
    data = valid_manifest_data()
    if case == "duplicate_basket":
        data["basket"] = ["BTC", "BTC"]
    elif case == "missing_start":
        data["starting_quantities"] = {"BTC": "1"}
    else:
        data["starting_quantities"] = {"BTC": "-1", "USDT": "1000"}
    with pytest.raises(ValidationError):
        ExperimentManifest.model_validate(data)


def test_manifest_rejects_invalid_timing_window() -> None:
    data = valid_manifest_data()
    data["data_window"] = {
        "start": "2024-01-02T00:00:00Z",
        "end": "2024-01-01T00:00:00Z",
    }
    with pytest.raises(ValidationError, match="start must be before end"):
        ExperimentManifest.model_validate(data)


def test_manifest_requires_dataset_fingerprint_and_safe_relative_path() -> None:
    missing = valid_manifest_data()
    sources = cast(list[dict[str, object]], deepcopy(missing["data_sources"]))
    sources[0].pop("expected_semantic_fingerprint")
    missing["data_sources"] = sources
    with pytest.raises(ValidationError, match="expected_semantic_fingerprint"):
        ExperimentManifest.model_validate(missing)

    unsafe = valid_manifest_data()
    sources = cast(list[dict[str, object]], deepcopy(unsafe["data_sources"]))
    sources[0]["relative_path"] = "../outside.csv"
    unsafe["data_sources"] = sources
    with pytest.raises(ValidationError, match="relative_path"):
        ExperimentManifest.model_validate(unsafe)


def test_manifest_requires_predeclared_incremental_control_for_relationship_claim() -> (
    None
):
    data = valid_manifest_data()
    benchmarks = deepcopy(data["benchmarks"])
    assert isinstance(benchmarks, dict)
    benchmarks["primary_incremental_benchmark"] = None
    data["benchmarks"] = benchmarks

    with pytest.raises(ValidationError, match="primary_incremental_benchmark"):
        ExperimentManifest.model_validate(data)


def test_relationship_claim_must_classify_success_against_primary_control() -> None:
    data = valid_manifest_data()
    data["primary_metric"] = "hodl_relative_terminal_wealth"

    with pytest.raises(ValidationError, match="relationship-alpha claim"):
        ExperimentManifest.model_validate(data)


def test_manifest_requires_exact_financial_strings_not_json_floats() -> None:
    data = valid_manifest_data()
    execution = deepcopy(data["execution"])
    assert isinstance(execution, dict)
    execution["fee_bps"] = 0.1
    data["execution"] = execution

    with pytest.raises(ValidationError, match="exact decimal"):
        ExperimentManifest.model_validate(data)


def _evidence_only_manifest_data() -> dict[str, object]:
    data = valid_manifest_data()
    data["basket"] = ["BTC", "ETH"]
    data["starting_quantities"] = {"BTC": "0.05", "ETH": "0.5"}
    data["analysis_anchor"] = "ETH"
    data["instruments"] = [
        {
            "instrument_id": "btc-eth",
            "venue": "fixture",
            "venue_symbol": "BTCETH",
            "base_asset": "BTC",
            "quote_asset": "ETH",
        },
        {
            "instrument_id": "btc-usdt-evidence",
            "venue": "fixture",
            "venue_symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
        },
        {
            "instrument_id": "eth-usdt-evidence",
            "venue": "fixture",
            "venue_symbol": "ETHUSDT",
            "base_asset": "ETH",
            "quote_asset": "USDT",
        },
    ]
    data["evidence_instrument_ids"] = [
        "btc-usdt-evidence",
        "eth-usdt-evidence",
    ]
    data["data_sources"] = [
        {
            "dataset_id": "btceth-1h",
            "instrument_id": "btc-eth",
            "relative_path": "market/BTCETH_1h.parquet",
            "expected_semantic_fingerprint": "a" * 64,
        },
        {
            "dataset_id": "btcusdt-1h",
            "instrument_id": "btc-usdt-evidence",
            "relative_path": "market/BTCUSDT_1h.parquet",
            "expected_semantic_fingerprint": "b" * 64,
        },
        {
            "dataset_id": "ethusdt-1h",
            "instrument_id": "eth-usdt-evidence",
            "relative_path": "market/ETHUSDT_1h.parquet",
            "expected_semantic_fingerprint": "c" * 64,
        },
    ]
    execution = deepcopy(data["execution"])
    assert isinstance(execution, dict)
    execution["execution_instrument_id"] = "btc-eth"
    execution["numeraire_asset"] = "ETH"
    data["execution"] = execution
    data["external_flows"] = []
    data["evaluation_window"] = {
        "start": "2024-01-01T04:00:00Z",
        "end": "2024-01-01T12:00:00Z",
    }
    return data


def test_manifest_defaults_evaluation_to_full_data_window() -> None:
    manifest = ExperimentManifest.model_validate(valid_manifest_data())

    assert manifest.evaluation_window is None
    assert manifest.effective_evaluation_window() == manifest.data_window


def test_manifest_allows_explicit_evidence_only_instruments_outside_basket() -> None:
    manifest = ExperimentManifest.model_validate(_evidence_only_manifest_data())

    assert manifest.evidence_instrument_ids == (
        "btc-usdt-evidence",
        "eth-usdt-evidence",
    )
    assert manifest.effective_evaluation_window().start == datetime(
        2024, 1, 1, 4, tzinfo=UTC
    )
    assert manifest.execution.execution_instrument_id == "btc-eth"


def test_manifest_rejects_evidence_execution_or_unlabeled_third_asset() -> None:
    execution_evidence = _evidence_only_manifest_data()
    execution = deepcopy(execution_evidence["execution"])
    assert isinstance(execution, dict)
    execution["execution_instrument_id"] = "btc-usdt-evidence"
    execution_evidence["execution"] = execution
    with pytest.raises(ValidationError, match="evidence-only instrument"):
        ExperimentManifest.model_validate(execution_evidence)

    unlabeled = _evidence_only_manifest_data()
    unlabeled["evidence_instrument_ids"] = ["eth-usdt-evidence"]
    with pytest.raises(ValidationError, match="instrument assets must belong"):
        ExperimentManifest.model_validate(unlabeled)


def test_manifest_rejects_evaluation_window_outside_data_or_pre_evaluation_flow() -> (
    None
):
    outside = _evidence_only_manifest_data()
    outside["evaluation_window"] = {
        "start": "2023-12-31T23:00:00Z",
        "end": "2024-01-01T12:00:00Z",
    }
    with pytest.raises(ValidationError, match="evaluation_window"):
        ExperimentManifest.model_validate(outside)

    flow = _evidence_only_manifest_data()
    flow["external_flows"] = [
        {
            "flow_id": "warmup-deposit",
            "effective_time": "2024-01-01T03:00:00Z",
            "asset": "ETH",
            "quantity_delta": "1",
        }
    ]
    with pytest.raises(ValidationError, match="evaluation_window"):
        ExperimentManifest.model_validate(flow)
