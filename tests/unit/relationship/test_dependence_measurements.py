"""Dependence measurements recover planted structure and refuse thin or flat data."""

import numpy as np
import pytest

from qap.relationship.dependence_measurements import (
    copula_tails,
    granger,
    kalman_reading,
    rolling_dependence,
)
from qap.relationship.lab_copula import copula_features
from qap.relationship.lab_features import rolling_correlation
from qap.relationship.pair_measurements import MeasurementError

RNG_SEED = 20261027


def rng() -> np.random.Generator:
    return np.random.default_rng(RNG_SEED)


def test_kalman_tracks_a_planted_hedge_slope() -> None:
    generator = rng()
    log_b = np.cumsum(0.01 * generator.standard_normal(2_000))
    log_a = 0.2 + 1.5 * log_b + 0.002 * generator.standard_normal(2_000)
    result = kalman_reading(log_a, log_b)
    assert result is not None
    assert result.beta == pytest.approx(1.5, abs=0.1)
    assert result.standard_error > 0
    assert abs(result.beta_change) < 0.2


def test_kalman_refuses_thin_or_flat_data() -> None:
    assert kalman_reading(np.zeros(10), np.zeros(10)) is None
    assert kalman_reading(rng().standard_normal(100), np.zeros(100)) is None
    with pytest.raises(MeasurementError):
        kalman_reading(np.zeros(100), np.zeros(99))


def test_granger_finds_planted_direction_only() -> None:
    generator = rng()
    leader = generator.standard_normal(3_000)
    follower = np.r_[0.0, 0.0, 0.7 * leader[:-2]] + 0.5 * generator.standard_normal(
        3_000
    )
    result = granger(leader, follower)
    assert result is not None
    assert result.a_to_b.passes
    assert result.a_to_b.lag_bars >= 2
    assert not result.b_to_a.passes
    assert result.max_lag == 4
    assert result.observations == 3_000


def test_granger_independent_noise_does_not_pass() -> None:
    generator = rng()
    result = granger(generator.standard_normal(2_000), generator.standard_normal(2_000))
    assert result is not None
    assert not result.a_to_b.passes
    assert not result.b_to_a.passes
    assert 0.0 <= result.a_to_b.p_value <= 1.0


def test_granger_refuses_thin_flat_or_malformed_data() -> None:
    assert granger(np.ones(50), np.ones(50)) is None
    assert granger(np.ones(200), rng().standard_normal(200)) is None
    with pytest.raises(MeasurementError):
        granger(np.ones(200), np.ones(199))
    with pytest.raises(MeasurementError):
        granger(np.ones(200), np.ones(200), max_lag=0)


def test_copula_tails_see_joint_crashes() -> None:
    generator = rng()
    shared = generator.standard_normal(1_500)
    # Common heavy-tailed shocks give both legs joint extremes.
    shocks = generator.standard_t(2, 1_500) * 0.02
    returns_a = 0.01 * shared + shocks + 0.004 * generator.standard_normal(1_500)
    returns_b = 0.01 * shared + shocks + 0.004 * generator.standard_normal(1_500)
    close_a = 100 * np.exp(np.r_[0.0, np.cumsum(returns_a)])
    close_b = 50 * np.exp(np.r_[0.0, np.cumsum(returns_b)])
    result = copula_tails(close_a, close_b)
    assert result is not None
    assert result.family != "indep"
    assert max(result.lower_tail, result.upper_tail) > 0.2
    assert result.observations == close_a.size - 2


def test_copula_tails_refuse_thin_or_flat_data() -> None:
    assert copula_tails(np.ones(50), np.ones(50)) is None
    prices = np.exp(np.cumsum(0.01 * rng().standard_normal(300)))
    assert copula_tails(prices, np.ones(300)) is None


def test_rolling_dependence_reports_latest_and_range() -> None:
    generator = rng()
    driver = generator.standard_normal(1_000)
    early = generator.standard_normal(500)
    late = 0.9 * driver[500:] + 0.3 * generator.standard_normal(500)
    result = rolling_dependence(driver, np.r_[early, late], window=100)
    assert result is not None
    assert result.window_bars == 100
    assert result.latest > 0.8
    assert result.low < 0.3
    assert result.low <= result.latest <= result.high <= 1.0


def test_rolling_dependence_clips_window_and_refuses_thin_data() -> None:
    generator = rng()
    a, b = generator.standard_normal(50), generator.standard_normal(50)
    result = rolling_dependence(a, b, window=500)
    assert result is not None and result.window_bars == 50
    assert rolling_dependence(a[:10], b[:10], window=500) is None


def test_flat_window_correlation_is_undefined_not_clipped() -> None:
    a = np.r_[np.zeros(30), rng().standard_normal(30)]
    b = rng().standard_normal(60)
    values = rolling_correlation(a, b, 20)
    assert np.isnan(values[:30]).all()
    assert np.isfinite(values[-1])
    assert rolling_dependence(b, np.r_[b[:40], np.zeros(20)], window=20) is None


def _walk(n: int) -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(7)
    x, y = generator.normal(0, 0.01, n), generator.normal(0, 0.01, n)
    a = 100 * np.exp(np.cumsum(x))
    b = 50 * np.exp(np.cumsum(0.6 * x + 0.8 * y))
    return a, b


def test_copula_tails_caps_fit_to_latest_4000_returns() -> None:
    close_a, close_b = _walk(10_000)
    result = copula_tails(close_a, close_b)
    assert result is not None
    assert result.observations == 4000


def test_copula_tails_matches_full_fit_below_cap() -> None:
    close_a, close_b = _walk(3_000)
    result = copula_tails(close_a, close_b)
    direct = copula_features(close_a, close_b, training=close_a.size - 2)
    assert result is not None and direct is not None
    assert result.family == direct.family
    assert result.lower_tail == direct.lower_tail
    assert result.upper_tail == direct.upper_tail
    assert result.observations == direct.training_observations
