from datetime import UTC, datetime, timedelta

from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    fingerprint_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId


def _series(
    *,
    base: str = "BTC",
    quote: str = "USDT",
    start_hour: int = 10,
    close_adjustment: float = 0.0,
    source_close_adjustment: timedelta = timedelta(0),
) -> ValidatedBarSeries:
    instrument = VenueInstrument(
        venue="binance",
        venue_symbol=f"{base}{quote}",
        base=AssetId(base),
        quote=AssetId(quote),
    )
    interval = BarInterval("1h")
    bars: list[MarketBar] = []
    for offset in range(3):
        hour = start_hour + offset
        candle_open = datetime(2024, 1, 1, hour, tzinfo=UTC)
        bars.append(
            MarketBar(
                instrument=instrument,
                interval=interval,
                candle_open_time=candle_open,
                open=100.0 + offset,
                high=110.0 + offset,
                low=90.0 + offset,
                close=105.0 + offset + close_adjustment,
                volume=10.0 + offset,
                source_close_time=(
                    candle_open
                    + timedelta(hours=1)
                    - timedelta(milliseconds=1)
                    + source_close_adjustment
                ),
            )
        )
    return validate_bar_series(bars)


def test_semantically_equal_series_have_one_stable_fingerprint() -> None:
    first = fingerprint_bar_series(_series())
    second = fingerprint_bar_series(_series())

    assert first == second
    assert len(first) == 64
    int(first, 16)


def test_fingerprint_changes_for_authoritative_value_or_timestamp_changes() -> None:
    baseline = fingerprint_bar_series(_series())

    assert fingerprint_bar_series(_series(close_adjustment=0.25)) != baseline
    assert fingerprint_bar_series(_series(start_hour=11)) != baseline
    assert (
        fingerprint_bar_series(
            _series(source_close_adjustment=-timedelta(milliseconds=1))
        )
        != baseline
    )


def test_fingerprint_changes_when_explicit_orientation_changes() -> None:
    baseline = fingerprint_bar_series(_series(base="BTC", quote="USDT"))
    reciprocal_orientation = fingerprint_bar_series(_series(base="USDT", quote="BTC"))

    assert reciprocal_orientation != baseline
