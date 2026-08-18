from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from qap.experiment import ExperimentManifest
from qap.experiment.events import build_event_records
from qap.experiment.runner import execute_experiment
from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    fingerprint_bar_series,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId
from qap.portfolio._decimal import exact_multiply, exact_sum

D = Decimal
START = datetime(2026, 8, 1, tzinfo=UTC)
RUN_AT = datetime(2026, 8, 19, tzinfo=UTC)
INTERVAL = BarInterval("1h")
USDT = AssetId("USDT")
ASSETS = tuple(AssetId(key) for key in ("AAA", "BBB", "CCC", "DDD"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _series(instrument: VenueInstrument):
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=10.0,
                high=10.0,
                low=10.0,
                close=10.0,
                volume=100.0,
            )
            for index in range(4)
        )
    )


def _manifest(tmp_path: Path) -> ExperimentManifest:
    instruments: list[dict[str, object]] = []
    data_sources: list[dict[str, object]] = []
    execution_ids: list[str] = []
    for asset in ASSETS:
        instrument_id = f"{asset.key.lower()}-usdt"
        execution_ids.append(instrument_id)
        instrument = VenueInstrument(
            venue="fixture",
            venue_symbol=f"{asset.key}USDT",
            base=asset,
            quote=USDT,
        )
        series = _series(instrument)
        relative_path = f"{instrument_id}.parquet"
        write_parquet_bar_series(tmp_path / relative_path, series)
        instruments.append(
            {
                "instrument_id": instrument_id,
                "venue": "fixture",
                "venue_symbol": instrument.venue_symbol,
                "base_asset": asset.key,
                "quote_asset": USDT.key,
            }
        )
        data_sources.append(
            {
                "dataset_id": f"fixture-{instrument_id}",
                "instrument_id": instrument_id,
                "relative_path": relative_path,
                "expected_semantic_fingerprint": fingerprint_bar_series(series),
            }
        )

    return ExperimentManifest.model_validate(
        {
            "schema_version": "qap.experiment.manifest.v1",
            "experiment_name": "four-asset bridge replay",
            "description": "Deterministic multi-asset ordinary-QAP replay fixture.",
            "research_family_id": "family-four-asset-bridge-v1",
            "parent_run_id": None,
            "basket": [asset.key for asset in ASSETS],
            "starting_quantities": {asset.key: "1" for asset in ASSETS},
            "universe_mode": "declared_fixed_basket",
            "analysis_anchor": USDT.key,
            "instruments": instruments,
            "evidence_instrument_ids": [],
            "interval": INTERVAL.label,
            "data_window": {
                "start": START.isoformat(),
                "end": (START + 4 * INTERVAL.duration).isoformat(),
            },
            "data_sources": data_sources,
            "relationship": {"component_id": "none", "config": {}},
            "policy": {
                "component_id": "scheduled_target",
                "config": {
                    "schedule": [
                        {
                            "as_of": (START + INTERVAL.duration).isoformat(),
                            "weights": {
                                "AAA": "0.40",
                                "BBB": "0.30",
                                "CCC": "0.20",
                                "DDD": "0.10",
                            },
                        }
                    ]
                },
            },
            "execution": {
                "mode": "multi_asset_bridge",
                "execution_instrument_ids": execution_ids,
                "bridge_asset": USDT.key,
                "market_metadata_mode": "historical_unconstrained",
                "numeraire_asset": USDT.key,
                "fee_bps": "10",
                "slippage_bps": "5",
                "minimum_rebalance_notional": "0",
                "adverse_cost_scenario": None,
            },
            "external_flows": [],
            "benchmarks": {
                "relationship_alpha_claim": False,
                "primary_incremental_benchmark": None,
                "controls": [],
            },
            "data_role": "development",
            "primary_metric": "hodl_relative_terminal_wealth",
            "success_threshold": "0",
            "random_seed": 7,
        }
    )


def test_ordinary_qap_replay_accounts_for_all_multi_asset_fills(tmp_path: Path) -> None:
    run = execute_experiment(
        _manifest(tmp_path),
        data_root=tmp_path,
        repository_root=REPOSITORY_ROOT,
        run_timestamp=RUN_AT,
    )
    strategy = run.role("strategy")
    first = strategy.trace.steps[0]

    assert first.multi_asset_execution is not None
    assert len(first.fills) >= 3
    assert first.fills == first.multi_asset_execution.fills
    assert first.state_after == first.multi_asset_execution.ending_state
    assert first.execution_reference_time == START + INTERVAL.duration
    assert len(first.execution_reference_prices) == 4
    assert all(price == D("10") for _, price in first.execution_reference_prices)
    assert strategy.trace.ending_state.quantity(USDT) >= D("0")
    assert first.valuation_price_snapshot.price(USDT) == D("1")

    expected_fees = exact_sum(
        exact_multiply(
            fill.fee_amount,
            step.valuation_price_snapshot.price(fill.quote),
        )
        for step in strategy.trace.steps
        for fill in step.fills
    )
    expected_slippage = exact_sum(
        exact_multiply(
            fill.slippage_value,
            step.valuation_price_snapshot.price(fill.quote),
        )
        for step in strategy.trace.steps
        for fill in step.fills
    )
    expected_turnover = exact_sum(
        exact_multiply(
            fill.gross_quote_notional,
            step.valuation_price_snapshot.price(fill.quote),
        )
        for step in strategy.trace.steps
        for fill in step.fills
    )
    assert strategy.fees_value == expected_fees
    assert strategy.slippage_value == expected_slippage
    assert strategy.turnover_value == expected_turnover

    events = build_event_records(run)
    strategy_fills = [
        event
        for event in events
        if event["role"] == "strategy" and event["event_type"] == "fill"
    ]
    strategy_executions = [
        event
        for event in events
        if event["role"] == "strategy" and event["event_type"] == "execution_outcome"
    ]
    assert len(strategy_fills) == len(strategy.trace.fills)
    assert strategy_executions[0]["payload"]["execution_mode"] == "multi_asset_bridge"
    assert strategy_executions[0]["payload"]["multi_asset_orders"] is not None
    assert strategy_executions[0]["payload"]["multi_asset_tracking_errors"] is not None


def test_multi_asset_manifest_rejects_singular_representative_instrument(
    tmp_path: Path,
) -> None:
    raw = _manifest(tmp_path).model_dump(mode="json")
    raw["execution"]["execution_instrument_id"] = "aaa-usdt"

    with pytest.raises(ValidationError, match="singular execution_instrument_id"):
        ExperimentManifest.model_validate(raw)
