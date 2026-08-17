from datetime import UTC, datetime, timedelta, timezone

import pytest

from qap.market import (
    BarInterval,
    BarSeriesValidationError,
    MarketBar,
    VenueInstrument,
    validate_bar_series,
)
from qap.portfolio import AssetId


def _instrument(symbol: str = "BTCUSDT") -> VenueInstrument:
    base = AssetId("BTC" if symbol == "BTCUSDT" else "ETH")
    return VenueInstrument(
        venue="binance",
        venue_symbol=symbol,
        base=base,
        quote=AssetId("USDT"),
    )


def _bar(
    hour: int,
    *,
    instrument: VenueInstrument | None = None,
    interval: BarInterval | None = None,
) -> MarketBar:
    return MarketBar(
        instrument=instrument or _instrument(),
        interval=interval or BarInterval("1h"),
        candle_open_time=datetime(2024, 1, 1, hour, tzinfo=UTC),
        open=100.0 + hour,
        high=110.0 + hour,
        low=90.0 + hour,
        close=105.0 + hour,
        volume=10.0 + hour,
    )


def test_validate_bar_series_preserves_order_and_metadata() -> None:
    bars = [_bar(10), _bar(11), _bar(12)]

    series = validate_bar_series(bars)

    assert series.instrument == bars[0].instrument
    assert series.interval == BarInterval("1h")
    assert series.bars == tuple(bars)
    assert series.timestamps == tuple(bar.candle_open_time for bar in bars)


def test_validate_bar_series_rejects_empty_input() -> None:
    with pytest.raises(BarSeriesValidationError, match="at least one bar"):
        validate_bar_series([])


def test_validate_bar_series_rejects_duplicate_timestamps() -> None:
    with pytest.raises(BarSeriesValidationError, match="duplicate.*10:00:00"):
        validate_bar_series([_bar(10), _bar(10)])


def test_validate_bar_series_rejects_out_of_order_timestamps() -> None:
    with pytest.raises(BarSeriesValidationError, match="out of order.*10:00:00"):
        validate_bar_series([_bar(11), _bar(10)])


def test_validate_bar_series_rejects_internal_gaps() -> None:
    with pytest.raises(
        BarSeriesValidationError,
        match="gap.*expected.*11:00:00.*got.*12:00:00",
    ):
        validate_bar_series([_bar(10), _bar(12)])


def test_validate_bar_series_rejects_mixed_instruments_or_intervals() -> None:
    with pytest.raises(BarSeriesValidationError, match="instrument"):
        validate_bar_series([_bar(10), _bar(11, instrument=_instrument("ETHUSDT"))])

    with pytest.raises(BarSeriesValidationError, match="interval"):
        validate_bar_series([_bar(10), _bar(11, interval=BarInterval("30m"))])


def test_history_through_exposes_only_bars_completed_by_decision_time() -> None:
    series = validate_bar_series([_bar(9), _bar(10), _bar(11), _bar(12)])

    history = series.history_through(datetime(2024, 1, 1, 11, tzinfo=UTC))

    assert history.as_of == datetime(2024, 1, 1, 11, tzinfo=UTC)
    assert [bar.candle_open_time.hour for bar in history.bars] == [9, 10]
    assert all(bar.bar_end_exclusive <= history.as_of for bar in history.bars)


def test_history_through_can_be_empty_without_exposing_future_bars() -> None:
    series = validate_bar_series([_bar(10), _bar(11)])

    history = series.history_through(datetime(2024, 1, 1, 10, tzinfo=UTC))

    assert history.bars == ()


def test_history_through_normalizes_zero_offset_decision_time_to_utc() -> None:
    zero_offset = timezone(timedelta(0), name="ZERO")
    series = validate_bar_series([_bar(10)])

    history = series.history_through(datetime(2024, 1, 1, 11, tzinfo=zero_offset))

    assert history.as_of.tzinfo is UTC


@pytest.mark.parametrize(
    "decision_time",
    [
        datetime(2024, 1, 1, 11),
        datetime(2024, 1, 1, 11, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_history_through_requires_utc_decision_time(decision_time: datetime) -> None:
    series = validate_bar_series([_bar(10)])

    with pytest.raises(ValueError, match="UTC"):
        series.history_through(decision_time)
