"""Descriptive pair measurements over aligned close prices.

Every function here is evidence only: it describes how two coins have moved
relative to each other. Nothing in this module can produce a rotation call.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import NDArray
from scipy import stats  # type: ignore[import-untyped]
from statsmodels.tsa.stattools import coint  # type: ignore[import-untyped]

Floats = NDArray[np.float64]

MIN_BARS_CORRELATION = 30
MIN_BARS_COINTEGRATION = 100
MIN_BARS_HALF_LIFE = 50
MIN_BARS_HURST = 100
MIN_BARS_REGIME = 60
_RELATIVE_HEDGE_TOLERANCE = 0.25
_HURST_REVERTING_BELOW = 0.45
_HURST_TRENDING_ABOVE = 0.55
_EFFICIENCY_TRENDING_ABOVE = 0.30


class MeasurementError(ValueError):
    """Raised when a measurement receives malformed input."""


def as_positive(values: object, *, field: str) -> Floats:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise MeasurementError(f"{field} must be a non-empty one-dimensional array")
    if not np.isfinite(array).all() or not np.greater(array, 0.0).all():
        raise MeasurementError(f"{field} must be finite and strictly positive")
    return array


def log_returns(close: Floats) -> Floats:
    return cast(Floats, np.diff(np.log(close)))


@dataclass(frozen=True, slots=True)
class Correlation:
    pearson: float
    spearman: float
    kendall: float
    observations: int


def correlation(returns_a: Floats, returns_b: Floats) -> Correlation | None:
    """Pearson, Spearman and Kendall dependence of simultaneous log returns."""

    if returns_a.shape != returns_b.shape:
        raise MeasurementError("return series must have the same length")
    if returns_a.size < MIN_BARS_CORRELATION:
        return None
    if float(np.std(returns_a)) == 0.0 or float(np.std(returns_b)) == 0.0:
        return None
    pearson = float(np.corrcoef(returns_a, returns_b)[0, 1])
    scipy_stats = cast(Any, stats)
    spearman = float(scipy_stats.spearmanr(returns_a, returns_b).statistic)
    kendall = float(scipy_stats.kendalltau(returns_a, returns_b).statistic)
    return Correlation(
        pearson=pearson,
        spearman=spearman,
        kendall=kendall,
        observations=int(returns_a.size),
    )


@dataclass(frozen=True, slots=True)
class HedgeRatio:
    """Slope of log(A) on log(B): how many units of B hedge one unit of A."""

    ols: float
    tls: float
    first_half_ols: float
    second_half_ols: float
    stable: bool


def _ols_slope(x: Floats, y: Floats) -> float:
    x_centered = x - float(np.mean(x))
    denominator = float(np.dot(x_centered, x_centered))
    if denominator == 0.0:
        raise MeasurementError("hedge ratio needs a moving denominator")
    return float(np.dot(x_centered, y - float(np.mean(y))) / denominator)


def _tls_slope(x: Floats, y: Floats) -> float:
    centered = np.column_stack((x - float(np.mean(x)), y - float(np.mean(y))))
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    direction = vt[0]
    if direction[0] == 0.0:
        raise MeasurementError("total least squares slope is undefined")
    return float(direction[1] / direction[0])


def hedge_ratio(log_a: Floats, log_b: Floats) -> HedgeRatio | None:
    if log_a.shape != log_b.shape:
        raise MeasurementError("log price series must have the same length")
    if log_a.size < MIN_BARS_COINTEGRATION:
        return None
    if np.ptp(log_b) == 0.0:
        return None
    half = log_a.size // 2
    if np.ptp(log_b[:half]) == 0.0 or np.ptp(log_b[half:]) == 0.0:
        return None
    first = _ols_slope(log_b[:half], log_a[:half])
    second = _ols_slope(log_b[half:], log_a[half:])
    scale = max(abs(first), abs(second), 1e-12)
    return HedgeRatio(
        ols=_ols_slope(log_b, log_a),
        tls=_tls_slope(log_b, log_a),
        first_half_ols=first,
        second_half_ols=second,
        stable=abs(first - second) / scale <= _RELATIVE_HEDGE_TOLERANCE,
    )


@dataclass(frozen=True, slots=True)
class Cointegration:
    """Engle-Granger test on log prices; passes at the supplied level."""

    statistic: float
    p_value: float
    level: float
    passes: bool


def cointegration(
    log_a: Floats, log_b: Floats, *, level: float = 0.05
) -> Cointegration | None:
    if not 0.0 < level < 1.0:
        raise MeasurementError("cointegration level must be between 0 and 1")
    if log_a.shape != log_b.shape:
        raise MeasurementError("log price series must have the same length")
    if log_a.size < MIN_BARS_COINTEGRATION:
        return None
    if np.ptp(log_a) == 0.0 or np.ptp(log_b) == 0.0:
        return None
    slope = _ols_slope(log_b, log_a)
    residual = (log_a - float(np.mean(log_a))) - slope * (log_b - float(np.mean(log_b)))
    if np.ptp(residual) <= 1e-12 * max(1.0, float(np.ptp(log_a))):
        return None
    diff_res = np.diff(residual)
    if np.ptp(diff_res) <= 1e-12 * max(1.0, float(np.ptp(residual))):
        return None
    max_lag = max(1, int(12 * (log_a.size / 100) ** 0.25))
    if diff_res.size <= max_lag + 2:
        return None
    rows = diff_res.size - max_lag
    adf_design = np.column_stack(
        [
            np.ones(rows),
            residual[max_lag:-1],
            *(
                diff_res[max_lag - k : max_lag - k + rows]
                for k in range(1, max_lag + 1)
            ),
        ]
    )
    if int(np.linalg.matrix_rank(adf_design)) < adf_design.shape[1]:
        return None
    result = cast(
        "tuple[float, float, object]",
        coint(log_a, log_b, trend="c", maxlag=max_lag, autolag="aic"),
    )
    statistic, p_value = float(result[0]), float(result[1])
    if not isfinite(statistic) or not isfinite(p_value):
        return None
    return Cointegration(
        statistic=statistic,
        p_value=p_value,
        level=level,
        passes=p_value < level,
    )


@dataclass(frozen=True, slots=True)
class HalfLife:
    """Ornstein-Uhlenbeck style reversion speed of the log ratio, in bars."""

    bars: float | None
    reverting: bool


def half_life(log_ratio: Floats) -> HalfLife | None:
    """AR(1) fit of the log ratio; no half-life when it does not revert."""

    if log_ratio.size < MIN_BARS_HALF_LIFE:
        return None
    lagged = log_ratio[:-1]
    delta = np.diff(log_ratio)
    centered = lagged - float(np.mean(lagged))
    denominator = float(np.dot(centered, centered))
    if denominator == 0.0:
        return None
    slope = float(np.dot(centered, delta - float(np.mean(delta))) / denominator)
    phi = 1.0 + slope
    if not 0.0 < phi < 1.0:
        return HalfLife(bars=None, reverting=False)
    return HalfLife(bars=-log(2.0) / log(phi), reverting=True)


HurstReading = Literal["reverting", "random", "trending"]


@dataclass(frozen=True, slots=True)
class Hurst:
    exponent: float
    reading: HurstReading


def hurst(log_ratio: Floats, *, max_lag: int = 100) -> Hurst | None:
    """Scaling exponent of lagged differences: below 0.5 reverts, above trends."""

    if max_lag < 8:
        raise MeasurementError("Hurst estimation needs a maximum lag of at least 8")
    if log_ratio.size < MIN_BARS_HURST:
        return None
    top = min(max_lag, log_ratio.size // 4)
    lags = np.unique(np.geomspace(2, top, num=20).astype(int))
    spreads = np.array(
        [float(np.std(log_ratio[lag:] - log_ratio[:-lag])) for lag in lags]
    )
    if (spreads <= 0.0).any():
        return None
    slope = float(np.polyfit(np.log(lags), np.log(spreads), 1)[0])
    reading: HurstReading = (
        "reverting"
        if slope < _HURST_REVERTING_BELOW
        else "trending"
        if slope > _HURST_TRENDING_ABOVE
        else "random"
    )
    return Hurst(exponent=slope, reading=reading)


def percentile_of_last(values: Floats) -> float:
    """Share of the window at or below the latest value, from 0 to 100."""

    if values.size == 0:
        raise MeasurementError("percentile needs at least one value")
    if not np.isfinite(values).all():
        raise MeasurementError("percentile requires finite values")
    at_or_below = int(np.count_nonzero(cast(NDArray[np.bool_], values <= values[-1])))
    return at_or_below / values.size * 100.0


VolatilityState = Literal["calm", "normal", "stressed"]
TrendState = Literal["trending", "ranging"]


@dataclass(frozen=True, slots=True)
class Regime:
    volatility: VolatilityState
    volatility_percentile: float
    trend: TrendState
    efficiency: float


def regime(log_ratio: Floats, *, window: int) -> Regime | None:
    """Current ratio volatility against its own history, and trend efficiency."""

    if log_ratio.size < MIN_BARS_REGIME or window < 5 or log_ratio.size < 2 * window:
        return None
    _, rolling_std = rolling_mean_std(np.diff(log_ratio), window)
    rolling = rolling_std[~np.isnan(rolling_std)]
    constant = np.allclose(rolling, rolling[0], rtol=1e-10, atol=1e-14)
    percentile = 50.0 if constant else percentile_of_last(rolling)
    volatility: VolatilityState = (
        "calm" if percentile < 33.0 else "stressed" if percentile > 67.0 else "normal"
    )
    tail = log_ratio[-window:]
    path = float(np.sum(np.abs(np.diff(tail))))
    efficiency = 0.0 if path == 0.0 else abs(float(tail[-1] - tail[0])) / path
    return Regime(
        volatility=volatility,
        volatility_percentile=percentile,
        trend="trending" if efficiency > _EFFICIENCY_TRENDING_ABOVE else "ranging",
        efficiency=efficiency,
    )


def rolling_mean_std(values: Floats, lookback: int) -> tuple[Floats, Floats]:
    """Trailing mean and sample deviation in O(n); NaN until a full window.

    Sums are taken about the global mean so long flat stretches do not lose
    precision to cancellation.
    """

    if lookback < 2:
        raise MeasurementError("band lookback must be at least 2 bars")
    mean = np.full(values.size, np.nan)
    std = np.full(values.size, np.nan)
    if values.size < lookback:
        return mean, std
    shift = float(np.mean(values))
    centered = values - shift
    total = np.concatenate(([0.0], np.cumsum(centered)))
    squares = np.concatenate(([0.0], np.cumsum(centered * centered)))
    window_sum = total[lookback:] - total[:-lookback]
    window_squares = squares[lookback:] - squares[:-lookback]
    window_mean = window_sum / lookback
    variance = (window_squares - lookback * window_mean**2) / (lookback - 1)
    deviation = np.sqrt(np.maximum(variance, 0.0))
    flat = deviation <= 1e-12 * np.maximum(1.0, np.abs(window_mean + shift))
    mean[lookback - 1 :] = window_mean + shift
    std[lookback - 1 :] = np.where(flat, 0.0, deviation)
    return mean, std


@dataclass(frozen=True, slots=True)
class RatioBands:
    """Rolling mean and standard deviation of the displayed ratio."""

    mean: Floats
    std: Floats
    z: Floats


def ratio_bands(ratio: Floats, *, lookback: int) -> RatioBands:
    """Rolling mean, deviation and z-score; NaN until a full lookback exists."""

    mean, std = rolling_mean_std(ratio, lookback)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(std > 0.0, (ratio - mean) / std, np.nan)
    return RatioBands(mean=mean, std=std, z=cast(Floats, z))
