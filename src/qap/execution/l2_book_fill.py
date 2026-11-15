"""Pure deterministic 20-level L2 order-book sweep for spot taker orders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import MAX_EMAX, MIN_EMIN, ROUND_DOWN, Context, Decimal, localcontext
from typing import cast

from qap.execution.fills import (
    Fill,
    FillSide,
    _new_fill,  # pyright: ignore[reportPrivateUsage]
)
from qap.execution.precision import (
    MarketPrecision,
    MarketPrecisionError,
    MarketPrecisionReason,
)
from qap.market import BookLevel, MarketMetadata, PublicBookSnapshot
from qap.portfolio._decimal import (
    DECIMAL_DIVISION_PRECISION,
    canonical_decimal,
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
)

_ZERO, _ONE, _TWO, _BPS_DENOM = (
    Decimal("0"),
    Decimal("1"),
    Decimal("2"),
    Decimal("10000"),
)
_DOWN_CTX = Context(
    prec=DECIMAL_DIVISION_PRECISION, Emin=MIN_EMIN, Emax=MAX_EMAX, rounding=ROUND_DOWN
)


@dataclass(frozen=True, slots=True)
class L2SweepResult:
    """Outcome of sweeping a bounded L2 spot order book for one taker leg."""

    fill: Fill | None
    rejected_reason: str | None
    levels_consumed: int
    mid_price: Decimal
    vwap_price: Decimal | None
    book_age_ms: float


def _divide_down(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DOWN_CTX):
        return canonical_decimal(left / right)


def _rejected(reason: str, *, mid_price: Decimal, book_age_ms: float) -> L2SweepResult:
    return L2SweepResult(None, reason, 0, mid_price, None, book_age_ms)


def _validated_decimal(
    value: object, *, field: str, allow_zero: bool = False
) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    if (allow_zero and value < _ZERO) or (not allow_zero and value <= _ZERO):
        raise ValueError(
            f"{field} must be {'non-negative' if allow_zero else 'positive'}"
        )
    return canonical_decimal(value)


def _consume_levels(
    levels: tuple[BookLevel, ...], target_base: Decimal
) -> tuple[Decimal, int, Decimal]:
    remaining, gross_quote, consumed = target_base, _ZERO, 0
    for level in levels:
        if remaining <= _ZERO:
            break
        take_qty = min(remaining, Decimal(str(level.quantity)))
        gross_quote = exact_add(
            gross_quote, exact_multiply(take_qty, Decimal(str(level.price)))
        )
        remaining = exact_subtract(remaining, take_qty)
        consumed += 1
    return gross_quote, consumed, remaining


def _validate_precision(
    precision: MarketPrecision | None, *, base_qty: Decimal, vwap: Decimal
) -> str | None:
    if precision is None:
        return None
    try:
        precision.validate_fill(
            base_quantity=base_qty,
            execution_price=vwap,
            market_notional_reference_price=vwap,
        )
    except MarketPrecisionError as err:
        return err.reason.value
    return None


def _sweep_sell(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    book: PublicBookSnapshot,
    mid_price: Decimal,
    book_age_ms: float,
    fee_rate: Decimal,
    requested_base: Decimal,
    precision: MarketPrecision | None,
) -> L2SweepResult:
    target_base = (
        precision.quantity_down(requested_base)
        if precision is not None
        else requested_base
    )
    if target_base <= _ZERO:
        return _rejected(
            MarketPrecisionReason.BELOW_MINIMUM_QUANTITY.value,
            mid_price=mid_price,
            book_age_ms=book_age_ms,
        )
    gross_quote, consumed, remaining = _consume_levels(book.bids, target_base)
    if remaining > _ZERO:
        return _rejected(
            "insufficient_book_depth", mid_price=mid_price, book_age_ms=book_age_ms
        )
    vwap = divide(gross_quote, target_base)
    if (
        err := _validate_precision(precision, base_qty=target_base, vwap=vwap)
    ) is not None:
        return _rejected(err, mid_price=mid_price, book_age_ms=book_age_ms)
    fee_amount = exact_multiply(gross_quote, fee_rate)
    net_quote = exact_subtract(gross_quote, fee_amount)
    if net_quote < _ZERO:
        raise ValueError("fee exceeds gross sell proceeds")
    slippage = max(_ZERO, exact_multiply(target_base, exact_subtract(mid_price, vwap)))
    fill = _new_fill(
        fill_id=fill_id,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        instrument=book.instrument,
        side=FillSide.SELL,
        reference_price=mid_price,
        execution_price=vwap,
        base_quantity=target_base,
        gross_quote_notional=gross_quote,
        fee_amount=fee_amount,
        slippage_value=slippage,
        balance_deltas={
            book.instrument.base: target_base.copy_negate(),
            book.instrument.quote: net_quote,
        },
    )
    return L2SweepResult(fill, None, consumed, mid_price, vwap, book_age_ms)


def _sweep_buy(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    book: PublicBookSnapshot,
    mid_price: Decimal,
    book_age_ms: float,
    fee_rate: Decimal,
    budget: Decimal,
    precision: MarketPrecision | None,
) -> L2SweepResult:
    remaining_quote = _divide_down(budget, exact_add(_ONE, fee_rate))
    raw_base = _ZERO
    for level in book.asks:
        if remaining_quote <= _ZERO:
            break
        lvl_price, lvl_qty = Decimal(str(level.price)), Decimal(str(level.quantity))
        lvl_cost = exact_multiply(lvl_qty, lvl_price)
        if remaining_quote >= lvl_cost:
            raw_base = exact_add(raw_base, lvl_qty)
            remaining_quote = exact_subtract(remaining_quote, lvl_cost)
        else:
            raw_base = exact_add(raw_base, _divide_down(remaining_quote, lvl_price))
            remaining_quote = _ZERO
    if remaining_quote > _ZERO:
        return _rejected(
            "insufficient_book_depth", mid_price=mid_price, book_age_ms=book_age_ms
        )
    filled_base = (
        precision.quantity_down(raw_base)
        if precision is not None
        else canonical_decimal(raw_base)
    )
    if filled_base <= _ZERO:
        return _rejected(
            MarketPrecisionReason.BELOW_MINIMUM_QUANTITY.value,
            mid_price=mid_price,
            book_age_ms=book_age_ms,
        )
    gross_quote, consumed, _ = _consume_levels(book.asks, filled_base)
    vwap = divide(gross_quote, filled_base)
    if (
        err := _validate_precision(precision, base_qty=filled_base, vwap=vwap)
    ) is not None:
        return _rejected(err, mid_price=mid_price, book_age_ms=book_age_ms)
    fee_amount = exact_multiply(gross_quote, fee_rate)
    total_debit = exact_add(gross_quote, fee_amount)
    if total_debit > budget:
        raise ArithmeticError("buy L2 sweep exceeds the declared quote budget")
    slippage = max(_ZERO, exact_multiply(filled_base, exact_subtract(vwap, mid_price)))
    fill = _new_fill(
        fill_id=fill_id,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        instrument=book.instrument,
        side=FillSide.BUY,
        reference_price=mid_price,
        execution_price=vwap,
        base_quantity=filled_base,
        gross_quote_notional=gross_quote,
        fee_amount=fee_amount,
        slippage_value=slippage,
        balance_deltas={
            book.instrument.base: filled_base,
            book.instrument.quote: total_debit.copy_negate(),
        },
    )
    return L2SweepResult(fill, None, consumed, mid_price, vwap, book_age_ms)


def sweep_l2_taker_order(
    *,
    fill_id: str,
    decision_id: str,
    execution_timestamp: datetime,
    side: FillSide,
    book: PublicBookSnapshot,
    book_received_ns: int,
    target_fill_ns: int,
    fee_bps: Decimal,
    base_quantity: Decimal | None = None,
    quote_budget: Decimal | None = None,
    max_staleness_ms: float = 500.0,
    market_metadata: MarketMetadata | None = None,
) -> L2SweepResult:
    """Sweep bounded L2 bids/asks deterministically with staleness and filter checks."""

    if not isinstance(cast(object, book), PublicBookSnapshot):
        raise TypeError("book must be a PublicBookSnapshot")
    if not isinstance(cast(object, side), FillSide):
        raise TypeError("side must be a FillSide")
    if max_staleness_ms < 0.0:
        raise ValueError("max_staleness_ms must be non-negative")
    fee_rate = divide(
        _validated_decimal(fee_bps, field="fee_bps", allow_zero=True), _BPS_DENOM
    )
    precision: MarketPrecision | None = None
    if market_metadata is not None:
        if not isinstance(cast(object, market_metadata), MarketMetadata):
            raise TypeError("market_metadata must be MarketMetadata or None")
        if market_metadata.instrument != book.instrument:
            raise ValueError("market_metadata instrument must match book instrument")
        precision = MarketPrecision(market_metadata)

    mid_price = divide(
        exact_add(Decimal(str(book.best_bid)), Decimal(str(book.best_ask))), _TWO
    )
    age_ms = (target_fill_ns - book_received_ns) / 1_000_000.0

    if side is FillSide.SELL:
        if base_quantity is None or quote_budget is not None:
            raise ValueError("SELL sweep requires base_quantity and quote_budget=None")
        requested_base = _validated_decimal(base_quantity, field="base_quantity")
        if age_ms > max_staleness_ms:
            return _rejected(
                "stale_order_book", mid_price=mid_price, book_age_ms=age_ms
            )
        return _sweep_sell(
            fill_id=fill_id,
            decision_id=decision_id,
            execution_timestamp=execution_timestamp,
            book=book,
            mid_price=mid_price,
            book_age_ms=age_ms,
            fee_rate=fee_rate,
            requested_base=requested_base,
            precision=precision,
        )

    if quote_budget is None or base_quantity is not None:
        raise ValueError("BUY sweep requires quote_budget and base_quantity=None")
    budget = _validated_decimal(quote_budget, field="quote_budget")
    if age_ms > max_staleness_ms:
        return _rejected("stale_order_book", mid_price=mid_price, book_age_ms=age_ms)
    return _sweep_buy(
        fill_id=fill_id,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        book=book,
        mid_price=mid_price,
        book_age_ms=age_ms,
        fee_rate=fee_rate,
        budget=budget,
        precision=precision,
    )


__all__ = ["L2SweepResult", "sweep_l2_taker_order"]
