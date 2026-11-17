"""Hand-computed L2 taker sweeps: VWAP, fees, depth, staleness, and conservation."""

from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any

import pytest

from qap.execution.fills import FillSide
from qap.execution.l2_book_fill import L2SweepResult, sweep_l2_taker_order
from qap.market import MarketMetadata, PublicBookSnapshot, VenueInstrument
from qap.market.microstructure import public_book_snapshot_from_rows
from qap.portfolio import (
    AssetId,
    PortfolioLedger,
    PortfolioState,
    value_holdings_at_prices,
)

D = Decimal
BTC = AssetId("BTC")
USDT = AssetId("USDT")
INSTRUMENT = VenueInstrument("binance", "BTCUSDT", BTC, USDT)
AT = datetime(2026, 11, 15, 12, tzinfo=UTC)
MID = D("100.5")
MS = 1_000_000

BIDS = [["100.0", "1.0"], ["99.0", "2.0"], ["98.0", "5.0"]]
ASKS = [["101.0", "1.0"], ["102.0", "2.0"], ["103.0", "5.0"]]


def make_book() -> PublicBookSnapshot:
    return public_book_snapshot_from_rows(
        instrument=INSTRUMENT,
        observed_at=AT,
        source_id="fixture-depth20",
        source_payload={"bids": BIDS, "asks": ASKS},
        bids=BIDS,
        asks=ASKS,
    )


def sell(
    qty: str,
    *,
    age_ms: int = 10,
    fee_bps: str = "10",
    metadata: MarketMetadata | None = None,
) -> L2SweepResult:
    return sweep_l2_taker_order(
        fill_id="f-sell",
        decision_id="d-1",
        execution_timestamp=AT,
        side=FillSide.SELL,
        book=make_book(),
        book_received_ns=0,
        target_fill_ns=age_ms * MS,
        fee_bps=D(fee_bps),
        base_quantity=D(qty),
        market_metadata=metadata,
    )


def buy(budget: str, *, age_ms: int = 10, fee_bps: str = "10") -> L2SweepResult:
    return sweep_l2_taker_order(
        fill_id="f-buy",
        decision_id="d-1",
        execution_timestamp=AT,
        side=FillSide.BUY,
        book=make_book(),
        book_received_ns=0,
        target_fill_ns=age_ms * MS,
        fee_bps=D(fee_bps),
        quote_budget=D(budget),
    )


