"""Declarative registry of pure causal Lab strategy signal builders."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from qap.policy.lab_settings import LabSettings, SignalMethod
from qap.relationship.lab_copula import rolling_spread_copula
from qap.relationship.lab_features import hedge_residual, trailing_zscore
from qap.relationship.pair_measurements import Floats, rolling_mean_std


@dataclass(frozen=True, slots=True)
class LabSignal:
    values: Floats
    preference: Floats
    unit: str
    upper: float
    lower: float
    available: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StrategySpec:
    method: SignalMethod
    label: str
    requires_1m: bool
    requires_anchor: bool
    build: Callable[[Floats, Floats, LabSettings, Floats | None], LabSignal]


def _step_preferences(
    values: Floats,
    next_state: Callable[[float, float], float],
) -> Floats:
    preference = np.full(values.size, np.nan)
    state = 0.0
    for index, value in enumerate(values):
        if not np.isfinite(value):
            continue
        state = next_state(state, float(value))
        preference[index] = state
    return preference


def _finalize_signal(
    values: Floats,
    unit: str,
    upper: float,
    lower: float,
    next_state: Callable[[float, float], float],
) -> LabSignal:
    preference = _step_preferences(values, next_state)
    available = bool(np.isfinite(preference).any())
    return LabSignal(
        values,
        preference,
        unit,
        upper,
        lower,
        available,
        None if available else "Not enough history for the selected method.",
    )


def _build_zscore(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None
) -> LabSignal:
    del anchor
    residual = hedge_residual(
        a, b, window=settings.lookback, method=settings.hedge_method
    )
    values = trailing_zscore(residual, settings.lookback)
    upper, lower = settings.entry, -settings.entry

    def step(state: float, value: float) -> float:
        if value >= upper:
            return -1.0
        if value <= lower:
            return 1.0
        if abs(value) <= settings.exit:
            return 0.0
        return state

    return _finalize_signal(values, "z-score", upper, lower, step)


def _build_trend(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None
) -> LabSignal:
    del anchor
    lr = (np.log(a) - np.log(a[0])) - (np.log(b) - np.log(b[0]))
    fast, _ = rolling_mean_std(lr, settings.fast_window)
    slow, _ = rolling_mean_std(lr, settings.slow_window)
    values = fast - slow
    upper, lower = settings.trend_deadband, -settings.trend_deadband

    def step(state: float, value: float) -> float:
        if value >= upper:
            return 1.0
        if value <= lower:
            return -1.0
        if (state > 0 and value <= 0.0) or (state < 0 and value >= 0.0):
            return 0.0
        return state

    return _finalize_signal(values, "log-ratio MA spread", upper, lower, step)


def _build_copula(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None
) -> LabSignal:
    prob_a = rolling_spread_copula(a, b, window=settings.lookback, anchor=anchor)
    if prob_a is None or not np.isfinite(prob_a).any():
        empty = np.full(a.size, np.nan)
        return LabSignal(
            empty,
            empty.copy(),
            "conditional probability",
            1,
            0,
            False,
            "Not enough varying data for a copula fit.",
        )
    lower, upper = settings.copula_probability, 1.0 - settings.copula_probability

    def step(state: float, value: float) -> float:
        if value <= lower:
            return 1.0
        if value >= upper:
            return -1.0
        if abs(value - 0.5) <= settings.copula_exit_band:
            return 0.0
        return state

    return _finalize_signal(prob_a, "conditional probability", upper, lower, step)


def _build_lead_lag(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None
) -> LabSignal:
    values = np.full(a.size, np.nan)
    empty_pref = np.full(a.size, np.nan)
    if anchor is None or anchor.shape != a.shape:
        return LabSignal(
            values,
            empty_pref,
            "anchor return",
            settings.anchor_threshold,
            -settings.anchor_threshold,
            False,
            "Choose an anchor with aligned one-minute history.",
        )
    returns_a, returns_b, driver = (
        np.diff(np.log(a)),
        np.diff(np.log(b)),
        np.diff(np.log(anchor)),
    )
    if driver.size < settings.lookback + 1:
        return LabSignal(
            values,
            empty_pref,
            "anchor return",
            0,
            0,
            False,
            "Not enough anchor movement to fit a lead-lag signal.",
        )
    for r_idx in range(settings.lookback, driver.size):
        w = slice(r_idx - settings.lookback, r_idx)
        var_d = float(np.var(driver[w]))
        if var_d <= 1e-20:
            continue
        beta_a = float(np.cov(returns_a[w], driver[w], ddof=0)[0, 1] / var_d)
        beta_b = float(np.cov(returns_b[w], driver[w], ddof=0)[0, 1] / var_d)
        values[r_idx + 1] = (beta_a - beta_b) * driver[r_idx] - (
            returns_a[r_idx] - returns_b[r_idx]
        )
    if not np.isfinite(values).any():
        return LabSignal(
            values,
            empty_pref,
            "anchor return",
            0,
            0,
            False,
            "Not enough anchor movement to fit a lead-lag signal.",
        )
    upper, lower = settings.anchor_threshold, -settings.anchor_threshold

    def step(state: float, value: float) -> float:
        if value >= upper:
            return 1.0
        if value <= lower:
            return -1.0
        if abs(value) <= 0.25 * settings.anchor_threshold:
            return 0.0
        return state

    return _finalize_signal(values, "anchor-relative return", upper, lower, step)


STRATEGY_REGISTRY: dict[SignalMethod, StrategySpec] = {
    "zscore": StrategySpec(
        method="zscore",
        label="Mean Reversion (Z-Score)",
        requires_1m=False,
        requires_anchor=False,
        build=_build_zscore,
    ),
    "copula": StrategySpec(
        method="copula",
        label="Spread Copula",
        requires_1m=False,
        requires_anchor=False,
        build=_build_copula,
    ),
    "trend": StrategySpec(
        method="trend",
        label="Ratio Trend (MA)",
        requires_1m=False,
        requires_anchor=False,
        build=_build_trend,
    ),
    "lead_lag": StrategySpec(
        method="lead_lag",
        label="Anchor Lead-Lag (1m)",
        requires_1m=True,
        requires_anchor=True,
        build=_build_lead_lag,
    ),
}
