"""Property and edge-case tests for scale-invariant Lab features and copula."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

import numpy as np
import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from qap.policy.lab_settings import LabSettings, SignalMethod
from qap.policy.lab_signals import signal_path
from qap.relationship.lab_copula import rolling_spread_copula
from qap.relationship.lab_features import hedge_residual, kalman_hedge
from qap.relationship.pair_measurements import Floats

HedgeKind = Literal["ratio", "ols", "tls", "kalman"]

_SCALE_STRATEGY = st.floats(
    min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False
)


def _base_series(size: int = 260, seed: int = 77) -> tuple[Floats, Floats, Floats]:
    rng = np.random.default_rng(seed)
    anchor = 100.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, size)))
    log_anc = np.log(anchor) - np.log(anchor[0])
    a = 50.0 * np.exp(1.1 * log_anc + rng.normal(0.0, 0.02, size))
    b = 80.0 * np.exp(0.9 * log_anc + rng.normal(0.0, 0.02, size))
    return a, b, anchor


_BASE_A, _BASE_B, _BASE_ANCHOR = _base_series()


@pytest.mark.parametrize("method", ["ratio", "ols", "tls", "kalman"])
@hyp_settings(max_examples=20, deadline=None)
@given(scale_a=_SCALE_STRATEGY, scale_b=_SCALE_STRATEGY)
def test_hedge_residual_is_scale_invariant(
    method: HedgeKind, scale_a: float, scale_b: float
) -> None:
    baseline = hedge_residual(_BASE_A, _BASE_B, window=40, method=method)
    scaled = hedge_residual(
        _BASE_A * scale_a, _BASE_B * scale_b, window=40, method=method
    )
    np.testing.assert_allclose(scaled, baseline, rtol=1e-7, atol=1e-7, equal_nan=True)


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
@hyp_settings(max_examples=10, deadline=None)
@given(
    scale_a=_SCALE_STRATEGY,
    scale_b=_SCALE_STRATEGY,
    scale_anchor=_SCALE_STRATEGY,
)
def test_signal_path_is_scale_invariant(
    method: SignalMethod,
    hedge_method: HedgeKind,
    use_anchor: bool,
    scale_a: float,
    scale_b: float,
    scale_anchor: float,
) -> None:
    cfg = LabSettings(
        method=method,
        hedge_method=hedge_method,
        lookback=70,
        fast_window=8,
        slow_window=24,
    )
    anc = _BASE_ANCHOR if use_anchor else None
    baseline = signal_path(_BASE_A, _BASE_B, cfg, anc)
    scaled = signal_path(
        _BASE_A * scale_a,
        _BASE_B * scale_b,
        cfg,
        (_BASE_ANCHOR * scale_anchor) if use_anchor else None,
    )
    assert baseline.available is True
    assert scaled.available is True
    np.testing.assert_allclose(
        scaled.values, baseline.values, rtol=1e-7, atol=1e-7, equal_nan=True
    )
    np.testing.assert_array_equal(scaled.preference, baseline.preference)


def test_kalman_hedge_preserves_strict_causality_and_intercept() -> None:
    log_a = np.log(_BASE_A)
    log_b = np.log(_BASE_B)
    full = kalman_hedge(log_a, log_b)
    for cutoff in (50, 120, 200):
        prefix = kalman_hedge(log_a[:cutoff], log_b[:cutoff])
        np.testing.assert_allclose(prefix.beta, full.beta[:cutoff], rtol=0, atol=1e-12)
        np.testing.assert_allclose(
            prefix.intercept, full.intercept[:cutoff], rtol=0, atol=1e-12
        )
        np.testing.assert_allclose(
            prefix.standard_error, full.standard_error[:cutoff], rtol=0, atol=1e-12
        )


@pytest.mark.parametrize("method", ["ols", "tls", "kalman"])
def test_hedge_residual_handles_flat_second_leg(method: HedgeKind) -> None:
    flat_b = np.full_like(_BASE_A, 100.0)
    res = hedge_residual(_BASE_A, flat_b, window=40, method=method)
    assert np.isfinite(res[40:]).all()


def test_rolling_spread_copula_refuses_invalid_inputs() -> None:
    assert rolling_spread_copula(_BASE_A, _BASE_B, window=59) is None
    assert rolling_spread_copula(_BASE_A[:80], _BASE_B[:80], window=80) is None
    assert rolling_spread_copula(_BASE_A, _BASE_B[:-1], window=60) is None
    assert (
        rolling_spread_copula(_BASE_A, _BASE_B, window=60, anchor=_BASE_ANCHOR[:-1])
        is None
    )


def test_lab_settings_s1_defaults_and_copula_band_validation() -> None:
    defaults = LabSettings()
    assert defaults.rotation_size == Decimal("0.5")
    assert defaults.copula_exit_band == 0.15
    assert defaults.trend_deadband == 0.002

    with pytest.raises(ValidationError):
        LabSettings(copula_probability=0.35, copula_exit_band=0.15)
    with pytest.raises(ValidationError):
        LabSettings(copula_probability=0.40, copula_exit_band=0.15)
