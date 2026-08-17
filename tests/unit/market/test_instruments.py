from datetime import UTC, datetime, timedelta, timezone

import pytest

from qap.market import VenueInstrument
from qap.portfolio import AssetId, PairId, PairOrientation


def test_venue_instrument_keeps_venue_identity_outside_asset_identity() -> None:
    btc = AssetId("BTC")
    usdt = AssetId("USDT")

    instrument = VenueInstrument(
        venue="binance",
        venue_symbol="BTCUSDT",
        base=btc,
        quote=usdt,
    )

    assert instrument.venue == "binance"
    assert instrument.venue_symbol == "BTCUSDT"
    assert instrument.base is btc
    assert instrument.quote is usdt
    assert instrument.orientation == PairOrientation(btc, usdt)
    assert instrument.pair_id == PairId(btc, usdt)
    assert instrument.valid_from is None
    assert instrument.valid_to is None


def test_venue_instrument_preserves_observed_validity_metadata() -> None:
    valid_from = datetime(2020, 1, 1, tzinfo=UTC)
    valid_to = datetime(2021, 1, 1, tzinfo=UTC)

    instrument = VenueInstrument(
        venue="binance",
        venue_symbol="ETHUSDT",
        base=AssetId("ETH"),
        quote=AssetId("USDT"),
        valid_from=valid_from,
        valid_to=valid_to,
    )

    assert instrument.valid_from == valid_from
    assert instrument.valid_to == valid_to


def test_venue_instrument_normalizes_zero_offset_validity_to_utc() -> None:
    zero_offset = timezone(timedelta(0), name="ZERO")

    instrument = VenueInstrument(
        venue="binance",
        venue_symbol="ETHUSDT",
        base=AssetId("ETH"),
        quote=AssetId("USDT"),
        valid_from=datetime(2020, 1, 1, tzinfo=zero_offset),
        valid_to=datetime(2021, 1, 1, tzinfo=zero_offset),
    )

    assert instrument.valid_from is not None
    assert instrument.valid_to is not None
    assert instrument.valid_from.tzinfo is UTC
    assert instrument.valid_to.tzinfo is UTC


@pytest.mark.parametrize(
    ("valid_from", "valid_to"),
    [
        (datetime(2020, 1, 1), None),
        (None, datetime(2021, 1, 1)),
        (
            datetime(2021, 1, 1, tzinfo=UTC),
            datetime(2020, 1, 1, tzinfo=UTC),
        ),
    ],
)
def test_venue_instrument_rejects_invalid_validity_metadata(
    valid_from: datetime | None,
    valid_to: datetime | None,
) -> None:
    with pytest.raises(ValueError, match="validity"):
        VenueInstrument(
            venue="binance",
            venue_symbol="BTCUSDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
            valid_from=valid_from,
            valid_to=valid_to,
        )


def test_venue_instrument_rejects_same_asset_orientation() -> None:
    btc = AssetId("BTC")

    with pytest.raises(ValueError, match="distinct"):
        VenueInstrument(
            venue="binance",
            venue_symbol="BTCBTC",
            base=btc,
            quote=btc,
        )
