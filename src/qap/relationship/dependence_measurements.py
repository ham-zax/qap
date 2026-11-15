"""Descriptive dependence measurements: Kalman hedge, Granger, copula tails, rolling.

Evidence only, like ``pair_measurements``. Nothing here can produce a rotation call.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, cast

import numpy as np
from scipy import stats  # type: ignore[import-untyped]

from qap.relationship.lab_copula import copula_features
from qap.relationship.lab_features import kalman_hedge, rolling_correlation
from qap.relationship.pair_measurements import Floats, MeasurementError

MIN_BARS_KALMAN = 60
MIN_BARS_GRANGER = 100
MIN_BARS_COPULA = 120
COPULA_MAX_RETURNS = 4000
MIN_ROLLING_WINDOW = 20
GRANGER_MAX_LAG = 4
_GRANGER_LEVEL = 0.05


@dataclass(frozen=True, slots=True)
class KalmanReading:
    """Latest sequential hedge slope and how far it moved over the window."""

    beta: float
    standard_error: float
    beta_change: float


def kalman_reading(log_a: Floats, log_b: Floats) -> KalmanReading | None:
    if log_a.shape != log_b.shape:
        raise MeasurementError("log price series must have the same length")
    if log_a.size < MIN_BARS_KALMAN or np.ptp(log_b) == 0.0:
        return None
    hedge = kalman_hedge(log_a, log_b)
    # The first half is filter warm-up; change is measured over the settled half.
    settled = log_a.size // 2
    return KalmanReading(
        beta=float(hedge.beta[-1]),
        standard_error=float(hedge.standard_error[-1]),
        beta_change=float(hedge.beta[-1] - hedge.beta[settled]),
    )


@dataclass(frozen=True, slots=True)
class GrangerDirection:
    """Best lag by F-test; the p-value is Bonferroni-adjusted over tested lags."""

    lag_bars: int
    p_value: float
    passes: bool


@dataclass(frozen=True, slots=True)
class Granger:
    a_to_b: GrangerDirection
    b_to_a: GrangerDirection
    max_lag: int
    observations: int


def _lags(values: Floats, lag: int, rows: int) -> Floats:
    return np.column_stack(
        [values[lag - k : lag - k + rows] for k in range(1, lag + 1)]
    )


def _rss(design: Floats, target: Floats) -> float:
    coefficients, *_ = np.linalg.lstsq(design, target, rcond=None)
    residual = target - design @ coefficients
    return float(residual @ residual)


def _direction(cause: Floats, effect: Floats, max_lag: int) -> GrangerDirection | None:
    best: tuple[float, int] | None = None
    for lag in range(1, max_lag + 1):
        rows = effect.size - lag
        target = effect[lag:]
        own = np.column_stack((np.ones(rows), _lags(effect, lag, rows)))
        full = np.column_stack((own, _lags(cause, lag, rows)))
        restricted, unrestricted = _rss(own, target), _rss(full, target)
        freedom = rows - full.shape[1]
        if unrestricted <= 0.0 or freedom <= 0:
            return None
        statistic = ((restricted - unrestricted) / lag) / (unrestricted / freedom)
        p_value = float(cast(Any, stats).f.sf(statistic, lag, freedom))
        if not isfinite(p_value):
            return None
        if best is None or p_value < best[0]:
            best = (p_value, lag)
    if best is None:
        return None
    adjusted = min(1.0, best[0] * max_lag)
    return GrangerDirection(
        lag_bars=best[1], p_value=adjusted, passes=adjusted < _GRANGER_LEVEL
    )


def granger(
    returns_a: Floats, returns_b: Floats, *, max_lag: int = GRANGER_MAX_LAG
) -> Granger | None:
    """Historical predictive precedence in returns; never proof of a usable lead."""
    if returns_a.shape != returns_b.shape:
        raise MeasurementError("return series must have the same length")
    if max_lag < 1:
        raise MeasurementError("Granger max lag must be positive")
    if returns_a.size < MIN_BARS_GRANGER:
        return None
    if np.ptp(returns_a) == 0.0 or np.ptp(returns_b) == 0.0:
        return None
    forward = _direction(returns_a, returns_b, max_lag)
    backward = _direction(returns_b, returns_a, max_lag)
    if forward is None or backward is None:
        return None
    return Granger(forward, backward, max_lag, int(returns_a.size))


@dataclass(frozen=True, slots=True)
class CopulaTails:
    family: str
    lower_tail: float
    upper_tail: float
    observations: int


def copula_tails(close_a: Floats, close_b: Floats) -> CopulaTails | None:
    """Tail dependence of the fitted bivariate copula over the whole window."""
    if close_a.shape != close_b.shape:
        raise MeasurementError("close series must have the same length")
    if close_a.size < MIN_BARS_COPULA:
        return None
    keep = COPULA_MAX_RETURNS + 2
    close_a, close_b = close_a[-keep:], close_b[-keep:]
    # copula_features needs one held-back return; the fit uses every other one.
    fitted = copula_features(close_a, close_b, training=close_a.size - 2)
    if fitted is None:
        return None
    return CopulaTails(
        family=fitted.family,
        lower_tail=fitted.lower_tail,
        upper_tail=fitted.upper_tail,
        observations=fitted.training_observations,
    )


@dataclass(frozen=True, slots=True)
class RollingDependence:
    """Trailing return correlation: latest value and its range over the window."""

    window_bars: int
    latest: float
    low: float
    high: float


def rolling_dependence(
    returns_a: Floats, returns_b: Floats, *, window: int
) -> RollingDependence | None:
    if returns_a.shape != returns_b.shape:
        raise MeasurementError("return series must have the same length")
    window = min(window, returns_a.size)
    if window < MIN_ROLLING_WINDOW:
        return None
    values = rolling_correlation(returns_a, returns_b, window)
    finite = values[np.isfinite(values)]
    # A constant leg inside any window leaves that window undefined, not zero.
    if finite.size == 0 or not isfinite(float(values[-1])):
        return None
    return RollingDependence(
        window_bars=window,
        latest=float(values[-1]),
        low=float(finite.min()),
        high=float(finite.max()),
    )
