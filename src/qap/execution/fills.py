"""Immutable direct-spot fill records and exact buy/sell arithmetic."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import MAX_EMAX, MIN_EMIN, ROUND_DOWN, Context, Decimal, localcontext
from enum import StrEnum
from types import MappingProxyType
from typing import cast

from qap.execution.costs import CostModel
from qap.execution.precision import MarketPrecision
from qap.market import MarketMetadata, VenueInstrument
from qap.portfolio import AssetId
from qap.portfolio._decimal import (
    DECIMAL_DIVISION_PRECISION,
    canonical_decimal,
    exact_add,
    exact_multiply,
    exact_subtract,
)

_ONE = Decimal("1")
_ZERO = Decimal("0")
_CONSERVATIVE_DIVISION_CONTEXT = Context(
    prec=DECIMAL_DIVISION_PRECISION,
    Emin=MIN_EMIN,
    Emax=MAX_EMAX,
    rounding=ROUND_DOWN,
)


class FillSide(StrEnum):
    """The side taken in the declared venue instrument orientation."""

    BUY = "buy"
    SELL = "sell"


def _validated_identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _validated_utc(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("execution_timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("execution_timestamp must be timezone-aware UTC")
    return value.astimezone(UTC)


def _validated_positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return canonical_decimal(value)


def _validated_instrument(value: object) -> VenueInstrument:
    if not isinstance(value, VenueInstrument):
        raise TypeError("instrument must be a VenueInstrument")
    return value


def _validated_cost_model(value: object) -> CostModel:
    if not isinstance(value, CostModel):
        raise TypeError("cost_model must be a CostModel")
    return value


def _market_precision(
    metadata: MarketMetadata | None,
    *,
    instrument: VenueInstrument,
    quantization: "ExecutionQuantization",
) -> MarketPrecision | None:
    if metadata is None:
        return None
    if not isinstance(cast(object, metadata), MarketMetadata):
        raise TypeError("market_metadata must be MarketMetadata or None")
    if metadata.instrument != instrument:
        raise ValueError("market_metadata instrument must match fill instrument")
    if (
        quantization.base_step is not None
        and quantization.base_step != metadata.quantity_step
    ):
        raise ValueError("market metadata and explicit base_step must agree")
    return MarketPrecision(metadata)


def _positive_divide_down(left: Decimal, right: Decimal) -> Decimal:
    """Divide positive values conservatively for an owned-funds ceiling."""

    if left <= _ZERO or right <= _ZERO:
        raise ValueError("conservative execution division requires positive values")
    with localcontext(_CONSERVATIVE_DIVISION_CONTEXT):
        return canonical_decimal(left / right)


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    value_numerator, value_denominator = value.as_integer_ratio()
    step_numerator, step_denominator = step.as_integer_ratio()
    units = (value_numerator * step_denominator) // (value_denominator * step_numerator)
    return canonical_decimal(exact_multiply(Decimal(units), step))


@dataclass(frozen=True, slots=True)
class ExecutionQuantization:
    """The minimal explicit venue-precision hook admitted in Phase 06."""

    base_step: Decimal | None = None

    def __post_init__(self) -> None:
        if self.base_step is None:
            return
        step = _validated_positive_decimal(self.base_step, field="base_step")
        object.__setattr__(self, "base_step", step)

    def base_quantity_down(self, quantity: Decimal) -> Decimal:
        """Round a non-negative base quantity down to the declared step."""

        if not isinstance(cast(object, quantity), Decimal):
            raise TypeError("base quantity must be Decimal")
        if not quantity.is_finite() or quantity < _ZERO:
            raise ValueError("base quantity must be finite and non-negative")
        normalized = canonical_decimal(quantity)
        if self.base_step is None:
            return normalized
        return _floor_to_step(normalized, self.base_step)


@dataclass(frozen=True, slots=True, init=False)
class Fill:
    """One fully modeled direct-spot fill with explicit inventory deltas."""

    fill_id: str
    decision_id: str
    execution_timestamp: datetime
    instrument: VenueInstrument
    side: FillSide
    reference_price: Decimal
    execution_price: Decimal
    base_quantity: Decimal
    gross_quote_notional: Decimal
    fee_amount: Decimal
    fee_asset: AssetId
    slippage_value: Decimal
    balance_deltas: Mapping[AssetId, Decimal]

    def __init__(self) -> None:
        raise TypeError("use build_buy_fill() or build_sell_fill()")

    @property
    def venue(self) -> str:
        return self.instrument.venue

    @property
    def venue_symbol(self) -> str:
        return self.instrument.venue_symbol

    @property
    def base(self) -> AssetId:
        return self.instrument.base

    @property
    def quote(self) -> AssetId:
        return self.instrument.quote

    @property
    def event_id(self) -> str:
        """Expose the stable fill identity to the portfolio ledger."""

        return self.fill_id


def _new_fill(
    *,
    fill_id: object,
    decision_id: object,
    execution_timestamp: object,
    instrument: object,
    side: FillSide,
    reference_price: Decimal,
    execution_price: Decimal,
    base_quantity: Decimal,
    gross_quote_notional: Decimal,
    fee_amount: Decimal,
    slippage_value: Decimal,
    balance_deltas: Mapping[AssetId, Decimal],
) -> Fill:
    validated_instrument = _validated_instrument(instrument)
    result = object.__new__(Fill)
    object.__setattr__(
        result,
        "fill_id",
        _validated_identifier(fill_id, field="fill_id"),
    )
    object.__setattr__(
        result,
        "decision_id",
        _validated_identifier(decision_id, field="decision_id"),
    )
    object.__setattr__(
        result,
        "execution_timestamp",
        _validated_utc(execution_timestamp),
    )
    object.__setattr__(result, "instrument", validated_instrument)
    object.__setattr__(result, "side", side)
    object.__setattr__(result, "reference_price", reference_price)
    object.__setattr__(result, "execution_price", execution_price)
    object.__setattr__(result, "base_quantity", base_quantity)
    object.__setattr__(result, "gross_quote_notional", gross_quote_notional)
    object.__setattr__(result, "fee_amount", fee_amount)
    object.__setattr__(result, "fee_asset", validated_instrument.quote)
    object.__setattr__(result, "slippage_value", slippage_value)
    object.__setattr__(
        result,
        "balance_deltas",
        MappingProxyType(dict(sorted(balance_deltas.items()))),
    )
    return result


def build_buy_fill(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    instrument: VenueInstrument,
    quote_budget: Decimal,
    reference_price: Decimal,
    market_notional_reference_price: Decimal | None = None,
    cost_model: CostModel,
    quantization: ExecutionQuantization = ExecutionQuantization(),
    market_metadata: MarketMetadata | None = None,
) -> Fill:
    """Buy base while reserving the quote-denominated fee inside the budget."""

    validated_instrument = _validated_instrument(instrument)
    budget = _validated_positive_decimal(quote_budget, field="quote_budget")
    reference = _validated_positive_decimal(
        reference_price,
        field="reference_price",
    )
    costs = _validated_cost_model(cost_model)
    if not isinstance(cast(object, quantization), ExecutionQuantization):
        raise TypeError("quantization must be an ExecutionQuantization")
    precision = _market_precision(
        market_metadata,
        instrument=validated_instrument,
        quantization=quantization,
    )

    execution_price = costs.buy_execution_price(reference)
    if precision is not None:
        execution_price = precision.execution_price(execution_price, side="buy")
    quote_cost_per_base = exact_multiply(
        execution_price,
        exact_add(_ONE, costs.fee_rate),
    )
    unquantized_base = _positive_divide_down(budget, quote_cost_per_base)
    base_quantity = quantization.base_quantity_down(unquantized_base)
    if precision is not None:
        base_quantity = precision.quantity_down(base_quantity)
        precision.validate_fill(
            base_quantity=base_quantity,
            execution_price=execution_price,
            market_notional_reference_price=market_notional_reference_price,
        )
    elif base_quantity <= _ZERO:
        raise ValueError("quote_budget is too small for a positive base fill")

    gross_quote_notional = exact_multiply(base_quantity, execution_price)
    fee_amount = exact_multiply(gross_quote_notional, costs.fee_rate)
    total_quote_debit = exact_add(gross_quote_notional, fee_amount)
    if total_quote_debit > budget:
        raise ArithmeticError("buy fill exceeds the declared quote budget")
    slippage_value = exact_multiply(
        base_quantity,
        exact_subtract(execution_price, reference),
    )
    return _new_fill(
        fill_id=fill_id,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        instrument=validated_instrument,
        side=FillSide.BUY,
        reference_price=reference,
        execution_price=execution_price,
        base_quantity=base_quantity,
        gross_quote_notional=gross_quote_notional,
        fee_amount=fee_amount,
        slippage_value=slippage_value,
        balance_deltas={
            validated_instrument.base: base_quantity,
            validated_instrument.quote: total_quote_debit.copy_negate(),
        },
    )


def build_sell_fill(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    instrument: VenueInstrument,
    base_quantity: Decimal,
    reference_price: Decimal,
    market_notional_reference_price: Decimal | None = None,
    cost_model: CostModel,
    quantization: ExecutionQuantization = ExecutionQuantization(),
    market_metadata: MarketMetadata | None = None,
) -> Fill:
    """Sell base and deduct the quote-denominated fee from gross proceeds."""

    validated_instrument = _validated_instrument(instrument)
    requested_base = _validated_positive_decimal(
        base_quantity,
        field="base_quantity",
    )
    reference = _validated_positive_decimal(
        reference_price,
        field="reference_price",
    )
    costs = _validated_cost_model(cost_model)
    if not isinstance(cast(object, quantization), ExecutionQuantization):
        raise TypeError("quantization must be an ExecutionQuantization")
    precision = _market_precision(
        market_metadata,
        instrument=validated_instrument,
        quantization=quantization,
    )

    filled_base = quantization.base_quantity_down(requested_base)
    if precision is not None:
        filled_base = precision.quantity_down(filled_base)
    elif filled_base <= _ZERO:
        raise ValueError("base_quantity is too small for a positive fill")
    execution_price = costs.sell_execution_price(reference)
    if precision is not None:
        execution_price = precision.execution_price(execution_price, side="sell")
        precision.validate_fill(
            base_quantity=filled_base,
            execution_price=execution_price,
            market_notional_reference_price=market_notional_reference_price,
        )
    gross_quote_notional = exact_multiply(filled_base, execution_price)
    fee_amount = exact_multiply(gross_quote_notional, costs.fee_rate)
    net_quote_proceeds = exact_subtract(gross_quote_notional, fee_amount)
    if net_quote_proceeds < _ZERO:
        raise ValueError("fee exceeds gross sell proceeds")
    slippage_value = exact_multiply(
        filled_base,
        exact_subtract(reference, execution_price),
    )
    return _new_fill(
        fill_id=fill_id,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        instrument=validated_instrument,
        side=FillSide.SELL,
        reference_price=reference,
        execution_price=execution_price,
        base_quantity=filled_base,
        gross_quote_notional=gross_quote_notional,
        fee_amount=fee_amount,
        slippage_value=slippage_value,
        balance_deltas={
            validated_instrument.base: filled_base.copy_negate(),
            validated_instrument.quote: net_quote_proceeds,
        },
    )
