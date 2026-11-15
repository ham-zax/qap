"""Descriptive anchor measurements: beta, lead-lag and anchor ranking.

An anchor is the coin that drives the pair (BTC for the market, BNB for
BNB-chain coins). These measurements describe the link; they never trade.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from qap.relationship.pair_measurements import Floats, MeasurementError

MIN_BARS_ANCHOR = 100


@dataclass(frozen=True, slots=True)
class AnchorBeta:
    """Sensitivity of one coin's log returns to the anchor's, with fit quality."""

    beta: float
    r_squared: float


def anchor_beta(coin: Floats, anchor: Floats) -> AnchorBeta | None:
    if coin.shape != anchor.shape:
        raise MeasurementError("return series must have the same length")
    if coin.size < MIN_BARS_ANCHOR:
        return None
    anchor_centered = anchor - float(np.mean(anchor))
    variance = float(np.dot(anchor_centered, anchor_centered))
    coin_centered = coin - float(np.mean(coin))
    coin_variance = float(np.dot(coin_centered, coin_centered))
    if variance == 0.0 or coin_variance == 0.0:
        return None
    covariance = float(np.dot(anchor_centered, coin_centered))
    beta = covariance / variance
    return AnchorBeta(beta=beta, r_squared=covariance**2 / (variance * coin_variance))


@dataclass(frozen=True, slots=True)
class LeadLag:
    """How many bars the coin trails the anchor; negative means it leads."""

    lag_bars: int
    correlation: float
    stable: bool


def _correlation_at_lag(coin: Floats, anchor: Floats, lag: int) -> float:
    if lag >= 0:
        left, right = coin[lag:], anchor[: anchor.size - lag]
    else:
        left, right = coin[: coin.size + lag], anchor[-lag:]
    if left.size < 3 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def _peak_lag(coin: Floats, anchor: Floats, max_lag: int) -> tuple[int, float]:
    lags = range(-max_lag, max_lag + 1)
    scores = [_correlation_at_lag(coin, anchor, lag) for lag in lags]
    if all(np.isnan(scores)):
        raise MeasurementError("lead-lag has no defined correlation")
    peak = float(np.nanmax(np.abs(scores)))
    tied = [
        index
        for index, score in enumerate(scores)
        if np.isclose(abs(score), peak, rtol=1e-12, atol=1e-14)
    ]
    index = min(tied, key=lambda candidate: (abs(lags[candidate]), lags[candidate]))
    return list(lags)[index], float(scores[index])


def lead_lag(coin: Floats, anchor: Floats, *, max_lag: int) -> LeadLag | None:
    """Peak cross-correlation of coin returns against earlier anchor returns."""

    if coin.shape != anchor.shape:
        raise MeasurementError("return series must have the same length")
    if max_lag < 1:
        raise MeasurementError("max_lag must be at least one bar")
    if coin.size < max(MIN_BARS_ANCHOR, 8 * max_lag):
        return None
    try:
        lag, peak = _peak_lag(coin, anchor, max_lag)
        half = coin.size // 2
        first, _ = _peak_lag(coin[:half], anchor[:half], max_lag)
        second, _ = _peak_lag(coin[half:], anchor[half:], max_lag)
    except MeasurementError:
        return None
    return LeadLag(
        lag_bars=lag,
        correlation=peak,
        stable=abs(first - second) <= 1 and abs(lag - first) <= 1,
    )


@dataclass(frozen=True, slots=True)
class AnchorFit:
    """How much of both coins' moves one candidate anchor explains."""

    anchor: str
    beta_a: float
    beta_b: float
    r_squared_a: float
    r_squared_b: float
    joint_explained: float


def rank_anchors(
    candidates: Mapping[str, tuple[Floats, Floats, Floats]],
) -> tuple[AnchorFit, ...]:
    """Rank candidates by mean explained variance of both coins' log returns.

    Each candidate maps to (returns of A, returns of B, returns of the anchor)
    on the bars all three coins share, so candidates with shorter history stay
    comparable.
    """

    fits: list[AnchorFit] = []
    for name, (returns_a, returns_b, anchor_returns) in candidates.items():
        beta_a = anchor_beta(returns_a, anchor_returns)
        beta_b = anchor_beta(returns_b, anchor_returns)
        if beta_a is None or beta_b is None:
            continue
        fits.append(
            AnchorFit(
                anchor=name,
                beta_a=beta_a.beta,
                beta_b=beta_b.beta,
                r_squared_a=beta_a.r_squared,
                r_squared_b=beta_b.r_squared,
                joint_explained=(beta_a.r_squared + beta_b.r_squared) / 2.0,
            )
        )
    return tuple(sorted(fits, key=lambda fit: fit.joint_explained, reverse=True))
