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
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
INSTRUMENT = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)
START = datetime(2024, 1, 1, 10, tzinfo=UTC)


def _aligned(closes: tuple[float, ...]):
    bars = tuple(
        MarketBar(
            instrument=INSTRUMENT,
            interval=INTERVAL,
            candle_open_time=START + position * INTERVAL.duration,
            source_close_time=(
                START + (position + 1) * INTERVAL.duration - timedelta(milliseconds=1)
            ),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1.0,
        )
        for position, close in enumerate(closes)
    )
    return align_bar_series((validate_bar_series(bars),)).series[0]


def test_slow_log_momentum_matches_hand_calculated_completed_bar_score() -> None:
    from qap.experiment.momentum import MomentumEvidenceStatus, slow_log_momentum

    evidence = slow_log_momentum(
        _aligned((100.0, 110.0, 121.0)),
        lookback_bars=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert evidence.status is MomentumEvidenceStatus.VALID
    assert evidence.asset == BTC
    assert evidence.lookback_bars == 2
    assert evidence.current_timestamp == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert evidence.reference_timestamp == datetime(2024, 1, 1, 10, tzinfo=UTC)
    assert evidence.score == pytest.approx(math.log(121.0 / 100.0))


def test_slow_log_momentum_never_uses_an_incomplete_future_bar() -> None:
    from qap.experiment.momentum import slow_log_momentum

    evidence = slow_log_momentum(
        _aligned((100.0, 110.0, 121.0, 1000.0)),
        lookback_bars=2,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert evidence.current_timestamp == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert evidence.score == pytest.approx(math.log(121.0 / 100.0))


def test_slow_log_momentum_reports_insufficient_history_without_fallback() -> None:
    from qap.experiment.momentum import MomentumEvidenceStatus, slow_log_momentum

    evidence = slow_log_momentum(
        _aligned((100.0, 110.0, 121.0)),
        lookback_bars=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert evidence.status is MomentumEvidenceStatus.INSUFFICIENT_HISTORY
    assert evidence.score is None
    assert evidence.reference_timestamp is None
    assert evidence.current_timestamp == datetime(2024, 1, 1, 12, tzinfo=UTC)


def test_slow_log_momentum_rejects_non_positive_lookback() -> None:
    from qap.experiment.momentum import slow_log_momentum

    with pytest.raises(ValueError, match="lookback_bars must be positive"):
        slow_log_momentum(
            _aligned((100.0, 110.0)),
            lookback_bars=0,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
        )
