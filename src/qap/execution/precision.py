"""Deterministic venue-precision checks for paper spot execution."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from math import gcd, lcm
from typing import cast

from qap.market import MarketMetadata
from qap.portfolio._decimal import canonical_decimal, exact_multiply

_ZERO = Decimal("0")


class PaperOrderType(StrEnum):
    """Order-type semantics supported by deterministic paper precision."""

    MARKET = "market"
    LIMIT = "limit"


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


def _common_step(first: Decimal, second: Decimal) -> Decimal:
    first_numerator, first_denominator = first.as_integer_ratio()
    second_numerator, second_denominator = second.as_integer_ratio()
    denominator = lcm(first_denominator, second_denominator)
    first_units = first_numerator * (denominator // first_denominator)
    second_units = second_numerator * (denominator // second_denominator)
    common_units = abs(first_units * second_units) // gcd(first_units, second_units)
    return canonical_decimal(Decimal(common_units) / Decimal(denominator))


def _is_multiple(value: Decimal, step: Decimal) -> bool:
    value_numerator, value_denominator = value.as_integer_ratio()
    step_numerator, step_denominator = step.as_integer_ratio()
    return (value_numerator * step_denominator) % (
        value_denominator * step_numerator
    ) == 0


def _order_type(value: PaperOrderType | str) -> PaperOrderType:
    raw = cast(object, value)
    if isinstance(raw, PaperOrderType):
        return raw
    if not isinstance(raw, str):
        raise TypeError("order_type must be a PaperOrderType or string")
    try:
        return PaperOrderType(raw)
    except ValueError as exc:
        raise ValueError("order_type must be 'market' or 'limit'") from exc


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

    def quantity_down(
        self,
        quantity: Decimal,
        *,
        order_type: PaperOrderType | str = PaperOrderType.MARKET,
    ) -> Decimal:
        """Round quantity down to all enabled steps for the modeled order type."""

        normalized = _validated_non_negative(quantity, field="quantity")
        kind = _order_type(order_type)
        step = self.metadata.quantity_step
        if (
            kind is PaperOrderType.MARKET
            and self.metadata.market_quantity_step is not None
        ):
            step = _common_step(step, self.metadata.market_quantity_step)
        return _floor_to_step(normalized, step)

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
        market_notional_reference_price: Decimal | None = None,
        order_type: PaperOrderType | str = PaperOrderType.MARKET,
    ) -> None:
        """Fail closed when rounded quantity/price/notional violates venue bounds."""

        quantity = _validated_non_negative(base_quantity, field="base_quantity")
        price = _validated_positive(execution_price, field="execution_price")
        kind = _order_type(order_type)
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
        if kind is PaperOrderType.MARKET:
            if (
                metadata.market_minimum_quantity is not None
                and quantity < metadata.market_minimum_quantity
            ):
                raise MarketPrecisionError(MarketPrecisionReason.BELOW_MINIMUM_QUANTITY)
            if (
                metadata.market_maximum_quantity is not None
                and quantity > metadata.market_maximum_quantity
            ):
                raise MarketPrecisionError(MarketPrecisionReason.ABOVE_MAXIMUM_QUANTITY)
            if metadata.market_quantity_step is not None and not _is_multiple(
                quantity, metadata.market_quantity_step
            ):
                raise MarketPrecisionError(MarketPrecisionReason.BELOW_MINIMUM_QUANTITY)

        minimum_applies = (
            kind is PaperOrderType.LIMIT or metadata.minimum_notional_applies_to_market
        )
        maximum_applies = (
            kind is PaperOrderType.LIMIT or metadata.maximum_notional_applies_to_market
        )
        notional_price = price
        market_notional_applies = kind is PaperOrderType.MARKET and (
            (minimum_applies and metadata.minimum_notional is not None)
            or (maximum_applies and metadata.maximum_notional is not None)
        )
        if market_notional_applies:
            if market_notional_reference_price is None:
                raise ValueError(
                    "market_notional_reference_price is required when a MARKET "
                    "notional filter applies"
                )
            notional_price = _validated_positive(
                market_notional_reference_price,
                field="market_notional_reference_price",
            )
        notional = exact_multiply(quantity, notional_price)
        if (
            minimum_applies
            and metadata.minimum_notional is not None
            and notional < metadata.minimum_notional
        ):
            raise MarketPrecisionError(MarketPrecisionReason.BELOW_MINIMUM_NOTIONAL)
        if (
            maximum_applies
            and metadata.maximum_notional is not None
            and notional > metadata.maximum_notional
        ):
            raise MarketPrecisionError(MarketPrecisionReason.ABOVE_MAXIMUM_NOTIONAL)


__all__ = [
    "MarketPrecision",
    "MarketPrecisionError",
    "MarketPrecisionReason",
    "PaperOrderType",
]
