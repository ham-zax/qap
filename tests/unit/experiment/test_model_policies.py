from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest

from qap.experiment.data import ExperimentSetupError, LoadedExperimentData
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.model_policies import compose_model_strategy_policy
from qap.experiment.provenance import DatasetFingerprint
from qap.market import (
    BarInterval,
    MarketBar,
    PriceSnapshot,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PortfolioState

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, tzinfo=UTC)

BTC_ETH = VenueInstrument(venue="fixture", venue_symbol="BTCETH", base=BTC, quote=ETH)
BTC_USDT = VenueInstrument(
    venue="fixture", venue_symbol="BTCUSDT", base=BTC, quote=USDT
)
ETH_USDT = VenueInstrument(
    venue="fixture", venue_symbol="ETHUSDT", base=ETH, quote=USDT
)


def _series(instrument: VenueInstrument, closes: tuple[float, ...]):
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1.0,
            )
            for index, close in enumerate(closes)
        )
    )


def _manifest(
    relationship_id: str,
    *,
    btc_fingerprint: str = "b" * 64,
    eth_fingerprint: str = "c" * 64,
) -> ExperimentManifest:
    relationship_config: dict[str, object] = {
        "base_asset": "ETH",
        "quote_asset": "BTC",
        "window_bars": 4,
        "min_observations": 4,
        "evidence_instrument_ids": ["eth-usdt-evidence", "btc-usdt-evidence"],
    }
    return ExperimentManifest.model_validate(
        {
            "schema_version": "qap.experiment.manifest.v1",
            "experiment_name": "scanner model policy fixture",
            "description": (
                "Direct execution plus explicit evidence-only relationship legs."
            ),
            "research_family_id": "scanner-policy-fixture",
            "parent_run_id": None,
            "basket": ["BTC", "ETH"],
            "starting_quantities": {"BTC": "0.05", "ETH": "0.5"},
            "universe_mode": "declared_fixed_basket",
            "analysis_anchor": "ETH",
            "instruments": [
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
            ],
            "evidence_instrument_ids": [
                "btc-usdt-evidence",
                "eth-usdt-evidence",
            ],
            "interval": "1h",
            "data_window": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-01T06:00:00Z",
            },
            "evaluation_window": {
                "start": "2024-01-01T04:00:00Z",
                "end": "2024-01-01T06:00:00Z",
            },
            "data_sources": [
                {
                    "dataset_id": "btceth",
                    "instrument_id": "btc-eth",
                    "relative_path": "market/BTCETH.parquet",
                    "expected_semantic_fingerprint": "a" * 64,
                },
                {
                    "dataset_id": "btcusdt",
                    "instrument_id": "btc-usdt-evidence",
                    "relative_path": "market/BTCUSDT.parquet",
                    "expected_semantic_fingerprint": btc_fingerprint,
                },
                {
                    "dataset_id": "ethusdt",
                    "instrument_id": "eth-usdt-evidence",
                    "relative_path": "market/ETHUSDT.parquet",
                    "expected_semantic_fingerprint": eth_fingerprint,
                },
            ],
            "relationship": {
                "component_id": relationship_id,
                "config": relationship_config,
            },
            "policy": {
                "component_id": "evidence_tilt",
                "config": {
                    "base_asset": "ETH",
                    "quote_asset": "BTC",
                    "neutral_weights": {"BTC": "0.5", "ETH": "0.5"},
                    "neutral_threshold": "0.5",
                    "enter_threshold": "1.5",
                    "maximum_tilt": "0.10",
                    "neutral_mode": "neutral_target",
                },
            },
            "execution": {
                "execution_instrument_id": "btc-eth",
                "numeraire_asset": "ETH",
                "fee_bps": "10",
                "slippage_bps": "5",
                "minimum_rebalance_notional": "0",
                "base_step": None,
                "adverse_cost_scenario": {"fee_bps": "20", "slippage_bps": "10"},
            },
            "external_flows": [],
            "benchmarks": {
                "relationship_alpha_claim": True,
                "primary_incremental_benchmark": "band-5pct-half",
                "controls": [
                    {
                        "kind": "band_partial",
                        "control_id": "band-5pct-half",
                        "band_width": "0.05",
                        "partial_correction_fraction": "0.5",
                    }
                ],
            },
            "data_role": "development",
            "primary_metric": "primary_control_relative_terminal_wealth",
            "success_threshold": "0",
            "random_seed": None,
        }
    )


