"""Ordinary degenerate histories must not manufacture evidence or crash analysis."""

import numpy as np
import pytest

from qap.relationship.anchor_measurements import lead_lag
from qap.relationship.pair_measurements import (
    MeasurementError,
    cointegration,
    hedge_ratio,
    hurst,
    percentile_of_last,
    ratio_bands,
    regime,
    rolling_mean_std,
)


def test_half_flat_hedge_is_unavailable() -> None:
    values = np.r_[np.ones(100), np.arange(100) * 0.01 + 1]
    assert hedge_ratio(2 * values, values) is None
    assert hedge_ratio(2 * values[::-1], values[::-1]) is None


def test_periodic_lag_tie_prefers_simultaneity() -> None:
    values = np.tile([1.0, -1.0], 200)
    result = lead_lag(values, values, max_lag=4)
    assert result is not None and result.lag_bars == 0


def test_constant_volatility_is_normal() -> None:
    for values in (np.ones(600), np.tile([0.0, 1.0], 300)):
        result = regime(values, window=40)
        assert result is not None and result.volatility == "normal"
        assert result.volatility_percentile == 50.0


def test_invalid_fit_settings_and_nonfinite_percentile_are_refused() -> None:
    values = np.arange(200, dtype=float)
    with pytest.raises(MeasurementError):
        cointegration(values, values, level=0)
    with pytest.raises(MeasurementError):
        hurst(values, max_lag=2)
    with pytest.raises(MeasurementError):
        percentile_of_last(np.array([1.0, np.nan]))


def test_collinear_cointegration_is_unavailable() -> None:
    values = np.cumsum(np.random.default_rng(3).standard_normal(300))
    assert cointegration(values, 2 * values) is None


def test_tiny_ratio_bands_keep_positive_std_and_finite_zscore() -> None:
    rng = np.random.default_rng(11)
    tiny_a = 1.5e-5 * np.exp(np.cumsum(rng.normal(0.0, 0.005, 100)))
    large_b = 90_000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.002, 100)))
    bands = ratio_bands(tiny_a / large_b, lookback=30)
    assert np.all(bands.std[29:] > 0.0)
    assert np.all(np.isfinite(bands.z[29:]))


def test_rolling_mean_std_handles_trailing_constant_zeros() -> None:
    rng = np.random.default_rng(20261027)
    values = np.r_[rng.standard_normal(40), np.zeros(20)]
    mean, std = rolling_mean_std(values, 20)
    assert mean[-1] == 0.0
    assert std[-1] == 0.0
