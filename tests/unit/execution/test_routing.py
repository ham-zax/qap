from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.execution import CostModel, FillSide
from qap.market import MarketMetadata, VenueInstrument
from qap.portfolio import AssetId, PortfolioState

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
SOL = AssetId("SOL")

ETHBTC = VenueInstrument(
    venue="binance",
    venue_symbol="ETHBTC",
    base=ETH,
    quote=BTC,
)
ETHUSDT = VenueInstrument(
    venue="binance",
    venue_symbol="ETHUSDT",
    base=ETH,
    quote=USDT,
)
BTCUSDT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)
AT = datetime(2024, 1, 1, 1, tzinfo=UTC)
D = Decimal


def _metadata(instrument: VenueInstrument, *, step: str) -> MarketMetadata:
    return MarketMetadata(
        instrument=instrument,
        status="TRADING",
        price_tick=D("0.01"),
        minimum_price=D("0.01"),
        maximum_price=D("1000000"),
        quantity_step=D(step),
        minimum_quantity=D(step),
        maximum_quantity=D("1000000"),
        minimum_notional=D("5"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


def test_direct_route_is_preferred_even_when_bridge_is_declared() -> None:
    from qap.execution.routing import plan_execution_route

    route = plan_execution_route(
        source=ETH,
        destination=BTC,
        instruments=(ETHUSDT, BTCUSDT, ETHBTC),
        declared_assets={ETH, BTC, USDT},
        bridge=USDT,
    )

    assert route.bridge is None
    assert len(route.legs) == 1
    assert route.legs[0].instrument == ETHBTC
    assert route.legs[0].side is FillSide.SELL
    assert route.legs[0].source == ETH
    assert route.legs[0].destination == BTC
    assert route.route_id == "direct:ETH>BTC:binance:ETHBTC:sell"


def test_inverse_direct_market_uses_buy_side_without_synthetic_price() -> None:
    from qap.execution.routing import plan_execution_route

    route = plan_execution_route(
        source=BTC,
        destination=ETH,
        instruments=(ETHBTC,),
        declared_assets={ETH, BTC},
    )

    assert len(route.legs) == 1
    assert route.legs[0].instrument == ETHBTC
    assert route.legs[0].side is FillSide.BUY
    assert route.legs[0].source == BTC
    assert route.legs[0].destination == ETH
    assert route.route_id == "direct:BTC>ETH:binance:ETHBTC:buy"


def test_one_declared_bridge_returns_exactly_two_real_spot_legs() -> None:
    from qap.execution.routing import plan_execution_route

    route = plan_execution_route(
        source=ETH,
        destination=BTC,
        instruments=(ETHUSDT, BTCUSDT),
        declared_assets={ETH, BTC, USDT},
        bridge=USDT,
    )

    assert route.bridge == USDT
    assert tuple((leg.source, leg.destination) for leg in route.legs) == (
        (ETH, USDT),
        (USDT, BTC),
    )
    assert tuple(leg.side for leg in route.legs) == (FillSide.SELL, FillSide.BUY)
    assert route.route_id == (
        "bridge:ETH>USDT>BTC:binance:ETHUSDT:sell|binance:BTCUSDT:buy"
    )


def test_missing_second_bridge_leg_fails_unsupported_route() -> None:
    from qap.execution.routing import (
        RoutePlanningError,
        RoutingReason,
        plan_execution_route,
    )

    with pytest.raises(RoutePlanningError) as error:
        plan_execution_route(
            source=ETH,
            destination=BTC,
            instruments=(ETHUSDT,),
            declared_assets={ETH, BTC, USDT},
            bridge=USDT,
        )

    assert error.value.reason is RoutingReason.UNSUPPORTED_ROUTE


def test_bridge_must_be_explicitly_admitted_for_transient_ownership() -> None:
    from qap.execution.routing import (
        RoutePlanningError,
        RoutingReason,
        plan_execution_route,
    )

    with pytest.raises(RoutePlanningError) as error:
        plan_execution_route(
            source=ETH,
            destination=BTC,
            instruments=(ETHUSDT, BTCUSDT),
            declared_assets={ETH, BTC},
            bridge=USDT,
        )

    assert error.value.reason is RoutingReason.UNDECLARED_BRIDGE


def test_two_leg_execution_charges_costs_twice_and_uses_actual_bridge_output() -> None:
    from qap.execution.routing import execute_routed_conversion, plan_execution_route

    route = plan_execution_route(
        source=ETH,
        destination=BTC,
        instruments=(ETHUSDT, BTCUSDT),
        declared_assets={ETH, BTC, USDT},
        bridge=USDT,
    )
    starting = PortfolioState.from_holdings({ETH: D("2")})

    result = execute_routed_conversion(
        route=route,
        fill_id_prefix="bridge-conversion",
        decision_id="decision-1",
        execution_timestamp=AT,
        source_quantity=D("2"),
        current_state=starting,
        reference_prices={ETHUSDT: D("2000"), BTCUSDT: D("40000")},
        market_metadata={
            ETHUSDT: _metadata(ETHUSDT, step="0.001"),
            BTCUSDT: _metadata(BTCUSDT, step="0.000001"),
        },
        cost_model=CostModel(fee_bps=D("10"), slippage_bps=D("20")),
    )

    assert result.reason is None
    assert len(result.fills) == 2
    assert result.intermediate_state is not None
    first, second = result.fills
    assert first.side is FillSide.SELL
    assert second.side is FillSide.BUY
    assert first.fee_amount > 0 and second.fee_amount > 0
    assert first.slippage_value > 0 and second.slippage_value > 0
    actual_bridge_output = first.balance_deltas[USDT]
    assert actual_bridge_output > 0
    assert result.intermediate_state.quantity(USDT) == actual_bridge_output
    assert -second.balance_deltas[USDT] <= actual_bridge_output
    assert result.bridge_residue == result.ending_state.quantity(USDT)
    assert result.bridge_residue >= 0
    assert result.ending_state.quantity(ETH) == 0
    assert result.ending_state.quantity(BTC) > 0


def test_two_leg_route_preflights_all_reference_prices_before_any_fill() -> None:
    from qap.execution.routing import (
        RoutedExecutionReason,
        execute_routed_conversion,
        plan_execution_route,
    )

    route = plan_execution_route(
        source=ETH,
        destination=BTC,
        instruments=(ETHUSDT, BTCUSDT),
        declared_assets={ETH, BTC, USDT},
        bridge=USDT,
    )
    starting = PortfolioState.from_holdings({ETH: D("2")})

    result = execute_routed_conversion(
        route=route,
        fill_id_prefix="missing-price",
        decision_id="decision-2",
        execution_timestamp=AT,
        source_quantity=D("2"),
        current_state=starting,
        reference_prices={ETHUSDT: D("2000")},
        market_metadata={
            ETHUSDT: _metadata(ETHUSDT, step="0.001"),
            BTCUSDT: _metadata(BTCUSDT, step="0.000001"),
        },
        cost_model=CostModel.zero(),
    )

    assert result.reason is RoutedExecutionReason.MISSING_REFERENCE_PRICE
    assert result.failed_leg_index == 1
    assert result.fills == ()
    assert result.intermediate_state is None
    assert result.ending_state == starting


def test_two_leg_route_preflights_all_metadata_before_any_fill() -> None:
    from qap.execution.routing import (
        RoutedExecutionReason,
        execute_routed_conversion,
        plan_execution_route,
    )

    route = plan_execution_route(
        source=ETH,
        destination=BTC,
        instruments=(ETHUSDT, BTCUSDT),
        declared_assets={ETH, BTC, USDT},
        bridge=USDT,
    )
    starting = PortfolioState.from_holdings({ETH: D("2")})

    result = execute_routed_conversion(
        route=route,
        fill_id_prefix="missing-metadata",
        decision_id="decision-3",
        execution_timestamp=AT,
        source_quantity=D("2"),
        current_state=starting,
        reference_prices={ETHUSDT: D("2000"), BTCUSDT: D("40000")},
        market_metadata={ETHUSDT: _metadata(ETHUSDT, step="0.001")},
        cost_model=CostModel.zero(),
    )

    assert result.reason is RoutedExecutionReason.MISSING_MARKET_METADATA
    assert result.failed_leg_index == 1
    assert result.fills == ()
    assert result.ending_state == starting


def test_route_rejects_same_asset_conversion() -> None:
    from qap.execution.routing import plan_execution_route

    with pytest.raises(ValueError, match="must differ"):
        plan_execution_route(
            source=SOL,
            destination=SOL,
            instruments=(ETHUSDT, BTCUSDT),
            declared_assets={SOL, USDT},
            bridge=USDT,
        )
