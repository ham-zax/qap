"""Pure causal Lab preferences, separate from all owned inventory and fills."""

from dataclasses import dataclass

import numpy as np

from qap.policy.lab_settings import LabSettings
from qap.relationship.lab_copula import copula_features
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
        fast, _ = rolling_mean_std(a / b, settings.fast_window)
        slow, _ = rolling_mean_std(a / b, settings.slow_window)
        values = fast / slow - 1
        upper, lower, unit = 0.0, 0.0, "relative MA spread"
    elif settings.method == "copula":
        fitted = copula_features(a, b, settings.lookback)
        if fitted is None:
            return LabSignal(
                values,
                preference,
                "conditional probability",
                1,
                0,
                False,
                "Not enough varying data for a copula fit.",
            )
        values = fitted.probability_a
        lower, upper, unit = (
            settings.copula_probability,
            1 - settings.copula_probability,
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
        fit = min(settings.lookback, driver.size)
        variance = float(np.var(driver[:fit]))
        if fit < settings.lookback or variance <= 1e-20:
            return LabSignal(
                values,
                preference,
                "anchor return",
                0,
                0,
                False,
                "Not enough anchor movement to fit a lead-lag signal.",
            )
        beta_a = float(np.cov(returns_a[:fit], driver[:fit], ddof=0)[0, 1] / variance)
        beta_b = float(np.cov(returns_b[:fit], driver[:fit], ddof=0)[0, 1] / variance)
        values[fit + 1 :] = ((beta_a - beta_b) * driver - (returns_a - returns_b))[fit:]
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
            state = 1.0 if value > 0 else -1.0 if value < 0 else 0.0
        elif settings.method == "lead_lag":
            state = 1.0 if value >= upper else -1.0 if value <= lower else 0.0
        elif settings.method == "copula":
            state = 1.0 if value <= lower else -1.0 if value >= upper else 0.0
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
