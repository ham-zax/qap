"""Venue-neutral paper-execution precision and notional metadata."""

from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from qap.market.instruments import VenueInstrument
from qap.portfolio._decimal import canonical_decimal

_ZERO = Decimal("0")


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return canonical_decimal(value)


def _optional_positive_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    return _positive_decimal(value, field=field)


def _status(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("status must be a string")
    normalized = value.strip().upper()
    if not normalized:
        raise ValueError("status must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class MarketMetadata:
    """Normalized spot-market constraints needed by deterministic paper fills."""

    instrument: VenueInstrument
    status: str
    price_tick: Decimal
    minimum_price: Decimal | None
    maximum_price: Decimal | None
    quantity_step: Decimal
    minimum_quantity: Decimal | None
    maximum_quantity: Decimal | None
    minimum_notional: Decimal | None
    maximum_notional: Decimal | None
    minimum_notional_applies_to_market: bool
    maximum_notional_applies_to_market: bool
    notional_average_price_minutes: int
    market_quantity_step: Decimal | None = None
    market_minimum_quantity: Decimal | None = None
    market_maximum_quantity: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.instrument), VenueInstrument):
            raise TypeError("instrument must be a VenueInstrument")
        status = _status(self.status)
        price_tick = _positive_decimal(self.price_tick, field="price_tick")
        minimum_price = _optional_positive_decimal(
            self.minimum_price,
            field="minimum_price",
        )
        maximum_price = _optional_positive_decimal(
            self.maximum_price,
            field="maximum_price",
        )
        quantity_step = _positive_decimal(self.quantity_step, field="quantity_step")
        minimum_quantity = _optional_positive_decimal(
            self.minimum_quantity,
            field="minimum_quantity",
        )
        maximum_quantity = _optional_positive_decimal(
            self.maximum_quantity,
            field="maximum_quantity",
        )
        minimum_notional = _optional_positive_decimal(
            self.minimum_notional,
            field="minimum_notional",
        )
        maximum_notional = _optional_positive_decimal(
            self.maximum_notional,
            field="maximum_notional",
        )
        market_quantity_step = _optional_positive_decimal(
            self.market_quantity_step,
            field="market_quantity_step",
        )
        market_minimum_quantity = _optional_positive_decimal(
            self.market_minimum_quantity,
            field="market_minimum_quantity",
        )
        market_maximum_quantity = _optional_positive_decimal(
            self.market_maximum_quantity,
            field="market_maximum_quantity",
        )
        if minimum_price is not None and maximum_price is not None:
            if minimum_price > maximum_price:
                raise ValueError("minimum_price must not exceed maximum_price")
        if minimum_quantity is not None and maximum_quantity is not None:
            if minimum_quantity > maximum_quantity:
                raise ValueError("minimum_quantity must not exceed maximum_quantity")
        if minimum_notional is not None and maximum_notional is not None:
            if minimum_notional > maximum_notional:
                raise ValueError("minimum_notional must not exceed maximum_notional")
        if (
            market_minimum_quantity is not None
            and market_maximum_quantity is not None
            and market_minimum_quantity > market_maximum_quantity
        ):
            raise ValueError(
                "market_minimum_quantity must not exceed market_maximum_quantity"
            )
        if not isinstance(cast(object, self.minimum_notional_applies_to_market), bool):
            raise TypeError("minimum_notional_applies_to_market must be a boolean")
        if not isinstance(cast(object, self.maximum_notional_applies_to_market), bool):
            raise TypeError("maximum_notional_applies_to_market must be a boolean")
        minutes = self.notional_average_price_minutes
        if isinstance(cast(object, minutes), bool) or not isinstance(
            cast(object, minutes), int
        ):
            raise TypeError("notional_average_price_minutes must be an integer")
        if minutes < 0:
            raise ValueError("notional_average_price_minutes must be non-negative")

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "price_tick", price_tick)
        object.__setattr__(self, "minimum_price", minimum_price)
        object.__setattr__(self, "maximum_price", maximum_price)
        object.__setattr__(self, "quantity_step", quantity_step)
        object.__setattr__(self, "minimum_quantity", minimum_quantity)
        object.__setattr__(self, "maximum_quantity", maximum_quantity)
        object.__setattr__(self, "minimum_notional", minimum_notional)
        object.__setattr__(self, "maximum_notional", maximum_notional)
        object.__setattr__(self, "market_quantity_step", market_quantity_step)
        object.__setattr__(self, "market_minimum_quantity", market_minimum_quantity)
        object.__setattr__(self, "market_maximum_quantity", market_maximum_quantity)

    @property
    def requires_market_notional_reference_price(self) -> bool:
        """Whether MARKET notional checks require a venue reference price."""

        return (
            self.minimum_notional is not None
            and self.minimum_notional_applies_to_market
        ) or (
            self.maximum_notional is not None
            and self.maximum_notional_applies_to_market
        )


__all__ = ["MarketMetadata"]
