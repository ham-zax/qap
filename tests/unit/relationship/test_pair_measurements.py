"""Pair and anchor measurements recover planted structure and refuse thin data."""

import numpy as np
import pytest

from qap.relationship.anchor_measurements import (
    anchor_beta,
    lead_lag,
    rank_anchors,
)
from qap.relationship.pair_measurements import (
    MeasurementError,
    cointegration,
    correlation,
    half_life,
    hedge_ratio,
    hurst,
    log_returns,
    percentile_of_last,
    ratio_bands,
    regime,
)

RNG_SEED = 20261003


def rng() -> np.random.Generator:
    return np.random.default_rng(RNG_SEED)


def ou_path(n: int, phi: float, sigma: float = 0.01) -> np.ndarray:
    generator = rng()
    values = np.zeros(n)
    for index in range(1, n):
        values[index] = phi * values[index - 1] + sigma * generator.standard_normal()
    return values


def test_correlation_matches_planted_dependence() -> None:
    generator = rng()
    driver = generator.standard_normal(2_000)
    follower = 0.8 * driver + 0.6 * generator.standard_normal(2_000)
    result = correlation(driver, follower)
    assert result is not None
    assert result.pearson == pytest.approx(0.8, abs=0.04)
    assert result.spearman == pytest.approx(0.8, abs=0.05)
    assert 0.5 < result.kendall < result.spearman
    assert result.observations == 2_000


def test_correlation_refuses_thin_or_constant_data() -> None:
    assert correlation(np.ones(10), np.ones(10)) is None
    assert correlation(np.ones(100), rng().standard_normal(100)) is None
    with pytest.raises(MeasurementError):
        correlation(np.ones(50), np.ones(49))


def test_half_life_recovers_ar1_speed_and_flags_random_walks() -> None:
    phi = 0.95
    result = half_life(ou_path(5_000, phi))
    assert result is not None and result.reverting and result.bars is not None
    assert result.bars == pytest.approx(-np.log(2) / np.log(phi), rel=0.25)
    walk = half_life(np.cumsum(rng().standard_normal(5_000)))
    assert walk is not None
    assert walk.bars is None or walk.bars > 500
    assert half_life(np.ones(10)) is None


def test_hurst_separates_reverting_random_and_trending_paths() -> None:
    reverting = hurst(ou_path(8_000, 0.90))
    random_walk = hurst(np.cumsum(rng().standard_normal(8_000)))
    # Persistent increments (momentum) are what makes a path trend; a constant
    # drift is removed by the per-lag deviation and would read as random.
    trending = hurst(np.cumsum(ou_path(8_000, 0.95)))
    assert reverting is not None and reverting.reading == "reverting"
    assert random_walk is not None and random_walk.reading == "random"
    assert trending is not None and trending.reading == "trending"
    assert reverting.exponent < random_walk.exponent < trending.exponent


def test_cointegration_passes_for_shared_trend_and_fails_for_independent_walks() -> (
    None
):
    generator = rng()
    trend = np.cumsum(generator.standard_normal(3_000)) * 0.01
    log_b = trend
    log_a = 1.3 * trend + ou_path(3_000, 0.8, sigma=0.01) + 0.5
    related = cointegration(log_a, log_b)
    assert related is not None and related.passes and related.p_value < 0.01
    independent = cointegration(
        np.cumsum(generator.standard_normal(3_000)) * 0.01,
        np.cumsum(generator.standard_normal(3_000)) * 0.01,
    )
    assert independent is not None and not independent.passes
    assert cointegration(np.arange(1.0, 30.0), np.arange(1.0, 30.0)) is None


def test_hedge_ratio_recovers_slope_and_flags_instability() -> None:
    generator = rng()
    log_b = np.cumsum(generator.standard_normal(4_000)) * 0.01
    log_a = 1.5 * log_b + 0.002 * generator.standard_normal(4_000)
    stable = hedge_ratio(log_a, log_b)
    assert stable is not None and stable.stable
    assert stable.ols == pytest.approx(1.5, abs=0.05)
    assert stable.tls == pytest.approx(1.5, abs=0.05)
    drifting = np.concatenate(
        (1.0 * log_b[:2_000], 1.0 * log_b[2_000] + 3.0 * (log_b[2_000:] - log_b[2_000]))
    )
    unstable = hedge_ratio(drifting, log_b)
    assert unstable is not None and not unstable.stable
    assert hedge_ratio(np.ones(500), np.ones(500)) is None


def test_ratio_bands_use_only_trailing_bars() -> None:
    ratio = np.linspace(1.0, 2.0, 200)
    bands = ratio_bands(ratio, lookback=20)
    assert np.isnan(bands.mean[:19]).all() and not np.isnan(bands.mean[19])
    assert bands.mean[19] == pytest.approx(ratio[:20].mean())
    assert bands.std[19] == pytest.approx(ratio[:20].std(ddof=1))
    changed = ratio.copy()
    changed[150:] += 5.0
    later = ratio_bands(changed, lookback=20)
    np.testing.assert_allclose(later.mean[:149], bands.mean[:149])
    with pytest.raises(MeasurementError):
        ratio_bands(ratio, lookback=1)


