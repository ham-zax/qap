from datetime import UTC, datetime
from decimal import Decimal

from qap.execution import (
    CostModel,
    DirectExecutionReason,
    FillSide,
    execute_direct_rebalance_leg,
)
from qap.market import VenueInstrument
from qap.portfolio import AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
BTC_USDT = VenueInstrument(
    venue="fixture",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)


def test_direct_leg_sells_declared_base_for_quote() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-1:leg-0",
        decision_id="decision-1",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={BTC: D("-1"), USDT: D("10")},
        current_state=PortfolioState.from_holdings({BTC: D("2")}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.reason is None
    assert result.fill is not None
    assert result.fill.side is FillSide.SELL
    assert result.fill.balance_deltas == {BTC: D("-1"), USDT: D("10")}


def test_direct_leg_buys_declared_base_with_quote() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-2:leg-0",
        decision_id="decision-2",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={BTC: D("5"), USDT: D("-50")},
        current_state=PortfolioState.from_holdings({USDT: D("100")}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.reason is None
    assert result.fill is not None
    assert result.fill.side is FillSide.BUY
    assert result.fill.balance_deltas == {BTC: D("5"), USDT: D("-50")}


def test_direct_leg_caps_requested_conversion_by_owned_source_balance() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-3:leg-0",
        decision_id="decision-3",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={BTC: D("5"), USDT: D("-50")},
        current_state=PortfolioState.from_holdings({USDT: D("30")}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.reason is None
    assert result.fill is not None
    assert result.fill.base_quantity == D("3")
    assert result.fill.balance_deltas == {BTC: D("3"), USDT: D("-30")}


def test_direct_leg_fails_closed_for_undeclared_route() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-4:leg-0",
        decision_id="decision-4",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={ETH: D("-1"), USDT: D("10")},
        current_state=PortfolioState.from_holdings({ETH: D("1")}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.fill is None
    assert result.reason is DirectExecutionReason.UNSUPPORTED_DIRECT_ROUTE


def test_direct_leg_reports_no_owned_source_inventory() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-5:leg-0",
        decision_id="decision-5",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={BTC: D("1"), USDT: D("-10")},
        current_state=PortfolioState.from_holdings({}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.fill is None
    assert result.reason is DirectExecutionReason.INSUFFICIENT_BALANCE


def test_direct_leg_returns_no_action_for_zero_deltas() -> None:
    result = execute_direct_rebalance_leg(
        fill_id="run-1:decision-6:leg-0",
        decision_id="decision-6",
        execution_timestamp=AT,
        instrument=BTC_USDT,
        quantity_deltas={BTC: D("0"), USDT: D("0")},
        current_state=PortfolioState.from_holdings({BTC: D("1")}),
        reference_price=D("10"),
        cost_model=CostModel.zero(),
    )

    assert result.fill is None
    assert result.reason is DirectExecutionReason.NO_ACTION
