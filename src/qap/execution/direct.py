"""Fail-closed execution of one declared direct spot rebalance leg."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.execution.costs import CostModel
from qap.execution.fills import (
    ExecutionQuantization,
    Fill,
    build_buy_fill,
    build_sell_fill,
)
from qap.execution.precision import MarketPrecisionError
from qap.market import MarketMetadata, VenueInstrument
from qap.portfolio import AssetId, PortfolioState
from qap.portfolio._decimal import canonical_decimal

_ZERO = Decimal("0")


class DirectExecutionReason(StrEnum):
    """Finite reasons why a requested direct leg produced no fill."""

    NO_ACTION = "no_action"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    UNSUPPORTED_DIRECT_ROUTE = "unsupported_direct_route"
    MARKET_NOT_TRADING = "market_not_trading"
    PRICE_BELOW_MINIMUM = "price_below_minimum"
    PRICE_ABOVE_MAXIMUM = "price_above_maximum"
    BELOW_MINIMUM_QUANTITY = "below_minimum_quantity"
    ABOVE_MAXIMUM_QUANTITY = "above_maximum_quantity"
    BELOW_MINIMUM_NOTIONAL = "below_minimum_notional"
    ABOVE_MAXIMUM_NOTIONAL = "above_maximum_notional"


@dataclass(frozen=True, slots=True)
class DirectExecutionResult:
    """Either one modeled direct fill or an explicit no-fill reason."""

    fill: Fill | None
    reason: DirectExecutionReason | None

    def __post_init__(self) -> None:
        if (self.fill is None) == (self.reason is None):
            raise ValueError("direct execution requires exactly one fill or reason")

    @property
    def executed(self) -> bool:
        return self.fill is not None


def _validated_deltas(
    values: Mapping[AssetId, Decimal],
) -> dict[AssetId, Decimal]:
    if not isinstance(cast(object, values), Mapping):
        raise TypeError("quantity_deltas must be a mapping")

    normalized: dict[AssetId, Decimal] = {}
    for asset, delta in values.items():
        if not isinstance(cast(object, asset), AssetId):
            raise TypeError("quantity_deltas keys must be AssetId values")
        if not isinstance(cast(object, delta), Decimal):
            raise TypeError(f"quantity delta for {asset.key} must be Decimal")
        if not delta.is_finite():
            raise ValueError(f"quantity delta for {asset.key} must be finite")
        canonical = canonical_decimal(delta)
        if canonical != _ZERO:
            normalized[asset] = canonical
    return normalized


def _no_fill(reason: DirectExecutionReason) -> DirectExecutionResult:
    return DirectExecutionResult(fill=None, reason=reason)


def execute_direct_rebalance_leg(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    instrument: VenueInstrument,
    quantity_deltas: Mapping[AssetId, Decimal],
    current_state: PortfolioState,
    reference_price: Decimal,
    cost_model: CostModel,
    quantization: ExecutionQuantization = ExecutionQuantization(),
    market_metadata: MarketMetadata | None = None,
) -> DirectExecutionResult:
    """Model one conversion only when it matches the declared direct market."""

    if not isinstance(cast(object, instrument), VenueInstrument):
        raise TypeError("instrument must be a VenueInstrument")
    if not isinstance(cast(object, current_state), PortfolioState):
        raise TypeError("current_state must be a PortfolioState")
    if not isinstance(cast(object, cost_model), CostModel):
        raise TypeError("cost_model must be a CostModel")
    if not isinstance(cast(object, quantization), ExecutionQuantization):
        raise TypeError("quantization must be an ExecutionQuantization")
    if market_metadata is not None and not isinstance(
        cast(object, market_metadata), MarketMetadata
    ):
        raise TypeError("market_metadata must be MarketMetadata or None")

    deltas = _validated_deltas(quantity_deltas)
    if not deltas:
        return _no_fill(DirectExecutionReason.NO_ACTION)

    if set(deltas) != {instrument.base, instrument.quote}:
        return _no_fill(DirectExecutionReason.UNSUPPORTED_DIRECT_ROUTE)

    base_delta = deltas[instrument.base]
    quote_delta = deltas[instrument.quote]

    if base_delta < _ZERO and quote_delta > _ZERO:
        available_base = current_state.quantity(instrument.base)
        if available_base <= _ZERO:
            return _no_fill(DirectExecutionReason.INSUFFICIENT_BALANCE)
        requested_base = base_delta.copy_abs()
        try:
            fill = build_sell_fill(
                fill_id=fill_id,
                decision_id=decision_id,
                execution_timestamp=execution_timestamp,
                instrument=instrument,
                base_quantity=min(requested_base, available_base),
                reference_price=reference_price,
                cost_model=cost_model,
                quantization=quantization,
                market_metadata=market_metadata,
            )
        except MarketPrecisionError as exc:
            return _no_fill(DirectExecutionReason(exc.reason.value))
        return DirectExecutionResult(fill=fill, reason=None)

    if base_delta > _ZERO and quote_delta < _ZERO:
        available_quote = current_state.quantity(instrument.quote)
        if available_quote <= _ZERO:
            return _no_fill(DirectExecutionReason.INSUFFICIENT_BALANCE)
        requested_quote = quote_delta.copy_abs()
        try:
            fill = build_buy_fill(
                fill_id=fill_id,
                decision_id=decision_id,
                execution_timestamp=execution_timestamp,
                instrument=instrument,
                quote_budget=min(requested_quote, available_quote),
                reference_price=reference_price,
                cost_model=cost_model,
                quantization=quantization,
                market_metadata=market_metadata,
            )
        except MarketPrecisionError as exc:
            return _no_fill(DirectExecutionReason(exc.reason.value))
        return DirectExecutionResult(fill=fill, reason=None)

    return _no_fill(DirectExecutionReason.UNSUPPORTED_DIRECT_ROUTE)
