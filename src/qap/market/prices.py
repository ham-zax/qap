"""Immutable explicit Decimal price observations."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Self, cast

from qap.portfolio import AssetId

_ONE = Decimal("1")
_ZERO = Decimal("0")


def _validated_utc(timestamp: object) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError("price timestamp must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError("price timestamp must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


def _validated_asset(asset: object, *, field: str) -> AssetId:
    if not isinstance(asset, AssetId):
        raise TypeError(f"{field} must be an AssetId")
    return asset


def _canonical_decimal(value: Decimal) -> Decimal:
    if value == _ZERO:
        return _ZERO
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise ValueError("price must be finite")
    normalized_digits = list(digits)
    while normalized_digits[-1] == 0:
        normalized_digits.pop()
        exponent += 1
    return Decimal((sign, tuple(normalized_digits), exponent))


def _validated_decimal_prices(
    prices: object,
) -> list[tuple[AssetId, Decimal]]:
    if not isinstance(prices, Mapping):
        raise TypeError("prices must be a mapping")

    normalized: list[tuple[AssetId, Decimal]] = []
    typed_prices = cast(Mapping[object, object], prices)
    for asset, price in typed_prices.items():
        validated_asset = _validated_asset(asset, field="price key")
        if not isinstance(price, Decimal):
            raise TypeError(f"price for {validated_asset.key} must be Decimal")
        if not price.is_finite() or price <= _ZERO:
            raise ValueError(f"price for {validated_asset.key} must be positive finite")
        normalized.append((validated_asset, _canonical_decimal(price)))
    return normalized


def _decimal_prices_from_floats(
    prices: object,
) -> dict[AssetId, Decimal]:
    if not isinstance(prices, Mapping):
        raise TypeError("float prices must be a mapping")

    decimal_prices: dict[AssetId, Decimal] = {}
    typed_prices = cast(Mapping[object, object], prices)
    for asset, price in typed_prices.items():
        validated_asset = _validated_asset(asset, field="float price key")
        if not isinstance(price, float):
            raise TypeError(f"float price for {validated_asset.key} must be a float")
        if not math.isfinite(price) or price <= 0:
            raise ValueError(
                f"float price for {validated_asset.key} must be positive finite"
            )
        decimal_prices[validated_asset] = Decimal(str(price))
    return decimal_prices


@dataclass(frozen=True, slots=True, init=False)
class PriceSnapshot:
    """Explicit asset-to-numeraire marks without valuation behavior."""

    timestamp: datetime
    numeraire: AssetId
    _items: tuple[tuple[AssetId, Decimal], ...]

    def __init__(self) -> None:
        raise TypeError("use PriceSnapshot.from_prices()")

    @classmethod
    def from_prices(
        cls,
        *,
        timestamp: datetime,
        numeraire: AssetId,
        prices: Mapping[AssetId, Decimal],
    ) -> Self:
        """Validate and copy explicit Decimal prices into a stable snapshot."""

        validated_timestamp = _validated_utc(timestamp)
        validated_numeraire = _validated_asset(numeraire, field="numeraire")
        normalized = _validated_decimal_prices(prices)

        normalized_prices = dict(normalized)
        if validated_numeraire not in normalized_prices:
            raise ValueError("numeraire price must be present explicitly")
        if normalized_prices[validated_numeraire] != _ONE:
            raise ValueError("numeraire price must be exactly 1 in its own units")

        snapshot = object.__new__(cls)
        object.__setattr__(snapshot, "timestamp", validated_timestamp)
        object.__setattr__(snapshot, "numeraire", validated_numeraire)
        object.__setattr__(snapshot, "_items", tuple(sorted(normalized)))
        return snapshot

    @classmethod
    def from_float_prices(
        cls,
        *,
        timestamp: datetime,
        numeraire: AssetId,
        prices: Mapping[AssetId, float],
    ) -> Self:
        """Cross the float boundary through stable decimal text serialization."""

        return cls.from_prices(
            timestamp=timestamp,
            numeraire=numeraire,
            prices=_decimal_prices_from_floats(prices),
        )

    @property
    def prices(self) -> Mapping[AssetId, Decimal]:
        """Return an immutable mapping ordered by stable asset identity."""

        return MappingProxyType(dict(self._items))

    def price(self, asset: AssetId) -> Decimal:
        """Return one explicit mark; never synthesize a missing price."""

        validated_asset = _validated_asset(asset, field="price lookup")
        for priced_asset, price in self._items:
            if priced_asset == validated_asset:
                return price
        raise KeyError(validated_asset)

    def __repr__(self) -> str:
        return (
            "PriceSnapshot("
            f"timestamp={self.timestamp!r}, "
            f"numeraire={self.numeraire!r}, "
            f"prices={dict(self._items)!r})"
        )
