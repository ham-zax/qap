"""Deterministic prospective liquidity evidence for Scanner-V1 Slice 2."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.market import BookLevel, PublicBookSnapshot
from qap.portfolio._decimal import divide

_ZERO = Decimal("0")
_ONE = Decimal("1")
_BPS = Decimal("10000")


class BookSide(StrEnum):
    BUY_BASE = "buy_base"
    SELL_BASE = "sell_base"


class BookWalkStatus(StrEnum):
    FILLED = "filled"
    UNFILLABLE = "unfillable"


@dataclass(frozen=True, slots=True)
class BookWalkResult:
    snapshot_id: str
    side: BookSide
    status: BookWalkStatus
    quote_notional_requested: Decimal
    quote_notional_filled: Decimal
    base_quantity: Decimal
    best_reference_price: Decimal
    levels_used: int
    vwap: Decimal | None
    book_slippage_bps: float | None


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return value


def _decimal_float(value: float) -> Decimal:
    return Decimal(str(value))


def _filled_walk(
    snapshot: PublicBookSnapshot,
    *,
    side: BookSide,
    requested: Decimal,
    filled: Decimal,
    base_quantity: Decimal,
    best_reference_price: Decimal,
    levels_used: int,
) -> BookWalkResult:
    vwap = divide(filled, base_quantity)
    if side is BookSide.BUY_BASE:
        slippage = (divide(vwap, best_reference_price) - _ONE) * _BPS
    else:
        slippage = (_ONE - divide(vwap, best_reference_price)) * _BPS
    return BookWalkResult(
        snapshot_id=snapshot.snapshot_id,
        side=side,
        status=BookWalkStatus.FILLED,
        quote_notional_requested=requested,
        quote_notional_filled=filled,
        base_quantity=base_quantity,
        best_reference_price=best_reference_price,
        levels_used=levels_used,
        vwap=vwap,
        book_slippage_bps=float(slippage),
    )


def _unfillable_walk(
    snapshot: PublicBookSnapshot,
    *,
    side: BookSide,
    requested: Decimal,
    filled: Decimal,
    base_quantity: Decimal,
    best_reference_price: Decimal,
    levels_used: int,
) -> BookWalkResult:
    return BookWalkResult(
        snapshot_id=snapshot.snapshot_id,
        side=side,
        status=BookWalkStatus.UNFILLABLE,
        quote_notional_requested=requested,
        quote_notional_filled=filled,
        base_quantity=base_quantity,
        best_reference_price=best_reference_price,
        levels_used=levels_used,
        vwap=None,
        book_slippage_bps=None,
    )


def _levels(snapshot: PublicBookSnapshot, side: BookSide) -> tuple[BookLevel, ...]:
    return snapshot.asks if side is BookSide.BUY_BASE else snapshot.bids


def walk_quote_notional(
    snapshot: PublicBookSnapshot,
    *,
    side: BookSide,
    quote_notional: Decimal,
) -> BookWalkResult:
    """Walk recorded depth for one exact quote notional without hidden-depth inference."""

    if not isinstance(cast(object, snapshot), PublicBookSnapshot):
        raise TypeError("snapshot must be a PublicBookSnapshot")
    if not isinstance(cast(object, side), BookSide):
        raise TypeError("side must be a BookSide")
    requested = _positive_decimal(quote_notional, field="quote_notional")
    levels = _levels(snapshot, side)
    best = _decimal_float(levels[0].price)
    remaining = requested
    quote_filled = _ZERO
    base_filled = _ZERO
    levels_used = 0

    for level in levels:
        price = _decimal_float(level.price)
        available_base = _decimal_float(level.quantity)
        available_quote = price * available_base
        take_quote = min(remaining, available_quote)
        if take_quote <= _ZERO:
            continue
        take_base = divide(take_quote, price)
        quote_filled += take_quote
        base_filled += take_base
        remaining -= take_quote
        levels_used += 1
        if remaining == _ZERO:
            return _filled_walk(
                snapshot,
                side=side,
                requested=requested,
                filled=quote_filled,
                base_quantity=base_filled,
                best_reference_price=best,
                levels_used=levels_used,
            )

    return _unfillable_walk(
        snapshot,
        side=side,
        requested=requested,
        filled=quote_filled,
        base_quantity=base_filled,
        best_reference_price=best,
        levels_used=levels_used,
    )


__all__ = [
    "BookSide",
    "BookWalkResult",
    "BookWalkStatus",
    "walk_quote_notional",
]
