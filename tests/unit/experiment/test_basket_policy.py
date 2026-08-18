# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from pydantic import ValidationError

import qap.experiment.basket_policy as basket_policy
from qap.experiment import ExperimentManifest
from qap.experiment.basket_manifest import basket_edge_rule
from qap.experiment.data import LoadedExperimentData
from qap.experiment.provenance import DatasetFingerprint
from qap.market import (
    BarInterval,
    MarketBar,
    PriceSnapshot,
    VenueInstrument,
    align_bar_series,
    fingerprint_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PortfolioState
from qap.portfolio._decimal import divide
from qap.relationship import RelationshipObservation, RelationshipObservationStatus

D = Decimal
START = datetime(2026, 8, 1, tzinfo=UTC)
INTERVAL = BarInterval("1h")
AAA = AssetId("AAA")
BBB = AssetId("BBB")
CCC = AssetId("CCC")
USDT = AssetId("USDT")
ASSETS = (AAA, BBB, CCC)


def _loaded_and_manifest() -> tuple[LoadedExperimentData, ExperimentManifest]:
    series_by_id = {}
    fingerprints_by_id = {}
    fingerprints = []
    instruments = []
    sources = []
    for position, asset in enumerate(ASSETS, start=1):
        instrument_id = f"{asset.key.lower()}-usdt"
        instrument = VenueInstrument(
            venue="fixture",
            venue_symbol=f"{asset.key}USDT",
            base=asset,
            quote=USDT,
        )
        series = validate_bar_series(
            tuple(
                MarketBar(
                    instrument=instrument,
                    interval=INTERVAL,
                    candle_open_time=START + index * INTERVAL.duration,
                    open=float(100 + position + index),
                    high=float(100 + position + index),
                    low=float(100 + position + index),
                    close=float(100 + position + index),
                    volume=100.0,
                )
                for index in range(4)
            )
        )
        fingerprint = fingerprint_bar_series(series)
        series_by_id[instrument_id] = series
        fingerprints_by_id[instrument_id] = fingerprint
        fingerprints.append(
            DatasetFingerprint(
                dataset_id=f"fixture-{instrument_id}",
                fingerprint=fingerprint,
            )
        )
        instruments.append(
            {
                "instrument_id": instrument_id,
                "venue": "fixture",
                "venue_symbol": instrument.venue_symbol,
                "base_asset": asset.key,
                "quote_asset": USDT.key,
            }
        )
        sources.append(
            {
                "dataset_id": f"fixture-{instrument_id}",
                "instrument_id": instrument_id,
                "relative_path": f"{instrument_id}.parquet",
                "expected_semantic_fingerprint": fingerprint,
            }
        )

    loaded = LoadedExperimentData(
        aligned=align_bar_series(tuple(series_by_id.values())),
        data_fingerprints=tuple(fingerprints),
        series_by_instrument_id=series_by_id,
        fingerprint_by_instrument_id=fingerprints_by_id,
    )
    edges = [
        {
            "edge_id": "aaa-bbb",
            "asset_a": "AAA",
            "asset_b": "BBB",
            "candidate_base": "AAA",
            "candidate_quote": "BBB",
            "model_family": "log_ratio_mean_reversion",
            "template_id": "fast",
        },
        {
            "edge_id": "bbb-ccc",
            "asset_a": "BBB",
            "asset_b": "CCC",
            "candidate_base": "BBB",
            "candidate_quote": "CCC",
            "model_family": "log_ratio_mean_reversion",
            "template_id": "fast",
        },
        {
            "edge_id": "aaa-ccc",
            "asset_a": "AAA",
            "asset_b": "CCC",
            "candidate_base": "AAA",
            "candidate_quote": "CCC",
            "model_family": "log_ratio_mean_reversion",
            "template_id": "fast",
        },
    ]
    manifest = ExperimentManifest.model_validate(
        {
            "schema_version": "qap.experiment.manifest.v1",
            "experiment_name": "basket-policy-unit",
            "description": "Focused Basket-V1 policy fixture.",
            "research_family_id": "basket-policy-unit-v1",
            "parent_run_id": None,
            "basket": [asset.key for asset in ASSETS],
            "starting_quantities": {asset.key: "1" for asset in ASSETS},
            "universe_mode": "declared_fixed_basket",
            "analysis_anchor": USDT.key,
            "instruments": instruments,
            "evidence_instrument_ids": [],
            "interval": "1h",
            "data_window": {
                "start": START.isoformat(),
                "end": (START + 4 * INTERVAL.duration).isoformat(),
            },
            "data_sources": sources,
            "relationship": {"component_id": "none", "config": {}},
            "policy": {
                "component_id": "basket_graph",
                "config": {"horizon": "short", "edges": edges},
            },
            "execution": {
                "mode": "multi_asset_bridge",
                "execution_instrument_ids": [
                    item["instrument_id"] for item in instruments
                ],
                "bridge_asset": "USDT",
                "market_metadata_mode": "historical_unconstrained",
                "numeraire_asset": "USDT",
                "fee_bps": "10",
                "slippage_bps": "5",
                "minimum_rebalance_notional": "0",
                "adverse_cost_scenario": {"fee_bps": "20", "slippage_bps": "10"},
            },
            "external_flows": [],
            "benchmarks": {
                "relationship_alpha_claim": True,
                "primary_incremental_benchmark": "relative-momentum-short",
                "controls": [
                    {
                        "kind": "band_partial",
                        "control_id": "band-5pct-half",
                        "band_width": "0.05",
                        "partial_correction_fraction": "0.5",
                    },
                    {
                        "kind": "pair_blind_relative_momentum",
                        "control_id": "relative-momentum-short",
                    },
                ],
            },
            "data_role": "development",
            "primary_metric": "primary_control_relative_terminal_wealth",
            "success_threshold": "0",
            "random_seed": 7,
        }
    )
    return loaded, manifest


def _observation(score: float) -> RelationshipObservation:
    class FakeObservation:
        status = RelationshipObservationStatus.VALID
        values = {"score": score}
        model_id = "fake"
        model_version = "1"
        input_fingerprint = "a" * 64

    return cast(RelationshipObservation, FakeObservation())


def test_composed_basket_policy_resolves_cycle_to_neutral_and_records_opinions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded, manifest = _loaded_and_manifest()
    scores = {("AAA", "BBB"): -2.0, ("BBB", "CCC"): -2.0, ("AAA", "CCC"): 2.0}

    def fake_observation(series: object, **_kwargs: object) -> RelationshipObservation:
        orientation = getattr(series, "orientation")
        return _observation(scores[(orientation.base.key, orientation.quote.key)])

    monkeypatch.setattr(
        basket_policy,
        "rolling_log_ratio_observation",
        fake_observation,
    )
    composition = basket_policy.compose_basket_strategy_policy(manifest, loaded)
    decision = composition.policy.decide(
        as_of=START + 3 * INTERVAL.duration,
        current_state=PortfolioState.from_holdings({asset: D("1") for asset in ASSETS}),
        price_snapshot=PriceSnapshot.from_prices(
            timestamp=START + 3 * INTERVAL.duration,
            numeraire=USDT,
            prices={AAA: D("1"), BBB: D("1"), CCC: D("1"), USDT: D("1")},
        ),
        applied_flows=(),
    )

    assert decision.target is not None
    assert set(decision.target.weights.values()) == {divide(D("1"), D("3"))}
    assert any(item.startswith("basket-opinion:v1:") for item in decision.evidence_ids)
    assert "basket-resolver:v1:maximum_tilt=0.10" in decision.evidence_ids


def test_basket_contract_derives_rule_and_rejects_weakened_benchmark_ladder() -> None:
    loaded, manifest = _loaded_and_manifest()
    del loaded
    assert basket_edge_rule(
        manifest.policy.config,
        manifest.interval,
        "fast",
    ) == (48, 46)

    raw = manifest.model_dump(mode="json")
    raw["benchmarks"]["controls"] = [raw["benchmarks"]["controls"][1]]
    with pytest.raises(ValidationError, match="band-5pct-half"):
        ExperimentManifest.model_validate(raw)

    raw = manifest.model_dump(mode="json")
    raw["benchmarks"]["controls"][1]["maximum_tilt"] = "0.20"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ExperimentManifest.model_validate(raw)
