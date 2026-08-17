from datetime import UTC, datetime

import pytest

from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId


def _instrument(base: str) -> VenueInstrument:
    return VenueInstrument(
        venue="binance",
        venue_symbol=f"{base}USDT",
        base=AssetId(base),
        quote=AssetId("USDT"),
    )


def _series(
    base: str,
    hours: range,
    *,
    interval: str = "1h",
) -> ValidatedBarSeries:
    instrument = _instrument(base)
    bar_interval = BarInterval(interval)
    return validate_bar_series(
        [
            MarketBar(
                instrument=instrument,
                interval=bar_interval,
                candle_open_time=datetime(2024, 1, 1, hour, tzinfo=UTC),
                open=float(hour + 100),
                high=float(hour + 110),
                low=float(hour + 90),
                close=float(hour + 105),
                volume=float(hour + 10),
            )
            for hour in hours
        ]
    )


def test_alignment_uses_exact_intersection_and_reports_edge_drops() -> None:
    btc = _series("BTC", range(9, 14))
    eth = _series("ETH", range(10, 13))

    aligned = align_bar_series([btc, eth])

    assert aligned.interval == BarInterval("1h")
    assert [timestamp.hour for timestamp in aligned.timestamps] == [10, 11, 12]

    aligned_btc = aligned.for_instrument(btc.instrument)
    assert aligned_btc.source_length == 5
    assert aligned_btc.dropped_leading == 1
    assert aligned_btc.dropped_trailing == 1
    assert aligned_btc.dropped_leading_timestamps == (
        datetime(2024, 1, 1, 9, tzinfo=UTC),
    )
    assert aligned_btc.dropped_trailing_timestamps == (
        datetime(2024, 1, 1, 13, tzinfo=UTC),
    )
    assert aligned_btc.opens == (110.0, 111.0, 112.0)
    assert aligned_btc.closes == (115.0, 116.0, 117.0)

    aligned_eth = aligned.for_instrument(eth.instrument)
    assert aligned_eth.source_length == 3
    assert aligned_eth.dropped_leading == 0
    assert aligned_eth.dropped_trailing == 0
    assert aligned_eth.dropped_leading_timestamps == ()
    assert aligned_eth.dropped_trailing_timestamps == ()
    assert aligned_eth.bars == eth.bars


def test_alignment_preserves_instrument_orientation_metadata() -> None:
    btc = _series("BTC", range(10, 13))
    eth = _series("ETH", range(10, 13))

    aligned = align_bar_series([btc, eth])

    assert aligned.for_instrument(btc.instrument).instrument.base == AssetId("BTC")
    assert aligned.for_instrument(eth.instrument).instrument.base == AssetId("ETH")


def test_alignment_requires_two_distinct_series_with_one_interval() -> None:
    btc = _series("BTC", range(10, 13))

    with pytest.raises(ValueError, match="at least two"):
        align_bar_series([btc])

    with pytest.raises(ValueError, match="duplicate instrument"):
        align_bar_series([btc, btc])

    with pytest.raises(ValueError, match="same interval"):
        align_bar_series([btc, _series("ETH", range(10, 16, 2), interval="2h")])


def test_alignment_rejects_series_without_a_common_timestamp() -> None:
    btc = _series("BTC", range(9, 11))
    eth = _series("ETH", range(12, 14))

    with pytest.raises(ValueError, match="no common timestamps"):
        align_bar_series([btc, eth])


def test_alignment_never_synthesizes_missing_instruments() -> None:
    btc = _series("BTC", range(10, 13))
    eth = _series("ETH", range(10, 13))
    aligned = align_bar_series([btc, eth])

    with pytest.raises(KeyError):
        aligned.for_instrument(_instrument("SOL"))
