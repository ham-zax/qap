"""Quant Borrow-Checker: non-negotiable mathematical and accounting laws.

DO NOT WEAKEN OR DELETE THESE TESTS. Every strategy estimator and Lab replay
path must satisfy strict causality (no lookahead), price-scale invariance,
rolling regime adaptation with hysteresis, and spot inventory conservation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

import numpy as np
import pytest

from qap.experiment.lab_proof import prove_lab_strategy
from qap.experiment.lab_replay import LabInputs, run_lab_replay
from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    validate_bar_series,
)
from qap.policy.lab_settings import LabSettings, SignalMethod
from qap.policy.lab_signals import signal_path
from qap.portfolio import AssetId
from qap.relationship.lab_features import hedge_residual
from qap.relationship.pair_measurements import Floats

HedgeKind = Literal["ratio", "ols", "tls", "kalman"]


def _synthetic_triplet(
    size: int = 360, seed: int = 42
) -> tuple[Floats, Floats, Floats]:
    rng = np.random.default_rng(seed)
    anchor_ret = rng.normal(0.0002, 0.012, size)
    anchor = 50_000.0 * np.exp(np.cumsum(anchor_ret))
    log_anchor = np.log(anchor)

    ou_a = np.zeros(size)
    ou_b = np.zeros(size)
    for idx in range(1, size):
        ou_a[idx] = 0.88 * ou_a[idx - 1] + rng.normal(0.0, 0.015)
        ou_b[idx] = 0.88 * ou_b[idx - 1] + rng.normal(0.0, 0.015)

    close_a = np.exp(-4.0 + 1.15 * (log_anchor - log_anchor[0]) + ou_a)
    close_b = np.exp(2.5 + 0.85 * (log_anchor - log_anchor[0]) + ou_b)
    return close_a, close_b, anchor


def _to_lab_inputs(
    close_a: Floats,
    close_b: Floats,
    anchor: Floats | None = None,
) -> LabInputs:
    interval = BarInterval("1h")
    start = datetime(2026, 1, 1, tzinfo=UTC)

    def build_series(code: str, values: Floats) -> ValidatedBarSeries:
        instrument = VenueInstrument(
            "binance", f"{code}USDT", AssetId(code), AssetId("USDT")
        )
        bars = tuple(
            MarketBar(
                instrument=instrument,
                interval=interval,
                candle_open_time=start + timedelta(hours=idx),
                open=float(values[idx - 1] if idx > 0 else price),
                high=float(max(price, values[idx - 1] if idx > 0 else price) * 1.001),
                low=float(min(price, values[idx - 1] if idx > 0 else price) * 0.999),
                close=float(price),
                volume=5_000_000.0,
            )
            for idx, price in enumerate(values)
        )
        return validate_bar_series(bars)

    return LabInputs(
        first=build_series("SOL", close_a),
        second=build_series("ETH", close_b),
        anchor=None if anchor is None else build_series("BTC", anchor),
    )


@pytest.mark.parametrize(
    ("method", "hedge_method", "use_anchor"),
    [
        ("zscore", "ratio", False),
        ("zscore", "ols", False),
        ("zscore", "tls", False),
        ("zscore", "kalman", False),
        ("trend", "ratio", False),
        ("copula", "ratio", False),
        ("copula", "ratio", True),
        ("lead_lag", "ratio", True),
    ],
)
def test_causality_no_lookahead_across_all_methods(
    method: SignalMethod,
    hedge_method: HedgeKind,
    use_anchor: bool,
) -> None:
    """Mutating bars >= t must never change signal values or preferences at < t."""
    a, b, anchor = _synthetic_triplet(size=320, seed=101)
    settings = LabSettings(
        method=method,
        hedge_method=hedge_method,
        lookback=70,
        fast_window=10,
        slow_window=30,
    )
    full_anchor = anchor if use_anchor else None
    baseline = signal_path(a, b, settings, full_anchor)

    for cutoff in (140, 210, 280):
        a_mut = a.copy()
        b_mut = b.copy()
        anc_mut = anchor.copy()
        a_mut[cutoff:] *= 7.5
        b_mut[cutoff:] *= 0.15
        anc_mut[cutoff:] *= 4.0

        truncated = signal_path(
            a[:cutoff],
            b[:cutoff],
            settings,
            anc_mut[:cutoff] if use_anchor else None,
        )
        mutated = signal_path(a_mut, b_mut, settings, anc_mut if use_anchor else None)

        np.testing.assert_allclose(
            truncated.values,
            baseline.values[:cutoff],
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        )
        np.testing.assert_allclose(
            mutated.values[:cutoff],
            baseline.values[:cutoff],
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        )
        np.testing.assert_array_equal(
            truncated.preference,
            baseline.preference[:cutoff],
        )
        np.testing.assert_array_equal(
            mutated.preference[:cutoff],
            baseline.preference[:cutoff],
        )


@pytest.mark.parametrize(
    ("method", "hedge_method", "use_anchor"),
    [
        ("zscore", "ratio", False),
        ("zscore", "ols", False),
        ("zscore", "tls", False),
        ("zscore", "kalman", False),
        ("trend", "ratio", False),
        ("copula", "ratio", False),
        ("copula", "ratio", True),
        ("lead_lag", "ratio", True),
    ],
)
def test_price_scale_invariance_across_all_methods(
    method: SignalMethod,
    hedge_method: HedgeKind,
    use_anchor: bool,
) -> None:
    """Multiplying Coin A by 1000x and Coin B by 0.0001x must not alter signals."""
    a, b, anchor = _synthetic_triplet(size=320, seed=202)
    settings = LabSettings(
        method=method,
        hedge_method=hedge_method,
        lookback=70,
        fast_window=10,
        slow_window=30,
    )

    unscaled = signal_path(a, b, settings, anchor if use_anchor else None)
    scaled = signal_path(
        a * 1_000.0,
        b * 0.0001,
        settings,
        (anchor * 500.0) if use_anchor else None,
    )

    assert unscaled.available is True
    assert scaled.available is True
    np.testing.assert_allclose(
        scaled.values,
        unscaled.values,
        rtol=1e-7,
        atol=1e-7,
        equal_nan=True,
    )
    np.testing.assert_array_equal(scaled.preference, unscaled.preference)


@pytest.mark.parametrize("hedge_method", ["ols", "tls", "kalman"])
def test_hedge_residual_includes_intercept_under_extreme_price_levels(
    hedge_method: HedgeKind,
) -> None:
    """Spread residual must not jump artificially when Coin B is priced at $70,000."""
    a, b, _ = _synthetic_triplet(size=240, seed=303)
    res_base = hedge_residual(a, b, window=50, method=hedge_method)
    res_shifted = hedge_residual(
        a * 500.0, b * 70_000.0, window=50, method=hedge_method
    )
    valid = np.isfinite(res_base) & np.isfinite(res_shifted)
    assert int(np.sum(valid)) > 150
    np.testing.assert_allclose(
        res_shifted[valid],
        res_base[valid],
        rtol=1e-7,
        atol=1e-7,
    )


@pytest.mark.parametrize("use_anchor", [False, True])
def test_rolling_copula_adapts_to_later_window_and_holds_across_multi_bar_dislocation(
    use_anchor: bool,
) -> None:
    """Copula must refit on rolling spreads and hold until spread normalizes."""
    rng = np.random.default_rng(404)
    size = 420
    anchor = 40_000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.008, size)))
    common = np.log(anchor) - np.log(anchor[0])

    # First 120 bars: tiny spread noise; bars 120+: 8x wider spread volatility.
    noise_scale = np.where(np.arange(size) < 120, 0.002, 0.016)
    eps_a = rng.normal(0.0, 1.0, size) * noise_scale
    eps_b = 0.65 * eps_a + rng.normal(0.0, np.sqrt(1 - 0.65**2), size) * noise_scale

    # Inject a 6-bar sustained underpricing of Coin A at bars 330..335 (-8% dip),
    # followed by full reversion back to 0 at bar 338.
    eps_a[330:336] -= 0.08
    eps_a[336] = -0.04
    eps_a[337:] = 0.0

    close_a = 100.0 * np.exp(common + eps_a)
    close_b = 2_000.0 * np.exp(common + eps_b)

    settings = LabSettings(method="copula", lookback=80, copula_probability=0.05)
    sig = signal_path(close_a, close_b, settings, anchor if use_anchor else None)

    assert sig.available is True
    # Coin A is deeply cheap across bars 330..335 -> must enter +1.0 and HOLD +1.0
    # across the multi-bar dislocation instead of resetting to 0.0 on bar 331.
    assert sig.preference[330] == 1.0
    assert np.all(sig.preference[331:335] == 1.0)
    # Once the dislocation fully reverts to equilibrium (bar 339+), state exits to 0.0.
    assert sig.preference[340] == 0.0


def test_lead_lag_rolling_beta_and_trend_hysteresis_prevent_whipsaw() -> None:
    """Lead-lag must adapt betas on rolling windows; trend must ignore micro-noise."""
    rng = np.random.default_rng(505)
    size = 360
    driver = rng.normal(0.0, 0.006, size)
    driver[280] = 0.04  # +4% anchor jump after regime shift

    ret_a = np.zeros(size)
    ret_b = np.zeros(size)
    # Bars 0..119: old regime has beta_a=0.2 < beta_b=1.8 (negative beta spread).
    ret_a[:120] = 0.2 * driver[:120] + rng.normal(0, 0.0005, 120)
    ret_b[:120] = 1.8 * driver[:120] + rng.normal(0, 0.0005, 120)
    # Bars 120..359: new regime flips to beta_a=1.8 > beta_b=0.2 (+1.6 beta spread).
    # At bar 280 Anchor jumps +4% while both coins move +0.8% simultaneously;
    # Coin A still owes +6.4% catch-up relative to Coin B under the current regime!
    for idx in range(120, size):
        if idx == 280:
            ret_a[idx] = 0.008
            ret_b[idx] = 0.008
        else:
            ret_a[idx] = 1.8 * driver[idx] + rng.normal(0, 0.0005)
            ret_b[idx] = 0.2 * driver[idx] + rng.normal(0, 0.0005)

    anchor = 1_000.0 * np.exp(np.cumsum(np.r_[0.0, driver[:-1]]))
    close_a = 50.0 * np.exp(np.cumsum(np.r_[0.0, ret_a[:-1]]))
    close_b = 50.0 * np.exp(np.cumsum(np.r_[0.0, ret_b[:-1]]))

    ll_sig = signal_path(
        close_a,
        close_b,
        LabSettings(method="lead_lag", lookback=80, anchor_threshold=0.015),
        anchor,
    )
    assert ll_sig.available is True
    # Frozen initial-window betas predict -1.0; rolling 80-bar betas predict +1.0.
    assert ll_sig.preference[281] == 1.0

    # Trend micro-noise check: +/- 1e-5 oscillation around flat ratio must not flip.
    idx_arr = np.arange(size, dtype=float)
    flat_a = 100.0 * (1.0 + 1e-5 * np.sin(idx_arr * 0.7))
    flat_b = np.full(size, 100.0)
    trend_sig = signal_path(
        flat_a,
        flat_b,
        LabSettings(method="trend", fast_window=8, slow_window=24),
    )
    finite_prefs = trend_sig.preference[np.isfinite(trend_sig.preference)]
    assert finite_prefs.size > 0
    assert np.all(finite_prefs == 0.0)


def test_mvp_defaults_to_full_0_to_100_rotation_and_conserves_spot_inventory() -> None:
    """MVP defaults to 50/50 start with 0.5 rotation size (0% to 100% owned spot)."""
    defaults = LabSettings()
    assert defaults.initial_weight == Decimal("0.5")
    assert defaults.rotation_size == Decimal("0.5")

    idx = np.arange(480, dtype=float)
    # Clean large-amplitude mean-reverting oscillation (+12% / -12%)
    close_a = 100.0 * np.exp(0.12 * np.sin(idx * 0.15))
    close_b = np.full(480, 100.0)
    inputs = _to_lab_inputs(close_a, close_b)

    low_cost = LabSettings(
        method="zscore",
        hedge_method="ols",
        lookback=40,
        entry=1.2,
        exit=0.2,
        minimum_hold=2,
        cooldown=2,
        fee_bps=Decimal("1"),
        slippage_bps=Decimal("1"),
        volume_impact_bps=Decimal("0"),
        auto_tune=False,
    )
    sig = signal_path(close_a, close_b, low_cost)
    replay = run_lab_replay(inputs, low_cost, sig)
    hodl = run_lab_replay(inputs, low_cost, sig, kind="hodl")

    assert len(replay.trades) >= 6
    assert replay.terminal_value > hodl.terminal_value
    for qty in replay.ending_state.holdings.values():
        assert qty >= Decimal("0")

    proof = prove_lab_strategy(inputs, low_cost, trial_count=1, identity_confirmed=True)
    assert proof.proof["final_oos_used"] is False
    assert proof.proof["passes"] is True