def test_percentile_and_regime_describe_the_latest_state() -> None:
    assert percentile_of_last(np.array([1.0, 2.0, 3.0, 4.0])) == 100.0
    assert percentile_of_last(np.array([4.0, 3.0, 2.0, 1.0])) == 25.0
    generator = rng()
    quiet = np.cumsum(0.001 * generator.standard_normal(600))
    shock = np.cumsum(
        np.concatenate(
            (
                0.001 * generator.standard_normal(560),
                0.02 * generator.standard_normal(40),
            )
        )
    )
    assert regime(quiet, window=40) is not None
    stressed = regime(shock, window=40)
    assert stressed is not None and stressed.volatility == "stressed"
    ramp = regime(np.linspace(0.0, 1.0, 400), window=40)
    assert ramp is not None and ramp.trend == "trending"
    assert regime(np.ones(10), window=40) is None


def test_lead_lag_finds_the_planted_delay_and_its_stability() -> None:
    generator = rng()
    anchor = generator.standard_normal(3_000)
    coin = np.roll(anchor, 3) + 0.5 * generator.standard_normal(3_000)
    result = lead_lag(coin[10:], anchor[10:], max_lag=8)
    assert result is not None
    assert result.lag_bars == 3 and result.stable and result.correlation > 0.8
    unrelated = lead_lag(generator.standard_normal(3_000), anchor, max_lag=8)
    assert unrelated is not None and abs(unrelated.correlation) < 0.15
    assert lead_lag(coin[:50], anchor[:50], max_lag=8) is None
    with pytest.raises(MeasurementError):
        lead_lag(coin, anchor, max_lag=0)


def test_anchor_beta_and_ranking_prefer_the_real_driver() -> None:
    generator = rng()
    market = generator.standard_normal(2_500)
    noise = generator.standard_normal(2_500)
    returns_a = 1.2 * market + 0.4 * generator.standard_normal(2_500)
    returns_b = 0.7 * market + 0.4 * generator.standard_normal(2_500)
    fit = anchor_beta(returns_a, market)
    assert fit is not None and fit.beta == pytest.approx(1.2, abs=0.05)
    ranking = rank_anchors(
        {
            "binance:BTC": (returns_a, returns_b, market),
            "binance:ADA": (returns_a, returns_b, noise),
            "binance:TOO_SHORT": (returns_a[:20], returns_b[:20], market[:20]),
        }
    )
    assert [row.anchor for row in ranking] == ["binance:BTC", "binance:ADA"]
    assert ranking[0].joint_explained > 0.6 > ranking[1].joint_explained


def test_log_returns_reject_nonpositive_inputs_upstream() -> None:
    assert log_returns(np.array([1.0, 2.0, 4.0])) == pytest.approx(
        [np.log(2.0), np.log(2.0)]
    )


def test_cointegration_returns_none_on_rank_deficient_residual() -> None:
    import warnings

    idx = np.arange(300, dtype=float)
    log_a = np.linspace(1.0, 2.0, 300) + 0.01 * (idx % 4)
    log_b = np.linspace(0.5, 1.0, 300)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert cointegration(log_a, log_b) is None
    assert caught == []


def test_beta_not_equal_to_one_distinguishes_ratio_and_hedge_residuals() -> None:
    from qap.relationship.dependence_measurements import kalman_reading
    from qap.relationship.lab_features import hedge_residual

    rng = np.random.default_rng(20261116)
    n = 400
    log_b = np.linspace(0.0, 2.0, n) + np.cumsum(rng.normal(0.0, 0.01, n))
    # True beta is 2.0 != 1.0, so 1:1 log ratio drifts while OLS/Kalman track beta=2.
    log_a = 2.0 * log_b + rng.normal(0.0, 0.02, n)
    close_a, close_b = 100.0 * np.exp(log_a), 50.0 * np.exp(log_b)

    ratio_hl = half_life(log_a - log_b)
    ols_res = hedge_residual(close_a, close_b, window=80, method="ols")[100:]
    kalman_res = hedge_residual(close_a, close_b, window=80, method="kalman")[100:]
    ols_hl = half_life(ols_res)
    kalman = kalman_reading(log_a, log_b)

    assert ratio_hl is None or not ratio_hl.reverting or (ratio_hl.bars or 0.0) > 50.0
    assert ols_hl is not None and ols_hl.reverting and (ols_hl.bars or 999.0) < 5.0
    assert kalman is not None and kalman.beta == pytest.approx(2.0, abs=0.15)
    assert float(np.std(kalman_res)) < 0.1 * float(np.std((log_a - log_b)[100:]))
