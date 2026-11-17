"""Unit tests for timestamped candle validation and replay/paper signal parity."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from qap.experiment.live_paper_candles import (
    LivePaperCandleError,
    candle_inputs_from_close_map,
    plan_candle_ingestion,
)
from qap.market import BarInterval, MarketBar, VenueInstrument, validate_bar_series
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import signal_path
from qap.portfolio import AssetId

USDT = AssetId("USDT")
BTC = VenueInstrument("binance", "BTCUSDT", AssetId("BTC"), USDT)
ETH = VenueInstrument("binance", "ETHUSDT", AssetId("ETH"), USDT)
SOL = VenueInstrument("binance", "SOLUSDT", AssetId("SOL"), USDT)


def _bars(
    inst: VenueInstrument, closes: np.ndarray, step_sec: int = 3600
) -> tuple[MarketBar, ...]:
    start = datetime(2026, 10, 1, 0, tzinfo=UTC)
    return tuple(
        MarketBar(
            instrument=inst,
            candle_open_time=start + timedelta(seconds=idx * step_sec),
            interval=BarInterval("1h" if step_sec == 3600 else "1m"),
            open=float(val),
            high=float(val) * 1.01,
            low=float(val) * 0.99,
            close=float(val),
            volume=100.0,
        )
        for idx, val in enumerate(closes)
    )


def test_candle_ingestion_is_idempotent_and_rejects_mutations_or_gaps() -> None:
    base = candle_inputs_from_close_map(
        "4h",
        {"BTCUSDT": [100.0, 101.0, 102.0], "ETHUSDT": [50.0, 50.5, 51.0]},
    )
    first = plan_candle_ingestion([], {}, base, [BTC, ETH])
    assert first.new_count == 3

    existing_t = list(first.new_times)
    existing_c = {k: list(v) for k, v in first.new_closes.items()}

    # Repeating the identical window yields zero new candles.
    repeat = plan_candle_ingestion(existing_t, existing_c, base, [BTC, ETH])
    assert repeat.new_count == 0
    assert repeat.overlap_count == 3

    # Adding one contiguous candle emits new_count == 1.
    plus_one = candle_inputs_from_close_map(
        "4h",
        {"BTCUSDT": [100.0, 101.0, 102.0, 103.0], "ETHUSDT": [50.0, 50.5, 51.0, 51.5]},
    )
    adv = plan_candle_ingestion(existing_t, existing_c, plus_one, [BTC, ETH])
    assert adv.new_count == 1 and adv.new_closes["BTCUSDT"] == (103.0,)

    # Altered historical close raises explicitly.
    altered = candle_inputs_from_close_map(
        "4h",
        {"BTCUSDT": [100.0, 999.0, 102.0], "ETHUSDT": [50.0, 50.5, 51.0]},
    )
    with pytest.raises(LivePaperCandleError, match="content mismatch"):
        plan_candle_ingestion(existing_t, existing_c, altered, [BTC, ETH])

    # Non-contiguous gap raises explicitly.
    gapped = candle_inputs_from_close_map(
        "4h",
        {"BTCUSDT": [104.0], "ETHUSDT": [52.0]},
        times=[existing_t[-1] + 2 * 14400],
    )
    with pytest.raises(LivePaperCandleError, match="Gap between"):
        plan_candle_ingestion(existing_t, existing_c, gapped, [BTC, ETH])


@pytest.mark.parametrize(
    ("method", "hedge", "anchored"),
    [
        ("zscore", "ratio", False),
        ("zscore", "ols", False),
        ("zscore", "tls", False),
        ("zscore", "kalman", False),
        ("copula", "ratio", False),
        ("copula", "ratio", True),
        ("trend", "ratio", False),
        ("lead_lag", "ratio", True),
    ],
)
def test_signal_causality_and_replay_prefix_parity_across_all_methods(
    method: str, hedge: str, anchored: bool
) -> None:
    rng = np.random.default_rng(42)
    n = 240
    anc_arr = 20.0 * np.exp(np.cumsum(rng.normal(0.0, 0.015, n)))
    a_arr = (
        100.0 * (anc_arr / 20.0) ** 0.8 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))
    )
    b_arr = 50.0 * (anc_arr / 20.0) ** 0.5 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))
    # Verify ValidatedBarSeries aligns cleanly as in replay.
    step_sec = 60 if method == "lead_lag" else 3600
    s_a = validate_bar_series(_bars(BTC, a_arr, step_sec=step_sec))
    s_b = validate_bar_series(_bars(ETH, b_arr, step_sec=step_sec))
    assert len(s_a.bars) == len(s_b.bars) == n

    # Copula requires lookback >= 60; use 72 so every method has finite signal values.
    cfg = LabSettings(
        method=method,  # type: ignore[arg-type]
        hedge_method=hedge,  # type: ignore[arg-type]
        auto_tune=False,
        lookback=72,
        entry=1.2,
        exit=0.4,
        copula_probability=0.05,
        copula_exit_band=0.15,
        fast_window=10,
        slow_window=30,
        trend_deadband=0.001,
        anchor_threshold=0.001,
        minimum_hold=0,
        cooldown=0,
    )
    prefix = 180
    sig_prefix = signal_path(
        a_arr[:prefix], b_arr[:prefix], cfg, anc_arr[:prefix] if anchored else None
    )
    assert sig_prefix.available is True
    assert int(np.isfinite(sig_prefix.values).sum()) >= 20
    assert int(np.isfinite(sig_prefix.preference).sum()) >= 20
    # Future-bar mutation after `prefix` must never alter signal at `prefix - 1`.
    mut_a = a_arr.copy()
    mut_b = b_arr.copy()
    mut_a[prefix:] *= 5.0
    mut_b[prefix:] *= 0.2
    sig_mutated = signal_path(mut_a, mut_b, cfg, anc_arr if anchored else None)
    assert np.allclose(
        sig_prefix.values,
        sig_mutated.values[:prefix],
        equal_nan=True,
    )
    assert np.allclose(
        sig_prefix.preference,
        sig_mutated.preference[:prefix],
        equal_nan=True,
    )


def test_metadata_round_trip_preserves_market_order_quantity_limits() -> None:
    from decimal import Decimal

    from qap.execution.precision import MarketPrecision
    from qap.experiment.live_paper_state import (
        metadata_from_record,
        metadata_to_record,
    )
    from qap.market import MarketMetadata

    meta = MarketMetadata(
        instrument=BTC,
        status="TRADING",
        price_tick=Decimal("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=None,
        minimum_notional=Decimal("5"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
        market_quantity_step=Decimal("1"),
        market_minimum_quantity=Decimal("1"),
        market_maximum_quantity=Decimal("100"),
    )
    restored = metadata_from_record(metadata_to_record(meta))
    assert restored == meta
    assert MarketPrecision(restored).quantity_down(Decimal("1.23")) == Decimal("1")
