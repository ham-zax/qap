"""Pure causal Lab preferences, separate from all owned inventory and fills."""

from dataclasses import dataclass

import numpy as np

from qap.policy.lab_settings import LabSettings
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


def signal_path(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None = None
) -> LabSignal:
    values = np.full(a.size, np.nan)
    preference = np.full(a.size, np.nan)
    upper, lower, unit = settings.entry, -settings.entry, "z-score"
    if settings.method == "zscore":
        residual = hedge_residual(
            a, b, window=settings.lookback, method=settings.hedge_method
        )
        values = trailing_zscore(residual, settings.lookback)
    elif settings.method == "trend":
        lr = (np.log(a) - np.log(a[0])) - (np.log(b) - np.log(b[0]))
        fast, _ = rolling_mean_std(lr, settings.fast_window)
        slow, _ = rolling_mean_std(lr, settings.slow_window)
        values = fast - slow
        upper, lower, unit = (
            settings.trend_deadband,
            -settings.trend_deadband,
            "log-ratio MA spread",
        )
    elif settings.method == "copula":
        prob_a = rolling_spread_copula(a, b, window=settings.lookback, anchor=anchor)
        if prob_a is None or not np.isfinite(prob_a).any():
            return LabSignal(
                values,
                preference,
                "conditional probability",
                1,
                0,
                False,
                "Not enough varying data for a copula fit.",
            )
        values = prob_a
        lower, upper, unit = (
            settings.copula_probability,
            1.0 - settings.copula_probability,
            "conditional probability",
        )
    else:
        if anchor is None or anchor.shape != a.shape:
            return LabSignal(
                values,
                preference,
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
                preference,
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
                preference,
                "anchor return",
                0,
                0,
                False,
                "Not enough anchor movement to fit a lead-lag signal.",
            )
        upper, lower, unit = (
            settings.anchor_threshold,
            -settings.anchor_threshold,
            "anchor-relative return",
        )
    state = 0.0
    for index, value in enumerate(values):
        if not np.isfinite(value):
            continue
        if settings.method == "trend":
            if value >= upper:
                state = 1.0
            elif value <= lower:
                state = -1.0
            elif (state > 0 and value <= 0.0) or (state < 0 and value >= 0.0):
                state = 0.0
        elif settings.method == "lead_lag":
            if value >= upper:
                state = 1.0
            elif value <= lower:
                state = -1.0
            elif abs(value) <= 0.25 * settings.anchor_threshold:
                state = 0.0
        elif settings.method == "copula":
            if value <= lower:
                state = 1.0
            elif value >= upper:
                state = -1.0
            elif abs(value - 0.5) <= settings.copula_exit_band:
                state = 0.0
        else:
            if value >= upper:
                state = -1.0
            elif value <= lower:
                state = 1.0
            elif abs(value) <= settings.exit:
                state = 0.0
        preference[index] = state
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
