from decimal import Decimal

import pytest

from qap.market import BookLevel, PublicBookSnapshot, VenueInstrument
from qap.portfolio import AssetId
from qap.scanner.liquidity import BookSide, BookWalkStatus, walk_quote_notional

BTC = AssetId("BTC")
ETH = AssetId("ETH")
INSTRUMENT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCETH",
    base=BTC,
    quote=ETH,
)


def _snapshot() -> PublicBookSnapshot:
    from datetime import UTC, datetime

    return PublicBookSnapshot(
        instrument=INSTRUMENT,
        observed_at=datetime(2026, 8, 18, tzinfo=UTC),
        source_id="fixture-depth",
        source_fingerprint="a" * 64,
        bids=(
            BookLevel(price=2.00, quantity=3.0),
            BookLevel(price=1.90, quantity=5.0),
        ),
        asks=(
            BookLevel(price=2.10, quantity=2.0),
            BookLevel(price=2.20, quantity=4.0),
        ),
    )


def test_buy_book_walk_consumes_price_priority_and_partial_last_level() -> None:
    result = walk_quote_notional(
        _snapshot(),
        side=BookSide.BUY_BASE,
        quote_notional=Decimal("6.4"),
    )

    assert result.status is BookWalkStatus.FILLED
    assert result.quote_notional_requested == Decimal("6.4")
    assert result.quote_notional_filled == Decimal("6.4")
    assert result.base_quantity == Decimal("3")
    assert result.best_reference_price == Decimal("2.1")
    assert result.vwap == Decimal("6.4") / Decimal("3")
    assert result.levels_used == 2
    assert result.book_slippage_bps == pytest.approx(
        float(((result.vwap / Decimal("2.1")) - Decimal("1")) * Decimal("10000"))
    )


def test_sell_book_walk_consumes_bids_until_requested_quote_proceeds() -> None:
    result = walk_quote_notional(
        _snapshot(),
        side=BookSide.SELL_BASE,
        quote_notional=Decimal("8.85"),
    )

    assert result.status is BookWalkStatus.FILLED
    assert result.quote_notional_filled == Decimal("8.85")
    assert result.base_quantity == Decimal("4.5")
    assert result.best_reference_price == Decimal("2.0")
    assert result.vwap == Decimal("8.85") / Decimal("4.5")
    assert result.levels_used == 2
    assert result.book_slippage_bps == pytest.approx(
        float((Decimal("1") - result.vwap / Decimal("2.0")) * Decimal("10000"))
    )


def test_unfillable_book_walk_preserves_available_depth_and_requested_denominator() -> (
    None
):
    buy = walk_quote_notional(
        _snapshot(),
        side=BookSide.BUY_BASE,
        quote_notional=Decimal("20"),
    )
    sell = walk_quote_notional(
        _snapshot(),
        side=BookSide.SELL_BASE,
        quote_notional=Decimal("20"),
    )

    assert buy.status is BookWalkStatus.UNFILLABLE
    assert buy.quote_notional_requested == Decimal("20")
    assert buy.quote_notional_filled == Decimal("13.0")
    assert buy.levels_used == 2
    assert buy.vwap is None
    assert buy.book_slippage_bps is None

    assert sell.status is BookWalkStatus.UNFILLABLE
    assert sell.quote_notional_requested == Decimal("20")
    assert sell.quote_notional_filled == Decimal("15.5")
    assert sell.levels_used == 2
    assert sell.vwap is None
    assert sell.book_slippage_bps is None


def test_book_walk_rejects_nonpositive_or_non_decimal_test_size() -> None:
    with pytest.raises(ValueError, match="positive"):
        walk_quote_notional(
            _snapshot(),
            side=BookSide.BUY_BASE,
            quote_notional=Decimal("0"),
        )
    with pytest.raises(TypeError, match="Decimal"):
        walk_quote_notional(  # type: ignore[arg-type]
            _snapshot(),
            side=BookSide.BUY_BASE,
            quote_notional=1.0,
        )
