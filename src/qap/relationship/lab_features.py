"""Causal descriptive features for the Lab; no inventory or execution authority."""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from qap.relationship.pair_measurements import Floats, rolling_mean_std


@dataclass(frozen=True, slots=True)
class KalmanHedge:
    beta: Floats
    standard_error: Floats


def kalman_hedge(log_a: Floats, log_b: Floats) -> KalmanHedge:
    """Sequential intercept/slope filter, observing each completed price once."""
    if log_a.shape != log_b.shape:
        raise ValueError("Kalman prices must share an index.")
    state = np.array([0.0, 1.0])
    covariance = np.eye(2)
    betas, errors = np.empty(log_a.size), np.empty(log_a.size)
    for index, (a, b) in enumerate(zip(log_a, log_b, strict=True)):
        vector = np.array([1.0, b])
        covariance += np.eye(2) * 1e-5
        gain = covariance @ vector / float(vector @ covariance @ vector + 1e-3)
        state += gain * (a - vector @ state)
        covariance = (np.eye(2) - np.outer(gain, vector)) @ covariance
        betas[index] = state[1]
        errors[index] = np.sqrt(max(0.0, covariance[1, 1]))
    return KalmanHedge(beta=betas, standard_error=errors)


def rolling_covariance(a: Floats, b: Floats, window: int) -> Floats:
    """Trailing sample covariance; all pre-window values are unavailable."""
    mean_a, _ = rolling_mean_std(a, window)
    mean_b, _ = rolling_mean_std(b, window)
    mean_ab, _ = rolling_mean_std(a * b, window)
    return (mean_ab - mean_a * mean_b) * window / (window - 1)


def rolling_correlation(a: Floats, b: Floats, window: int) -> Floats:
    _, std_a = rolling_mean_std(a, window)
    _, std_b = rolling_mean_std(b, window)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = rolling_covariance(a, b, window) / (std_a * std_b)
    # Running sums leave ~sqrt(eps) residue in flat windows; treat that as flat.
    flat = (std_a <= 1e-6 * float(np.std(a))) | (std_b <= 1e-6 * float(np.std(b)))
    # A flat leg leaves correlation undefined; never clip its division to +/-1.
    return np.where(flat, np.nan, np.clip(result, -1.0, 1.0))


def hedge_residual(
    close_a: Floats,
    close_b: Floats,
    *,
    window: int,
    method: Literal["ratio", "ols", "tls", "kalman"],
) -> Floats:
    if method == "ratio":
        return close_a / close_b
    log_a, log_b = np.log(close_a), np.log(close_b)
    if method == "kalman":
        beta = kalman_hedge(log_a, log_b).beta
    else:
        _, std_a = rolling_mean_std(log_a, window)
        _, std_b = rolling_mean_std(log_b, window)
        covariance = rolling_covariance(log_a, log_b, window)
        with np.errstate(divide="ignore", invalid="ignore"):
            beta = covariance / std_b**2
            if method == "tls":
                difference = std_a**2 - std_b**2
                beta = (difference + np.sqrt(difference**2 + 4 * covariance**2)) / (
                    2 * covariance
                )
    # A changing hedge is a causal descriptive residual, never a synthetic holding.
    return log_a - beta * log_b


def trailing_zscore(values: Floats, window: int) -> Floats:
    """NaN warm-up stays local rather than contaminating later trailing windows."""
    result = np.full(values.size, np.nan)
    valid = np.flatnonzero(np.isfinite(values))
    if not valid.size:
        return result
    start = int(valid[0])
    usable = values[start:]
    if not np.isfinite(usable).all():
        return result
    mean, std = rolling_mean_std(usable, window)
    with np.errstate(divide="ignore", invalid="ignore"):
        result[start:] = np.where(std > 0, (usable - mean) / std, np.nan)
    return result