def metadata(*, step: str, minimum: str) -> MarketMetadata:
    return MarketMetadata(
        instrument=INSTRUMENT,
        status="TRADING",
        price_tick=D("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=D(step),
        minimum_quantity=D(minimum),
        maximum_quantity=None,
        minimum_notional=None,
        maximum_notional=None,
        minimum_notional_applies_to_market=False,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


def test_sell_sweeps_two_bid_levels_with_hand_computed_economics() -> None:
    # 1.0 @ 100 + 1.0 @ 99 = 199 gross -> VWAP 99.5; fee 10 bps = 0.199.
    result = sell("2")
    assert result.rejected_reason is None and result.fill is not None
    assert result.levels_consumed == 2
    assert result.vwap_price == D("99.5")
    assert result.mid_price == MID
    assert result.book_age_ms == 10.0
    fill = result.fill
    assert fill.side is FillSide.SELL
    assert fill.base_quantity == D("2")
    assert fill.gross_quote_notional == D("199")
    assert fill.fee_amount == D("0.199")
    assert fill.slippage_value == D("2")  # 2 * (100.5 - 99.5)


def test_buy_sweeps_two_ask_levels_and_spends_exactly_the_budget() -> None:
    # 1.0 @ 101 + 1.0 @ 102 = 203 gross; fee 0.203; total debit 203.203.
    result = buy("203.203")
    assert result.rejected_reason is None and result.fill is not None
    assert result.levels_consumed == 2
    assert result.vwap_price == D("101.5")
    fill = result.fill
    assert fill.side is FillSide.BUY
    assert fill.base_quantity == D("2")
    assert fill.gross_quote_notional == D("203")
    assert fill.fee_amount == D("0.203")
    assert fill.slippage_value == D("2")  # 2 * (101.5 - 100.5)


def test_buy_never_debits_more_than_its_budget() -> None:
    result = buy("150")
    assert result.fill is not None
    debit = result.fill.gross_quote_notional + result.fill.fee_amount
    assert debit <= D("150")
    assert result.fill.base_quantity > D("1")  # spills past the first ask level


def test_fills_conserve_balances_and_value_loss_equals_costs() -> None:
    ledger = PortfolioLedger(PortfolioState.from_holdings({BTC: D("5"), USDT: D("0")}))
    prices = {BTC: MID, USDT: D("1")}
    before = value_holdings_at_prices(ledger.current_state, prices)

    sold = sell("2").fill
    assert sold is not None
    after_sell = ledger.apply_fill(sold)
    assert after_sell.quantity(BTC) == D("3")
    assert after_sell.quantity(USDT) == D("198.801")  # 199 - 0.199 fee
    sell_loss = before - value_holdings_at_prices(after_sell, prices)
    assert sell_loss == sold.fee_amount + sold.slippage_value == D("2.199")

    bought = buy("100").fill
    assert bought is not None
    after_buy = ledger.apply_fill(bought)
    with localcontext() as ctx:
        ctx.prec = 120  # exact: the engine's own quantities carry ~50 digits
        spent = D("198.801") - after_buy.quantity(USDT)
        assert spent == bought.gross_quote_notional + bought.fee_amount
        assert spent <= D("100")
        assert after_buy.quantity(BTC) == D("3") + bought.base_quantity


@pytest.mark.parametrize(
    ("age_ns", "rejected"), [(500 * MS, False), (500 * MS + 1, True)]
)
def test_staleness_limit_is_inclusive_at_500_ms(age_ns: int, rejected: bool) -> None:
    result = sweep_l2_taker_order(
        fill_id="f",
        decision_id="d",
        execution_timestamp=AT,
        side=FillSide.SELL,
        book=make_book(),
        book_received_ns=0,
        target_fill_ns=age_ns,
        fee_bps=D("10"),
        base_quantity=D("1"),
    )
    assert (result.rejected_reason == "stale_order_book") is rejected
    assert (result.fill is None) is rejected


def test_stale_book_rejection_reports_age_and_creates_no_fill() -> None:
    result = buy("100", age_ms=600)
    assert result.fill is None and result.vwap_price is None
    assert result.rejected_reason == "stale_order_book"
    assert result.book_age_ms == 600.0
    assert result.levels_consumed == 0


def test_fresh_book_arriving_after_target_fill_ns_uses_later_effective_fill_time() -> (
    None
):
    result = sweep_l2_taker_order(
        fill_id="f-fresh",
        decision_id="d-fresh",
        execution_timestamp=AT,
        side=FillSide.SELL,
        book=make_book(),
        book_received_ns=850 * MS,
        target_fill_ns=75 * MS,
        fee_bps=D("10"),
        base_quantity=D("1"),
    )
    assert result.rejected_reason is None
    assert result.fill is not None
    assert result.requested_fill_ns == 75 * MS
    assert result.effective_fill_ns == 850 * MS
    assert result.book_age_ms == 0.0


def test_delayed_collection_with_older_book_is_rejected_when_exceeding_staleness() -> (
    None
):
    result = sweep_l2_taker_order(
        fill_id="f-late",
        decision_id="d-late",
        execution_timestamp=AT,
        side=FillSide.SELL,
        book=make_book(),
        book_received_ns=100 * MS,
        target_fill_ns=700 * MS,
        fee_bps=D("10"),
        base_quantity=D("1"),
        max_staleness_ms=500.0,
    )
    assert result.fill is None
    assert result.rejected_reason == "stale_order_book"
    assert result.requested_fill_ns == 700 * MS
    assert result.effective_fill_ns == 700 * MS
    assert result.book_age_ms == 600.0


@pytest.mark.parametrize("qty", ["8.000001", "9"])
def test_sell_beyond_twenty_level_bid_depth_is_rejected(qty: str) -> None:
    result = sell(qty)  # visible bid depth is exactly 8.0 BTC
    assert result.fill is None
    assert result.rejected_reason == "insufficient_book_depth"


def test_buy_beyond_visible_ask_depth_is_rejected() -> None:
    # Whole ask side costs 101 + 204 + 515 = 820 before fees.
    result = buy("10000")
    assert result.fill is None
    assert result.rejected_reason == "insufficient_book_depth"


def test_sell_full_visible_depth_is_accepted() -> None:
    result = sell("8")
    assert result.fill is not None and result.levels_consumed == 3
    assert result.fill.gross_quote_notional == D("100") + D("198") + D("490")


def test_quantity_below_exchange_minimum_is_rejected() -> None:
    result = sell("0.3", metadata=metadata(step="0.1", minimum="0.5"))
    assert result.fill is None
    assert result.rejected_reason is not None
    assert "minimum" in result.rejected_reason


def test_sell_quantity_is_rounded_down_to_the_exchange_step() -> None:
    result = sell("1.7", metadata=metadata(step="0.5", minimum="0.5"))
    assert result.fill is not None
    assert result.fill.base_quantity == D("1.5")


def raw_call(side: FillSide, **extra: Any) -> L2SweepResult:
    return sweep_l2_taker_order(
        fill_id="f",
        decision_id="d",
        execution_timestamp=AT,
        side=side,
        book=make_book(),
        book_received_ns=0,
        target_fill_ns=MS,
        fee_bps=D("10"),
        **extra,
    )


def test_argument_contracts_fail_closed() -> None:
    both = {"base_quantity": D("1"), "quote_budget": D("1")}
    with pytest.raises(ValueError, match="SELL sweep requires"):
        raw_call(FillSide.SELL, **both)
    with pytest.raises(ValueError, match="BUY sweep requires"):
        raw_call(FillSide.BUY, **both)
    with pytest.raises(TypeError, match="must be Decimal"):
        raw_call(FillSide.SELL, base_quantity=1.0)
    with pytest.raises(ValueError, match="must be positive"):
        raw_call(FillSide.SELL, base_quantity=D("0"))
    with pytest.raises(ValueError, match="non-negative"):
        raw_call(FillSide.SELL, base_quantity=D("1"), max_staleness_ms=-1.0)
