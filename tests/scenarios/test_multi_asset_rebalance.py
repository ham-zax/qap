from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, DirectExecutionReason
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
BTC = AssetId("BTC")
ETH = AssetId("ETH")
SOL = AssetId("SOL")
USDT = AssetId("USDT")

BTCUSDT = VenueInstrument(venue="binance", venue_symbol="BTCUSDT", base=BTC, quote=USDT)
ETHUSDT = VenueInstrument(venue="binance", venue_symbol="ETHUSDT", base=ETH, quote=USDT)
SOLUSDT = VenueInstrument(venue="binance", venue_symbol="SOLUSDT", base=SOL, quote=USDT)
INSTRUMENTS = (BTCUSDT, ETHUSDT, SOLUSDT)
PRICES = PriceSnapshot.from_prices(
    timestamp=AT,
    numeraire=USDT,
    prices={BTC: D("100"), ETH: D("50"), SOL: D("25"), USDT: D("1")},
)
REFERENCE_PRICES = {BTCUSDT: D("100"), ETHUSDT: D("50"), SOLUSDT: D("25")}
STARTING = PortfolioState.from_holdings(
    {BTC: D("1"), ETH: D("2"), SOL: D("4"), USDT: D("100")}
)
TARGET = AllocationTarget.for_basket(
    {BTC: D("0.4"), ETH: D("0.1"), SOL: D("0.2"), USDT: D("0.3")},
    basket={BTC, ETH, SOL, USDT},
)


def _metadata(
    instrument: VenueInstrument,
    *,
    step: str = "0.001",
    minimum_notional: str = "5",
) -> MarketMetadata:
    return MarketMetadata(
        instrument=instrument,
        status="TRADING",
        price_tick=D("0.01"),
        minimum_price=D("0.01"),
        maximum_price=D("1000000"),
        quantity_step=D(step),
        minimum_quantity=D(step),
        maximum_quantity=D("1000000"),
        minimum_notional=D(minimum_notional),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


METADATA = {
    BTCUSDT: _metadata(BTCUSDT),
    ETHUSDT: _metadata(ETHUSDT),
    SOLUSDT: _metadata(SOLUSDT),
}


def test_four_asset_rebalance_sells_then_buys_without_double_spending_bridge() -> None:
    from qap.execution.multi_asset import RebalancePhase, execute_multi_asset_rebalance

    result = execute_multi_asset_rebalance(
        decision_id="multi-1",
        execution_timestamp=AT,
        current_state=STARTING,
        target=TARGET,
        valuation_prices=PRICES,
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_metadata=METADATA,
        cost_model=CostModel(fee_bps=D("10"), slippage_bps=D("10")),
    )

    assert tuple(order.phase for order in result.orders) == (
        RebalancePhase.SELL_TO_BRIDGE,
        RebalancePhase.SELL_TO_BRIDGE,
        RebalancePhase.BUY_FROM_BRIDGE,
    )
    assert tuple(order.asset for order in result.orders) == (ETH, SOL, BTC)
    assert len(result.fills) == 3
    assert all(fill.fee_amount > 0 for fill in result.fills)
    assert all(fill.slippage_value > 0 for fill in result.fills)
    assert result.bridge_target_quantity == D("120")
    assert result.ending_state.quantity(USDT) >= result.bridge_target_quantity
    assert result.bridge_residual == (
        result.ending_state.quantity(USDT) - result.bridge_target_quantity
    )
    assert result.bridge_residual >= 0
    assert result.ending_state.quantity(BTC) > STARTING.quantity(BTC)
    assert result.ending_state.quantity(ETH) < STARTING.quantity(ETH)
    assert result.ending_state.quantity(SOL) < STARTING.quantity(SOL)
    assert all(quantity >= 0 for quantity in result.ending_state.holdings.values())

    from qap.experiment.reconciliation import reconcile_fill_sequence

    reconciliation = reconcile_fill_sequence(
        starting_state=STARTING,
        fills=result.fills,
        expected_states=result.states_after_fills,
    )
    assert reconciliation.matches is True
    assert reconciliation.ending_state == result.ending_state

    repeat = execute_multi_asset_rebalance(
        decision_id="multi-1",
        execution_timestamp=AT,
        current_state=STARTING,
        target=TARGET,
        valuation_prices=PRICES,
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_metadata=METADATA,
        cost_model=CostModel(fee_bps=D("10"), slippage_bps=D("10")),
    )
    assert repeat == result


def test_multi_asset_precision_no_fill_is_explicit_and_leaves_dust_owned() -> None:
    from qap.execution.multi_asset import execute_multi_asset_rebalance

    metadata = dict(METADATA)
    metadata[SOLUSDT] = _metadata(SOLUSDT, minimum_notional="25")

    result = execute_multi_asset_rebalance(
        decision_id="multi-min-notional",
        execution_timestamp=AT,
        current_state=STARTING,
        target=TARGET,
        valuation_prices=PRICES,
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_metadata=metadata,
        cost_model=CostModel.zero(),
    )

    sol_order = next(order for order in result.orders if order.asset == SOL)
    assert sol_order.fills == ()
    assert sol_order.leg_reason is DirectExecutionReason.BELOW_MINIMUM_NOTIONAL
    assert result.ending_state.quantity(SOL) == STARTING.quantity(SOL)
    assert result.ending_state.quantity(USDT) >= result.bridge_target_quantity


def test_multi_asset_preflights_all_order_data_before_any_execution() -> None:
    from qap.execution.multi_asset import (
        MultiAssetPreflightError,
        execute_multi_asset_rebalance,
    )

    references = dict(REFERENCE_PRICES)
    references.pop(BTCUSDT)

    with pytest.raises(MultiAssetPreflightError, match="BTC"):
        execute_multi_asset_rebalance(
            decision_id="multi-preflight",
            execution_timestamp=AT,
            current_state=STARTING,
            target=TARGET,
            valuation_prices=PRICES,
            bridge=USDT,
            instruments=INSTRUMENTS,
            reference_prices=references,
            market_metadata=METADATA,
            cost_model=CostModel.zero(),
        )
