from datetime import UTC, datetime, timedelta, timezone

import pytest

from qap.market import BarInterval, MarketBar, VenueInstrument
from qap.portfolio import AssetId


def _instrument() -> VenueInstrument:
    return VenueInstrument(
        venue="binance",
        venue_symbol="BTCUSDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )


def _bar(**overrides: object) -> MarketBar:
    values: dict[str, object] = {
        "instrument": _instrument(),
        "interval": BarInterval("1h"),
        "candle_open_time": datetime(2024, 1, 1, 10, tzinfo=UTC),
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 12.5,
        "source_close_time": datetime(
            2024,
            1,
            1,
            10,
            59,
            59,
            999000,
            tzinfo=UTC,
        ),
    }
    values.update(overrides)
    return MarketBar(**values)  # type: ignore[arg-type]


def test_market_bar_preserves_source_time_and_internal_completion_boundary() -> None:
    bar = _bar()

    assert bar.candle_open_time == datetime(2024, 1, 1, 10, tzinfo=UTC)
    assert bar.source_close_time == datetime(
        2024,
        1,
        1,
        10,
        59,
        59,
        999000,
        tzinfo=UTC,
    )
    assert bar.bar_end_exclusive == datetime(2024, 1, 1, 11, tzinfo=UTC)


def test_market_bar_normalizes_zero_offset_timestamps_to_utc() -> None:
    zero_offset = timezone(timedelta(0), name="ZERO")

    bar = _bar(
        candle_open_time=datetime(2024, 1, 1, 10, tzinfo=zero_offset),
        source_close_time=datetime(
            2024,
            1,
            1,
            10,
            59,
            59,
            999000,
            tzinfo=zero_offset,
        ),
    )

    assert bar.candle_open_time.tzinfo is UTC
    assert bar.source_close_time is not None
    assert bar.source_close_time.tzinfo is UTC


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime(2024, 1, 1, 10),
        datetime(2024, 1, 1, 10, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_market_bar_requires_utc_timestamps(timestamp: datetime) -> None:
    with pytest.raises(ValueError, match="UTC"):
        _bar(candle_open_time=timestamp)


@pytest.mark.parametrize("price", [0.0, -1.0, float("nan"), float("inf")])
def test_market_bar_rejects_invalid_prices(price: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        _bar(open=price)


@pytest.mark.parametrize(
    "overrides",
    [
        {"high": 99.0},
        {"low": 106.0},
    ],
)
def test_market_bar_rejects_contradictory_ohlc(overrides: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="OHLC"):
        _bar(**overrides)


def test_market_bar_rejects_negative_or_non_finite_volume() -> None:
    with pytest.raises(ValueError, match="volume"):
        _bar(volume=-1.0)

    with pytest.raises(ValueError, match="volume"):
        _bar(volume=float("nan"))


def test_market_bar_rejects_source_close_outside_its_interval() -> None:
    with pytest.raises(ValueError, match="source close"):
        _bar(source_close_time=datetime(2024, 1, 1, 11, tzinfo=UTC))
