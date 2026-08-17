import math
from datetime import UTC, datetime, timedelta

import pytest

from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId

BTC = AssetId("BTC")
ETH = AssetId("ETH")
SOL = AssetId("SOL")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, 10, tzinfo=UTC)


def _series(asset: AssetId, closes: tuple[float, ...]):
    instrument = VenueInstrument(
        venue="fixture",
        venue_symbol=f"{asset.key}USDT",
        base=asset,
        quote=USDT,
    )
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + position * INTERVAL.duration,
                source_close_time=(
                    START
                    + (position + 1) * INTERVAL.duration
                    - timedelta(milliseconds=1)
                ),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1.0,
            )
            for position, close in enumerate(closes)
        )
    )


def _aligned(
    btc: tuple[float, ...],
    eth: tuple[float, ...],
    sol: tuple[float, ...] | None = None,
):
    series = [_series(BTC, btc), _series(ETH, eth)]
    if sol is not None:
        series.append(_series(SOL, sol))
    return align_bar_series(series)


def test_cross_sectional_relative_scores_match_three_asset_hand_calculation() -> None:
    from qap.relationship.models import cross_sectional_relative_observation

    observation = cross_sectional_relative_observation(
        _aligned(
            (100.0, 110.0, 121.0),
            (100.0, 100.0, 100.0),
            (100.0, 90.0, 81.0),
        ),
        basket=(BTC, ETH, SOL),
        window_returns=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    btc_return = math.log(1.1)
    eth_return = 0.0
    sol_return = math.log(0.9)
    common = (btc_return + eth_return + sol_return) / 3.0

    assert observation.status.value == "valid"
    assert observation.model_id == "cross_sectional_relative_log_return"
    assert observation.model_version == "1"
    assert observation.coverage_returns == 2
    assert observation.pair_independence_limited is False
    assert observation.common_mode_returns == pytest.approx((common, common))
    assert observation.scores[BTC] == pytest.approx(2.0 * (btc_return - common))
    assert observation.scores[ETH] == pytest.approx(2.0 * (eth_return - common))
    assert observation.scores[SOL] == pytest.approx(2.0 * (sol_return - common))
    assert sum(observation.scores.values()) == pytest.approx(0.0, abs=1e-15)


def test_cross_sectional_relative_ignores_incomplete_future_bar() -> None:
    from qap.relationship.models import cross_sectional_relative_observation

    baseline = cross_sectional_relative_observation(
        _aligned(
            (100.0, 110.0, 121.0),
            (100.0, 100.0, 100.0),
            (100.0, 90.0, 81.0),
        ),
        basket=(BTC, ETH, SOL),
        window_returns=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )
    with_future = cross_sectional_relative_observation(
        _aligned(
            (100.0, 110.0, 121.0, 1000.0),
            (100.0, 100.0, 100.0, 1.0),
            (100.0, 90.0, 81.0, 500.0),
        ),
        basket=(BTC, ETH, SOL),
        window_returns=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert with_future.scores == baseline.scores
    assert with_future.input_fingerprint == baseline.input_fingerprint


def test_cross_sectional_relative_requires_full_declared_return_window() -> None:
    from qap.relationship.models import cross_sectional_relative_observation

    observation = cross_sectional_relative_observation(
        _aligned((100.0, 110.0), (100.0, 100.0), (100.0, 90.0)),
        basket=(BTC, ETH, SOL),
        window_returns=2,
        as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
    )

    assert observation.status.value == "insufficient_history"
    assert observation.coverage_returns == 1
    assert observation.scores == {}


def test_two_asset_common_mode_is_explicitly_marked_as_pair_degenerate() -> None:
    from qap.relationship.models import cross_sectional_relative_observation

    observation = cross_sectional_relative_observation(
        _aligned((100.0, 110.0, 121.0), (100.0, 90.0, 81.0)),
        basket=(BTC, ETH),
        window_returns=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert observation.status.value == "valid"
    assert observation.pair_independence_limited is True
    assert observation.scores[BTC] == pytest.approx(-observation.scores[ETH])


def test_cross_sectional_relative_rejects_duplicate_or_unavailable_basket_assets() -> (
    None
):
    from qap.relationship.models import cross_sectional_relative_observation

    aligned = _aligned((100.0, 110.0, 121.0), (100.0, 100.0, 100.0))
    with pytest.raises(ValueError, match="unique"):
        cross_sectional_relative_observation(
            aligned,
            basket=(BTC, BTC),
            window_returns=2,
            as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="exactly one leg"):
        cross_sectional_relative_observation(
            aligned,
            basket=(BTC, SOL),
            window_returns=2,
            as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        )
