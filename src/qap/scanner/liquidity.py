"""Deterministic direct-book mechanics for Scanner-V1 Slice 2."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.market import BookLevel, PublicBookSnapshot
from qap.portfolio._decimal import (
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
)

_ZERO = Decimal("0")
_TWO = Decimal("2")
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
    mid_reference_price: Decimal
    levels_used: int
    vwap: Decimal | None
    book_price_impact_bps: Decimal | None

    @property
    def book_slippage_bps(self) -> float | None:
        """Compatibility projection for the original book-walk API."""

        return (
            None
            if self.book_price_impact_bps is None
            else float(self.book_price_impact_bps)
        )


@dataclass(frozen=True, slots=True)
class FrictionEvidence:
    snapshot_id: str
    side: BookSide
    quote_notional_requested: Decimal
    fillable: bool
    fee_bps: Decimal
    book_price_impact_bps: Decimal | None
    total_friction_bps: Decimal | None


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return value


def _decimal_float(value: float) -> Decimal:
    return Decimal(str(value))


def book_mid_price(snapshot: PublicBookSnapshot) -> Decimal:
    """Return the exact midpoint of the captured best bid and ask."""

    if not isinstance(cast(object, snapshot), PublicBookSnapshot):
        raise TypeError("snapshot must be a PublicBookSnapshot")
    best_bid = _decimal_float(snapshot.bids[0].price)
    best_ask = _decimal_float(snapshot.asks[0].price)
    return divide(exact_add(best_bid, best_ask), _TWO)


def _levels(snapshot: PublicBookSnapshot, side: BookSide) -> tuple[BookLevel, ...]:
    return snapshot.asks if side is BookSide.BUY_BASE else snapshot.bids


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
    mid = book_mid_price(snapshot)
    impact = exact_multiply(divide(abs(exact_subtract(vwap, mid)), mid), _BPS)
    return BookWalkResult(
        snapshot_id=snapshot.snapshot_id,
        side=side,
        status=BookWalkStatus.FILLED,
        quote_notional_requested=requested,
        quote_notional_filled=filled,
        base_quantity=base_quantity,
        best_reference_price=best_reference_price,
        mid_reference_price=mid,
        levels_used=levels_used,
        vwap=vwap,
        book_price_impact_bps=impact,
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
        mid_reference_price=book_mid_price(snapshot),
        levels_used=levels_used,
        vwap=None,
        book_price_impact_bps=None,
    )


def walk_quote_notional(
    snapshot: PublicBookSnapshot,
    *,
    side: BookSide,
    quote_notional: Decimal,
) -> BookWalkResult:
    """Walk only recorded depth for one exact quote notional."""

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
        available_quote = exact_multiply(price, available_base)
        take_quote = min(remaining, available_quote)
        if take_quote <= _ZERO:
            continue
        take_base = divide(take_quote, price)
        quote_filled = exact_add(quote_filled, take_quote)
        base_filled = exact_add(base_filled, take_base)
        remaining = exact_subtract(remaining, take_quote)
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


def friction_evidence(
    walk: BookWalkResult,
    *,
    fee_bps: Decimal,
) -> FrictionEvidence:
    """Combine book impact with the configured taker fee exactly once."""

    if not isinstance(cast(object, walk), BookWalkResult):
        raise TypeError("walk must be a BookWalkResult")
    if not isinstance(cast(object, fee_bps), Decimal):
        raise TypeError("fee_bps must be a Decimal")
    if not fee_bps.is_finite() or fee_bps < _ZERO:
        raise ValueError("fee_bps must be finite and non-negative")
    impact = walk.book_price_impact_bps
    if walk.status is BookWalkStatus.UNFILLABLE:
        return FrictionEvidence(
            snapshot_id=walk.snapshot_id,
            side=walk.side,
            quote_notional_requested=walk.quote_notional_requested,
            fillable=False,
            fee_bps=fee_bps,
            book_price_impact_bps=None,
            total_friction_bps=None,
        )
    if impact is None:
        raise ValueError("filled book walk must carry book price impact")
    return FrictionEvidence(
        snapshot_id=walk.snapshot_id,
        side=walk.side,
        quote_notional_requested=walk.quote_notional_requested,
        fillable=True,
        fee_bps=fee_bps,
        book_price_impact_bps=impact,
        total_friction_bps=exact_add(fee_bps, impact),
    )


__all__ = [
    "BookSide",
    "BookWalkResult",
    "BookWalkStatus",
    "FrictionEvidence",
    "book_mid_price",
    "friction_evidence",
    "walk_quote_notional",
]
