from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from qap.market import BarInterval, MarketBar, VenueInstrument, validate_bar_series
from qap.portfolio import AssetId
from qap.scanner.graph import NeighborRecord, SsdGraph
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.trials import (
    ScannerModelFamily,
    enumerate_fixed_trials,
    preference_score,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
CUTOFF = datetime(2026, 1, 15, tzinfo=UTC)
SCAN_ID = "a" * 64


def _source(asset: AssetId, interval: BarInterval, *, bars: int):
    instrument = VenueInstrument(
        venue="binance",
        venue_symbol=f"{asset.key}USDT",
        base=asset,
        quote=USDT,
    )
    start = CUTOFF - bars * interval.duration
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=interval,
                candle_open_time=start + position * interval.duration,
                source_close_time=(
                    start
                    + (position + 1) * interval.duration
                    - timedelta(milliseconds=1)
                ),
                open=100.0 + position * 0.01,
                high=100.0 + position * 0.01,
                low=100.0 + position * 0.01,
                close=100.0 + position * 0.01,
                volume=1.0,
            )
            for position in range(bars)
        )
    )


def _evaluated(asset: AssetId, interval: BarInterval) -> EvaluatedSeries:
    lookback = timedelta(days=14)
    bars = lookback // interval.duration
    return evaluate_series(
        _source(asset, interval, bars=bars),
        dataset_id=f"{asset.key.lower()}-{interval.label}",
        eligible_information_end=CUTOFF,
        lookback=lookback,
    )


def _graph() -> SsdGraph:
    return SsdGraph(
        scan_id=SCAN_ID,
        venue="binance",
        horizon=ScannerHorizon.SHORT.value,
        eligible_asset_count=2,
        total_valid_pair_comparisons=1,
        distance_digest="d" * 64,
        records=(
            NeighborRecord(
                scan_id=SCAN_ID,
                venue="binance",
                horizon=ScannerHorizon.SHORT.value,
                pair_id="BTC/ETH",
                asset_a="BTC",
                asset_b="ETH",
                ssd_distance=0.1,
                rank_from_a=1,
                rank_from_b=1,
                selected_by_a=True,
                selected_by_b=True,
                automatic_neighbor_selected=True,
                manual_pinned=False,
            ),
        ),
    )


def _model_series() -> dict[tuple[str, str], EvaluatedSeries]:
    return {
        (asset.key, interval.label): _evaluated(asset, interval)
        for asset in (BTC, ETH)
        for interval in (BarInterval("15m"), BarInterval("1h"))
    }


def test_fixed_trial_enumeration_has_one_ratio_and_two_residual_orientations() -> None:
    trials = enumerate_fixed_trials(_graph(), model_series_by_asset=_model_series())

    assert len(trials) == 18
    ratio = [
        trial
        for trial in trials
        if trial.model_family is ScannerModelFamily.LOG_RATIO_MEAN_REVERSION
    ]
    residual = [
        trial
        for trial in trials
        if trial.model_family is ScannerModelFamily.RESIDUAL_MEAN_REVERSION
    ]
    assert len(ratio) == 6
    assert len(residual) == 12
    assert {
        (trial.orientation.base.key, trial.orientation.quote.key) for trial in ratio
    } == {("BTC", "ETH")}
    assert {
        (trial.orientation.base.key, trial.orientation.quote.key) for trial in residual
    } == {("BTC", "ETH"), ("ETH", "BTC")}
    assert len({trial.candidate_id for trial in trials}) == 18
    assert all(len(trial.candidate_id) == 64 for trial in trials)


def test_trial_identity_binds_model_resolution_slice_fingerprints() -> None:
    model_series = _model_series()
    baseline = enumerate_fixed_trials(_graph(), model_series_by_asset=model_series)
    changed_series = dict(model_series)
    changed_series[("BTC", "15m")] = replace(
        changed_series[("BTC", "15m")],
        selection_slice_fingerprint="f" * 64,
    )
    changed = enumerate_fixed_trials(_graph(), model_series_by_asset=changed_series)

    baseline_ids = {
        (
            trial.resolution.label,
            trial.model_family.value,
            trial.template_id.value,
            trial.orientation.base.key,
        ): trial.candidate_id
        for trial in baseline
    }
    changed_ids = {
        (
            trial.resolution.label,
            trial.model_family.value,
            trial.template_id.value,
            trial.orientation.base.key,
        ): trial.candidate_id
        for trial in changed
    }
    assert (
        baseline_ids[("15m", "log_ratio_mean_reversion", "fast", "BTC")]
        != changed_ids[("15m", "log_ratio_mean_reversion", "fast", "BTC")]
    )
    assert (
        baseline_ids[("1h", "log_ratio_mean_reversion", "fast", "BTC")]
        == changed_ids[("1h", "log_ratio_mean_reversion", "fast", "BTC")]
    )


def test_trial_enumeration_rejects_insufficient_model_slice_quality() -> None:
    model_series = _model_series()
    model_series[("ETH", "15m")] = replace(
        model_series[("ETH", "15m")],
        bar_coverage=0.94,
    )

    with pytest.raises(ValueError, match="model slice coverage"):
        enumerate_fixed_trials(_graph(), model_series_by_asset=model_series)


def test_trial_enumeration_binds_lineage_and_template_window_bars() -> None:
    trials = enumerate_fixed_trials(_graph(), model_series_by_asset=_model_series())
    slow_15m_ratio = next(
        trial
        for trial in trials
        if trial.resolution == BarInterval("15m")
        and trial.template_id.value == "slow"
        and trial.model_family is ScannerModelFamily.LOG_RATIO_MEAN_REVERSION
    )

    assert slow_15m_ratio.window_bars == 14 * 24 * 4
    assert slow_15m_ratio.automatic_neighbor_selected is True
    assert slow_15m_ratio.manual_pinned is False
    assert slow_15m_ratio.preference_sign == -1
    assert set(slow_15m_ratio.selection_slice_fingerprints) == {
        _model_series()[("BTC", "15m")].selection_slice_fingerprint,
        _model_series()[("ETH", "15m")].selection_slice_fingerprint,
    }


def test_preference_score_is_negative_z_for_both_families() -> None:
    assert preference_score(2.5) == -2.5
    assert preference_score(-1.25) == 1.25