def _loaded(
    *,
    btc_values: tuple[float, ...] = (100.0, 103.0, 101.0, 108.0, 111.0, 109.0),
    eth_values: tuple[float, ...] = (50.0, 52.0, 51.0, 55.0, 54.0, 58.0),
    btc_fingerprint: str = "b" * 64,
    eth_fingerprint: str = "c" * 64,
) -> LoadedExperimentData:
    direct = _series(BTC_ETH, (10.0, 10.2, 10.1, 10.4, 10.3, 10.5))
    btc = _series(BTC_USDT, btc_values)
    eth = _series(ETH_USDT, eth_values)
    return LoadedExperimentData(
        aligned=align_bar_series((direct, btc, eth)),
        data_fingerprints=(
            DatasetFingerprint(dataset_id="btceth", fingerprint="a" * 64),
            DatasetFingerprint(dataset_id="btcusdt", fingerprint=btc_fingerprint),
            DatasetFingerprint(dataset_id="ethusdt", fingerprint=eth_fingerprint),
        ),
        series_by_instrument_id={
            "btc-eth": direct,
            "btc-usdt-evidence": btc,
            "eth-usdt-evidence": eth,
        },
        fingerprint_by_instrument_id={
            "btc-eth": "a" * 64,
            "btc-usdt-evidence": btc_fingerprint,
            "eth-usdt-evidence": eth_fingerprint,
        },
    )


def _decide_once(relationship_id: str):
    manifest = _manifest(relationship_id)
    composition = compose_model_strategy_policy(manifest, _loaded())
    decision = composition.policy.decide(
        as_of=datetime(2024, 1, 1, 5, tzinfo=UTC),
        current_state=PortfolioState.from_holdings(
            {BTC: Decimal("0.05"), ETH: Decimal("0.5")}
        ),
        price_snapshot=PriceSnapshot.from_prices(
            timestamp=datetime(2024, 1, 1, 5, tzinfo=UTC),
            numeraire=ETH,
            prices={BTC: Decimal("10"), ETH: Decimal("1")},
        ),
        applied_flows=(),
    )
    return composition, decision


def test_log_ratio_composition_uses_named_evidence_legs_not_direct_market() -> None:
    composition, decision = _decide_once("rolling_log_ratio_zscore")

    assert decision.evidence_ids
    assert len(composition.relationship_observations) == 1
    observation = composition.relationship_observations[0]
    assert observation.base_source_fingerprint == "c" * 64
    assert observation.quote_source_fingerprint == "b" * 64


def test_residual_mean_reversion_composes_named_evidence_legs() -> None:
    composition, decision = _decide_once("residual_mean_reversion")

    assert decision.evidence_ids
    observation = composition.relationship_observations[0]
    assert observation.model_id == "rolling_log_price_ols_residual_zscore"
    assert observation.base_source_fingerprint == "c" * 64
    assert observation.quote_source_fingerprint == "b" * 64


def test_warmup_changes_first_score_without_changing_start_or_eval_duration() -> None:
    baseline_manifest = _manifest("rolling_log_ratio_zscore")
    changed_manifest = _manifest(
        "rolling_log_ratio_zscore",
        btc_fingerprint="d" * 64,
        eth_fingerprint="e" * 64,
    )
    baseline = compose_model_strategy_policy(baseline_manifest, _loaded())
    changed = compose_model_strategy_policy(
        changed_manifest,
        _loaded(
            btc_values=(85.0, 120.0, 90.0, 108.0, 111.0, 109.0),
            eth_values=(60.0, 40.0, 70.0, 55.0, 54.0, 58.0),
            btc_fingerprint="d" * 64,
            eth_fingerprint="e" * 64,
        ),
    )
    as_of = baseline_manifest.effective_evaluation_window().start
    state = baseline_manifest.starting_state()
    prices = PriceSnapshot.from_prices(
        timestamp=as_of,
        numeraire=ETH,
        prices={BTC: Decimal("10.4"), ETH: Decimal("1")},
    )
    baseline.policy.decide(
        as_of=as_of,
        current_state=state,
        price_snapshot=prices,
        applied_flows=(),
    )
    changed.policy.decide(
        as_of=as_of,
        current_state=changed_manifest.starting_state(),
        price_snapshot=prices,
        applied_flows=(),
    )

    baseline_score = baseline.relationship_observations[0].values["score"]
    changed_score = changed.relationship_observations[0].values["score"]
    assert baseline_score != pytest.approx(changed_score)
    assert baseline_manifest.starting_state() == changed_manifest.starting_state()
    baseline_window = baseline_manifest.effective_evaluation_window()
    changed_window = changed_manifest.effective_evaluation_window()
    assert (
        baseline_window.end - baseline_window.start
        == changed_window.end - changed_window.start
    )


def test_relationship_evidence_ids_must_be_declared_evidence_instruments() -> None:
    manifest = _manifest("residual_mean_reversion")
    raw = manifest.model_dump(mode="json")
    relationship = raw["relationship"]
    assert isinstance(relationship, dict)
    config = cast(dict[str, object], relationship["config"])
    config["evidence_instrument_ids"] = ["eth-usdt-evidence", "btc-eth"]
    changed = ExperimentManifest.model_validate(raw)

    with pytest.raises(
        ExperimentSetupError, match="declared evidence-only instruments"
    ):
        compose_model_strategy_policy(changed, _loaded())
