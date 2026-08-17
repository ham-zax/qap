"""Exact read-only valuation primitives over authoritative holdings."""

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import cast

from qap.portfolio._decimal import canonical_decimal, exact_multiply, exact_sum
from qap.portfolio.assets import AssetId
from qap.portfolio.state import PortfolioState

_ZERO = Decimal("0")


class MissingHoldingPriceError(ValueError):
    """A held asset has no explicit mark in the supplied price mapping."""

    asset: AssetId

    def __init__(self, asset: AssetId) -> None:
        self.asset = asset
        super().__init__(f"missing price for held asset {asset.key}")


def _validated_price(asset: AssetId, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"price for {asset.key} must be Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"price for {asset.key} must be finite and strictly positive")
    return canonical_decimal(value)


def holding_values_at_prices(
    state: PortfolioState,
    prices: Mapping[AssetId, Decimal],
) -> Mapping[AssetId, Decimal]:
    """Return exact per-asset values for every held quantity."""

    if not isinstance(cast(object, state), PortfolioState):
        raise TypeError("state must be a PortfolioState")
    if not isinstance(cast(object, prices), Mapping):
        raise TypeError("prices must be a mapping")

    typed_prices = cast(Mapping[object, object], prices)
    values: list[tuple[AssetId, Decimal]] = []
    for asset, quantity in state.holdings.items():
        try:
            raw_price = typed_prices[asset]
        except KeyError as exc:
            raise MissingHoldingPriceError(asset) from exc
        price = _validated_price(asset, raw_price)
        values.append((asset, exact_multiply(quantity, price)))
    return MappingProxyType(dict(values))


def value_holdings_at_prices(
    state: PortfolioState,
    prices: Mapping[AssetId, Decimal],
) -> Decimal:
    """Return one exact total derived from the per-asset valuation primitive."""

    return exact_sum(holding_values_at_prices(state, prices).values())
