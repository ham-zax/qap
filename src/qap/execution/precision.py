"""Deterministic venue-precision checks for paper spot execution."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.market import MarketMetadata
from qap.portfolio._decimal import canonical_decimal, exact_multiply

_ZERO = Decimal("0")


class MarketPrecisionReason(StrEnum):
    """Stable venue-constraint reasons for a rejected modeled fill."""

    MARKET_NOT_TRADING = "market_not_trading"
    PRICE_BELOW_MINIMUM = "price_below_minimum"
    PRICE_ABOVE_MAXIMUM = "price_above_maximum"
    BELOW_MINIMUM_QUANTITY = "below_minimum_quantity"
    ABOVE_MAXIMUM_QUANTITY = "above_maximum_quantity"
    BELOW_MINIMUM_NOTIONAL = "below_minimum_notional"
    ABOVE_MAXIMUM_NOTIONAL = "above_maximum_notional"


class MarketPrecisionError(ValueError):
    """Raised when a rounded modeled fill violates normalized venue metadata."""

    def __init__(self, reason: MarketPrecisionReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


def _validated_non_negative(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite() or value < _ZERO:
        raise ValueError(f"{field} must be finite and non-negative")
    return canonical_decimal(value)


def _validated_positive(value: object, *, field: str) -> Decimal:
    result = _validated_non_negative(value, field=field)
    if result <= _ZERO:
        raise ValueError(f"{field} must be positive")
    return result


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    value_numerator, value_denominator = value.as_integer_ratio()
    step_numerator, step_denominator = step.as_integer_ratio()
    units = (value_numerator * step_denominator) // (value_denominator * step_numerator)
    return canonical_decimal(exact_multiply(Decimal(units), step))


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    value_numerator, value_denominator = value.as_integer_ratio()
    step_numerator, step_denominator = step.as_integer_ratio()
    numerator = value_numerator * step_denominator
    denominator = value_denominator * step_numerator
    units = (numerator + denominator - 1) // denominator
    return canonical_decimal(exact_multiply(Decimal(units), step))


@dataclass(frozen=True, slots=True)
class MarketPrecision:
    """Apply one normalized venue metadata snapshot to deterministic paper fills."""

    metadata: MarketMetadata

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.metadata), MarketMetadata):
            raise TypeError("metadata must be MarketMetadata")

    def quantity_down(self, quantity: Decimal) -> Decimal:
        """Round a requested base quantity down to the venue quantity step."""

        normalized = _validated_non_negative(quantity, field="quantity")
        return _floor_to_step(normalized, self.metadata.quantity_step)

    def execution_price(self, price: Decimal, *, side: str) -> Decimal:
        """Quantize modeled price adversely: buys up, sells down."""

        normalized = _validated_positive(price, field="price")
        if side == "buy":
            return _ceil_to_step(normalized, self.metadata.price_tick)
        if side == "sell":
            return _floor_to_step(normalized, self.metadata.price_tick)
        raise ValueError("side must be 'buy' or 'sell'")

    def validate_fill(
        self,
        *,
        base_quantity: Decimal,
        execution_price: Decimal,
    ) -> None:
        """Fail closed when rounded quantity/price/notional violates venue bounds."""

        quantity = _validated_non_negative(base_quantity, field="base_quantity")
        price = _validated_positive(execution_price, field="execution_price")
        metadata = self.metadata
        if metadata.status != "TRADING":
            raise MarketPrecisionError(MarketPrecisionReason.MARKET_NOT_TRADING)
        if metadata.minimum_price is not None and price < metadata.minimum_price:
            raise MarketPrecisionError(MarketPrecisionReason.PRICE_BELOW_MINIMUM)
        if metadata.maximum_price is not None and price > metadata.maximum_price:
            raise MarketPrecisionError(MarketPrecisionReason.PRICE_ABOVE_MAXIMUM)
        if quantity <= _ZERO or (
            metadata.minimum_quantity is not None
            and quantity < metadata.minimum_quantity
        ):
            raise MarketPrecisionError(MarketPrecisionReason.BELOW_MINIMUM_QUANTITY)
        if (
            metadata.maximum_quantity is not None
            and quantity > metadata.maximum_quantity
        ):
            raise MarketPrecisionError(MarketPrecisionReason.ABOVE_MAXIMUM_QUANTITY)

        notional = exact_multiply(quantity, price)
        if (
            metadata.minimum_notional is not None
            and notional < metadata.minimum_notional
        ):
            raise MarketPrecisionError(MarketPrecisionReason.BELOW_MINIMUM_NOTIONAL)
        if (
            metadata.maximum_notional is not None
            and notional > metadata.maximum_notional
        ):
            raise MarketPrecisionError(MarketPrecisionReason.ABOVE_MAXIMUM_NOTIONAL)


__all__ = ["MarketPrecision", "MarketPrecisionError", "MarketPrecisionReason"]
