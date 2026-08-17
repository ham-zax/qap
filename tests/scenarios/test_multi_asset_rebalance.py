from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, DirectExecutionReason
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.policy import RebalancePlan, build_rebalance_plan
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


def _plan(
    *,
    current_state: PortfolioState = STARTING,
    target: AllocationTarget = TARGET,
    prices: PriceSnapshot = PRICES,
    bridge: AssetId = USDT,
) -> RebalancePlan:
    return build_rebalance_plan(
        current_state=current_state,
        target=target,
        prices=prices,
        execution_only_bridge=bridge,
    )


def test_multi_asset_execution_consumes_policy_rebalance_plan() -> None:
    from qap.execution.multi_asset import execute_multi_asset_rebalance

    plan = build_rebalance_plan(
        current_state=STARTING,
        target=TARGET,
        prices=PRICES,
    )

    result = execute_multi_asset_rebalance(
        decision_id="multi-plan-authority",
        execution_timestamp=AT,
        plan=plan,
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
        market_metadata=METADATA,
        cost_model=CostModel.zero(),
    )

    assert result.starting_state is plan.current_state
    assert result.target is plan.target


def test_multi_asset_plan_rejects_omitted_held_non_bridge_asset() -> None:
    target = AllocationTarget.for_basket(
        {BTC: D("0.5"), ETH: D("0.5")},
        basket={BTC, ETH},
    )

    with pytest.raises(ValueError, match="explicit zero.*SOL"):
        build_rebalance_plan(
            current_state=STARTING,
            target=target,
            prices=PRICES,
            execution_only_bridge=USDT,
        )


def test_four_asset_rebalance_sells_then_buys_without_double_spending_bridge() -> None:
    from qap.execution.multi_asset import RebalancePhase, execute_multi_asset_rebalance

    result = execute_multi_asset_rebalance(
        decision_id="multi-1",
        execution_timestamp=AT,
        plan=_plan(),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
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
        plan=_plan(),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
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
        plan=_plan(),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
        market_metadata=metadata,
        cost_model=CostModel.zero(),
    )

    sol_order = next(order for order in result.orders if order.asset == SOL)
    assert sol_order.fills == ()
    assert sol_order.leg_reason is DirectExecutionReason.BELOW_MINIMUM_NOTIONAL
    assert result.ending_state.quantity(SOL) == STARTING.quantity(SOL)
    assert result.ending_state.quantity(USDT) >= result.bridge_target_quantity


def test_multi_asset_dry_preflights_all_precision_outcomes_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.execution.multi_asset as multi_asset

    metadata = dict(METADATA)
    metadata[SOLUSDT] = _metadata(SOLUSDT, minimum_notional="25")
    real_execute = multi_asset.execute_routed_conversion
    route_calls: list[str] = []

    def recording_execute(**kwargs: object) -> object:
        route = kwargs["route"]
        assert hasattr(route, "route_id")
        route_calls.append(route.route_id)  # type: ignore[attr-defined]
        return real_execute(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(multi_asset, "execute_routed_conversion", recording_execute)

    result = multi_asset.execute_multi_asset_rebalance(
        decision_id="multi-preflight-precision",
        execution_timestamp=AT,
        plan=_plan(),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
        market_metadata=metadata,
        cost_model=CostModel.zero(),
    )

    assert len(route_calls) == 6
    assert route_calls[:3] == route_calls[3:]
    sol = next(order for order in result.orders if order.asset == SOL)
    assert sol.leg_reason is DirectExecutionReason.BELOW_MINIMUM_NOTIONAL


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
            plan=_plan(),
            bridge=USDT,
            instruments=INSTRUMENTS,
            reference_prices=references,
            market_notional_reference_prices=REFERENCE_PRICES,
            market_metadata=METADATA,
            cost_model=CostModel.zero(),
        )


def test_execution_only_bridge_need_not_be_an_economic_target_asset() -> None:
    from qap.execution.multi_asset import execute_multi_asset_rebalance

    starting = PortfolioState.from_holdings({BTC: D("0"), ETH: D("2"), USDT: D("10")})
    target = AllocationTarget.for_basket(
        {BTC: D("0.5"), ETH: D("0.5")},
        basket={BTC, ETH},
    )
    prices = PriceSnapshot.from_prices(
        timestamp=AT,
        numeraire=USDT,
        prices={BTC: D("100"), ETH: D("50"), USDT: D("1")},
    )

    result = execute_multi_asset_rebalance(
        decision_id="execution-only-bridge",
        execution_timestamp=AT,
        plan=_plan(current_state=starting, target=target, prices=prices),
        bridge=USDT,
        instruments=(BTCUSDT, ETHUSDT),
        reference_prices={BTCUSDT: D("100"), ETHUSDT: D("50")},
        market_notional_reference_prices={BTCUSDT: D("100"), ETHUSDT: D("50")},
        market_metadata={BTCUSDT: METADATA[BTCUSDT], ETHUSDT: METADATA[ETHUSDT]},
        cost_model=CostModel.zero(),
    )

    assert result.bridge_target_quantity == D("0")
    assert result.fills
    assert result.ending_state.quantity(USDT) >= D("0")
    bridge_tracking = next(
        item for item in result.tracking_errors if item.asset == USDT
    )
    assert bridge_tracking.target_weight == D("0")
    assert bridge_tracking.actual_weight >= D("0")


def test_multi_asset_orders_by_descending_target_value_change_then_asset_key() -> None:
    from qap.execution.multi_asset import execute_multi_asset_rebalance

    target = AllocationTarget.for_basket(
        {BTC: D("0.45"), ETH: D("0.2"), SOL: D("0.05"), USDT: D("0.3")},
        basket={BTC, ETH, SOL, USDT},
    )

    result = execute_multi_asset_rebalance(
        decision_id="multi-ordering",
        execution_timestamp=AT,
        plan=_plan(target=target),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
        market_metadata=METADATA,
        cost_model=CostModel.zero(),
    )

    assert tuple(order.asset for order in result.orders) == (SOL, ETH, BTC)


def test_multi_asset_result_reports_authoritative_tracking_and_unfilled_remainder() -> (
    None
):
    from qap.execution.multi_asset import execute_multi_asset_rebalance

    metadata = dict(METADATA)
    metadata[SOLUSDT] = _metadata(SOLUSDT, minimum_notional="25")

    result = execute_multi_asset_rebalance(
        decision_id="multi-tracking",
        execution_timestamp=AT,
        plan=_plan(),
        bridge=USDT,
        instruments=INSTRUMENTS,
        reference_prices=REFERENCE_PRICES,
        market_notional_reference_prices=REFERENCE_PRICES,
        market_metadata=metadata,
        cost_model=CostModel.zero(),
    )

    assert tuple(item.asset for item in result.tracking_errors) == (BTC, ETH, SOL, USDT)
    sol_tracking = next(item for item in result.tracking_errors if item.asset == SOL)
    assert sol_tracking.unfilled_quantity != D("0")
    assert sol_tracking.unfilled_value != D("0")
    assert sol_tracking.weight_error != D("0")
