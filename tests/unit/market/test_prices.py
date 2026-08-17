from collections.abc import MutableMapping
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import cast

import pytest

from qap.market import PriceSnapshot
from qap.portfolio import AssetId

D = Decimal


def test_price_snapshot_is_immutable_and_requires_explicit_prices() -> None:
    btc = AssetId("BTC")
    usdt = AssetId("USDT")
    snapshot = PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        numeraire=usdt,
        prices={usdt: D("1"), btc: D("42000.50")},
    )

    assert snapshot.price(btc) == D("42000.50")
    assert snapshot.price(usdt) == D("1")
    with pytest.raises(KeyError):
        snapshot.price(AssetId("ETH"))

    mutable_prices = cast(MutableMapping[AssetId, Decimal], snapshot.prices)
    with pytest.raises(TypeError):
        mutable_prices[btc] = D("1")


@pytest.mark.parametrize("price", [D("0"), D("-1"), D("NaN"), D("Infinity")])
def test_price_snapshot_rejects_non_positive_or_non_finite_prices(
    price: Decimal,
) -> None:
    usdt = AssetId("USDT")

    with pytest.raises(ValueError, match="positive finite"):
        PriceSnapshot.from_prices(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            numeraire=usdt,
            prices={usdt: D("1"), AssetId("BTC"): price},
        )


def test_price_snapshot_requires_numeraire_price_exactly_one() -> None:
    usdt = AssetId("USDT")

    with pytest.raises(ValueError, match="numeraire.*exactly 1"):
        PriceSnapshot.from_prices(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            numeraire=usdt,
            prices={usdt: D("0.999")},
        )


def test_price_snapshot_rejects_missing_numeraire_and_naive_time() -> None:
    usdt = AssetId("USDT")

    with pytest.raises(ValueError, match="numeraire"):
        PriceSnapshot.from_prices(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            numeraire=usdt,
            prices={AssetId("BTC"): D("42000")},
        )

    with pytest.raises(ValueError, match="UTC"):
        PriceSnapshot.from_prices(
            timestamp=datetime(2024, 1, 1),
            numeraire=usdt,
            prices={usdt: D("1")},
        )


def test_price_snapshot_serializes_float_prices_through_decimal_text() -> None:
    btc = AssetId("BTC")
    usdt = AssetId("USDT")

    snapshot = PriceSnapshot.from_float_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        numeraire=usdt,
        prices={usdt: 1.0, btc: 0.1},
    )

    assert snapshot.price(btc) == D("0.1")


def test_price_snapshot_normalizes_time_and_equivalent_decimal_encodings() -> None:
    btc = AssetId("BTC")
    usdt = AssetId("USDT")
    zero_offset = timezone(timedelta(0), name="ZERO")

    first = PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=zero_offset),
        numeraire=usdt,
        prices={usdt: D("1.0"), btc: D("42000.500")},
    )
    second = PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        numeraire=usdt,
        prices={btc: D("42000.5"), usdt: D("1")},
    )

    assert first.timestamp.tzinfo is UTC
    assert first == second
    assert hash(first) == hash(second)
    assert repr(first) == repr(second)
