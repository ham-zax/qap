"""Deterministic multi-asset paper rebalance through one settlement asset."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.execution.costs import CostModel
from qap.execution.direct import DirectExecutionReason
from qap.execution.fills import Fill
from qap.execution.routing import (
    ExecutionRoute,
    RoutePlanningError,
    execute_routed_conversion,
    plan_execution_route,
)
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    PortfolioState,
    holding_values_at_prices,
    value_holdings_at_prices,
)
from qap.portfolio._decimal import (
    canonical_decimal,
    divide,
    exact_multiply,
    exact_subtract,
    exact_sum,
)

_ZERO = Decimal("0")


class RebalancePhase(StrEnum):
    """Deterministic ordering phases for one settlement-asset rebalance."""

    SELL_TO_BRIDGE = "sell_to_bridge"
    BUY_FROM_BRIDGE = "buy_from_bridge"


class MultiAssetPreflightError(ValueError):
    """Raised before execution when any required order lacks route data."""

    def __init__(self, asset: AssetId, detail: str) -> None:
        self.asset = asset
        self.detail = detail
        super().__init__(f"{asset.key}: {detail}")


@dataclass(frozen=True, slots=True)
class MultiAssetOrderOutcome:
    """One deterministic sell/buy intent and its realized routed fills."""

    phase: RebalancePhase
    asset: AssetId
    route_id: str
    requested_source_quantity: Decimal
    fills: tuple[Fill, ...]
    leg_reason: DirectExecutionReason | None


@dataclass(frozen=True, slots=True)
class MultiAssetTrackingError:
    """Authoritative terminal deviation from one requested economic target."""

    asset: AssetId
    target_weight: Decimal
    actual_weight: Decimal
    weight_error: Decimal
    unfilled_quantity: Decimal
    unfilled_value: Decimal


@dataclass(frozen=True, slots=True)
class MultiAssetRebalanceResult:
    """Complete immutable outcome for one target-weight paper rebalance."""

    starting_state: PortfolioState
    ending_state: PortfolioState
    target: AllocationTarget
    bridge: AssetId
    bridge_target_quantity: Decimal
    bridge_residual: Decimal
    orders: tuple[MultiAssetOrderOutcome, ...]
    fills: tuple[Fill, ...]
    states_after_fills: tuple[PortfolioState, ...]
    tracking_errors: tuple[MultiAssetTrackingError, ...]


@dataclass(frozen=True, slots=True)
class _PlannedOrder:
    phase: RebalancePhase
    asset: AssetId
    route: ExecutionRoute
    quantity_delta: Decimal
    absolute_target_value_change: Decimal


@dataclass(frozen=True, slots=True)
class _ExecutionPass:
    ending_state: PortfolioState
    orders: tuple[MultiAssetOrderOutcome, ...]
    fills: tuple[Fill, ...]
    states_after_fills: tuple[PortfolioState, ...]


def _target_quantity(
    *,
    portfolio_value: Decimal,
    target_weight: Decimal,
    price: Decimal,
) -> Decimal:
    target_value = exact_multiply(portfolio_value, target_weight)
    return divide(target_value, price)


def _quantity_deltas(
    current_state: PortfolioState,
    *,
    target: AllocationTarget,
    prices: PriceSnapshot,
) -> tuple[Decimal, dict[AssetId, Decimal]]:
    total_value = value_holdings_at_prices(current_state, prices.prices)
    deltas: dict[AssetId, Decimal] = {}
    for asset, target_weight in target.weights.items():
        desired = _target_quantity(
            portfolio_value=total_value,
            target_weight=target_weight,
            price=prices.price(asset),
        )
        deltas[asset] = exact_subtract(desired, current_state.quantity(asset))
    return total_value, deltas


def _plan_orders(
    *,
    deltas: Mapping[AssetId, Decimal],
    bridge: AssetId,
    instruments: tuple[VenueInstrument, ...],
    declared_assets: frozenset[AssetId],
    valuation_prices: PriceSnapshot,
) -> tuple[_PlannedOrder, ...]:
    sells: list[_PlannedOrder] = []
    buys: list[_PlannedOrder] = []
    for asset in deltas:
        if asset == bridge:
            continue
        delta = deltas[asset]
        if delta == _ZERO:
            continue
        try:
            route = plan_execution_route(
                source=asset if delta < _ZERO else bridge,
                destination=bridge if delta < _ZERO else asset,
                instruments=instruments,
                declared_assets=declared_assets,
            )
        except RoutePlanningError as exc:
            raise MultiAssetPreflightError(asset, exc.reason.value) from exc
        order = _PlannedOrder(
            phase=(
                RebalancePhase.SELL_TO_BRIDGE
                if delta < _ZERO
                else RebalancePhase.BUY_FROM_BRIDGE
            ),
            asset=asset,
            route=route,
            quantity_delta=delta,
            absolute_target_value_change=exact_multiply(
                delta.copy_abs(), valuation_prices.price(asset)
            ),
        )
        (sells if delta < _ZERO else buys).append(order)

    def order_key(order: _PlannedOrder) -> tuple[Decimal, str]:
        return (-order.absolute_target_value_change, order.asset.key)

    return tuple(sorted(sells, key=order_key) + sorted(buys, key=order_key))


def _preflight_order_data(
    orders: tuple[_PlannedOrder, ...],
    *,
    reference_prices: Mapping[VenueInstrument, Decimal],
    market_notional_reference_prices: Mapping[VenueInstrument, Decimal],
    market_metadata: Mapping[VenueInstrument, MarketMetadata],
) -> None:
    for order in orders:
        for leg in order.route.legs:
            if leg.instrument not in reference_prices:
                raise MultiAssetPreflightError(order.asset, "missing_reference_price")
            metadata = market_metadata.get(leg.instrument)
            if metadata is None:
                raise MultiAssetPreflightError(order.asset, "missing_market_metadata")
            if metadata.instrument != leg.instrument:
                raise MultiAssetPreflightError(
                    order.asset, "metadata_instrument_mismatch"
                )
            if (
                metadata.requires_market_notional_reference_price
                and leg.instrument not in market_notional_reference_prices
            ):
                raise MultiAssetPreflightError(
                    order.asset, "missing_notional_reference_price"
                )


def _validated_instruments(
    values: Iterable[VenueInstrument],
) -> tuple[VenueInstrument, ...]:
    try:
        copied = tuple(values)
    except TypeError as exc:
        raise TypeError("instruments must be iterable") from exc
    if any(not isinstance(cast(object, item), VenueInstrument) for item in copied):
        raise TypeError("instruments members must be VenueInstrument")
    return copied


def _tracking_errors(
    *,
    portfolio_value: Decimal,
    ending_state: PortfolioState,
    target: AllocationTarget,
    bridge: AssetId,
    prices: PriceSnapshot,
) -> tuple[MultiAssetTrackingError, ...]:
    values = holding_values_at_prices(ending_state, prices.prices)
    ending_value = exact_sum(values.values())
    assets = tuple(sorted(set(target.weights) | set(ending_state.holdings) | {bridge}))
    result: list[MultiAssetTrackingError] = []
    for asset in assets:
        target_weight = target.weights.get(asset, _ZERO)
        target_value = exact_multiply(portfolio_value, target_weight)
        target_quantity = divide(target_value, prices.price(asset))
        actual_quantity = ending_state.quantity(asset)
        actual_value = values.get(asset, _ZERO)
        actual_weight = (
            divide(actual_value, ending_value) if ending_value > _ZERO else _ZERO
        )
        result.append(
            MultiAssetTrackingError(
                asset=asset,
                target_weight=target_weight,
                actual_weight=actual_weight,
                weight_error=exact_subtract(actual_weight, target_weight),
                unfilled_quantity=exact_subtract(target_quantity, actual_quantity),
                unfilled_value=exact_subtract(target_value, actual_value),
            )
        )
    return tuple(result)


def _bridge_budget_for_buy(
    *,
    quantity_delta: Decimal,
    asset_price: Decimal,
    bridge_price: Decimal,
) -> Decimal:
    desired_value = exact_multiply(quantity_delta, asset_price)
    return divide(desired_value, bridge_price)


def _execute_planned_orders(
    *,
    planned: tuple[_PlannedOrder, ...],
    decision_id: str,
    execution_timestamp: datetime,
    starting_state: PortfolioState,
    bridge: AssetId,
    bridge_target: Decimal,
    valuation_prices: PriceSnapshot,
    reference_prices: Mapping[VenueInstrument, Decimal],
    market_notional_reference_prices: Mapping[VenueInstrument, Decimal],
    market_metadata: Mapping[VenueInstrument, MarketMetadata],
    cost_model: CostModel,
) -> _ExecutionPass:
    state = starting_state
    outcomes: list[MultiAssetOrderOutcome] = []
    fills: list[Fill] = []
    states_after_fills: list[PortfolioState] = []
    for order_index, order in enumerate(planned):
        if order.phase is RebalancePhase.SELL_TO_BRIDGE:
            requested_source = canonical_decimal(-order.quantity_delta)
        else:
            desired_budget = _bridge_budget_for_buy(
                quantity_delta=order.quantity_delta,
                asset_price=valuation_prices.price(order.asset),
                bridge_price=valuation_prices.price(bridge),
            )
            spendable = exact_subtract(state.quantity(bridge), bridge_target)
            if spendable <= _ZERO:
                outcomes.append(
                    MultiAssetOrderOutcome(
                        phase=order.phase,
                        asset=order.asset,
                        route_id=order.route.route_id,
                        requested_source_quantity=_ZERO,
                        fills=(),
                        leg_reason=DirectExecutionReason.INSUFFICIENT_BALANCE,
                    )
                )
                continue
            requested_source = min(desired_budget, spendable)

        routed = execute_routed_conversion(
            route=order.route,
            fill_id_prefix=f"{decision_id}:order-{order_index + 1}",
            decision_id=decision_id,
            execution_timestamp=execution_timestamp,
            source_quantity=requested_source,
            current_state=state,
            reference_prices=reference_prices,
            market_notional_reference_prices=market_notional_reference_prices,
            market_metadata=market_metadata,
            cost_model=cost_model,
        )
        state = routed.ending_state
        fills.extend(routed.fills)
        if routed.fills:
            if len(routed.fills) == 2:
                if routed.intermediate_state is None:
                    raise ValueError("two-fill route must expose intermediate state")
                states_after_fills.append(routed.intermediate_state)
            states_after_fills.append(routed.ending_state)
        outcomes.append(
            MultiAssetOrderOutcome(
                phase=order.phase,
                asset=order.asset,
                route_id=order.route.route_id,
                requested_source_quantity=requested_source,
                fills=routed.fills,
                leg_reason=routed.leg_reason,
            )
        )
    return _ExecutionPass(
        ending_state=state,
        orders=tuple(outcomes),
        fills=tuple(fills),
        states_after_fills=tuple(states_after_fills),
    )


def execute_multi_asset_rebalance(
    *,
    decision_id: str,
    execution_timestamp: datetime,
    current_state: PortfolioState,
    target: AllocationTarget,
    valuation_prices: PriceSnapshot,
    bridge: AssetId,
    instruments: Iterable[VenueInstrument],
    reference_prices: Mapping[VenueInstrument, Decimal],
    market_notional_reference_prices: Mapping[VenueInstrument, Decimal],
    market_metadata: Mapping[VenueInstrument, MarketMetadata],
    cost_model: CostModel,
) -> MultiAssetRebalanceResult:
    """Sell overweights into bridge first, then fund underweights deterministically."""

    if not isinstance(cast(object, current_state), PortfolioState):
        raise TypeError("current_state must be PortfolioState")
    if not isinstance(cast(object, target), AllocationTarget):
        raise TypeError("target must be AllocationTarget")
    if not isinstance(cast(object, valuation_prices), PriceSnapshot):
        raise TypeError("valuation_prices must be PriceSnapshot")
    if not isinstance(cast(object, bridge), AssetId):
        raise TypeError("bridge must be AssetId")
    available = _validated_instruments(instruments)
    declared_assets = frozenset((*target.weights, bridge))
    total_value, deltas = _quantity_deltas(
        current_state,
        target=target,
        prices=valuation_prices,
    )
    planned = _plan_orders(
        deltas=deltas,
        bridge=bridge,
        instruments=available,
        declared_assets=declared_assets,
        valuation_prices=valuation_prices,
    )
    _preflight_order_data(
        planned,
        reference_prices=reference_prices,
        market_notional_reference_prices=market_notional_reference_prices,
        market_metadata=market_metadata,
    )

    bridge_target = _target_quantity(
        portfolio_value=total_value,
        target_weight=target.weights.get(bridge, _ZERO),
        price=valuation_prices.price(bridge),
    )
    # First pass is a complete immutable shadow execution: all route, precision,
    # cost, and settlement-balance outcomes are known before accepted fills exist.
    preview = _execute_planned_orders(
        planned=planned,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        starting_state=current_state,
        bridge=bridge,
        bridge_target=bridge_target,
        valuation_prices=valuation_prices,
        reference_prices=reference_prices,
        market_notional_reference_prices=market_notional_reference_prices,
        market_metadata=market_metadata,
        cost_model=cost_model,
    )
    executed = _execute_planned_orders(
        planned=planned,
        decision_id=decision_id,
        execution_timestamp=execution_timestamp,
        starting_state=current_state,
        bridge=bridge,
        bridge_target=bridge_target,
        valuation_prices=valuation_prices,
        reference_prices=reference_prices,
        market_notional_reference_prices=market_notional_reference_prices,
        market_metadata=market_metadata,
        cost_model=cost_model,
    )
    if executed != preview:
        raise RuntimeError(
            "multi-asset execution diverged from deterministic preflight"
        )

    residual = exact_subtract(executed.ending_state.quantity(bridge), bridge_target)
    return MultiAssetRebalanceResult(
        starting_state=current_state,
        ending_state=executed.ending_state,
        target=target,
        bridge=bridge,
        bridge_target_quantity=bridge_target,
        bridge_residual=residual,
        orders=executed.orders,
        fills=executed.fills,
        states_after_fills=executed.states_after_fills,
        tracking_errors=_tracking_errors(
            portfolio_value=total_value,
            ending_state=executed.ending_state,
            target=target,
            bridge=bridge,
            prices=valuation_prices,
        ),
    )


__all__ = [
    "MultiAssetOrderOutcome",
    "MultiAssetPreflightError",
    "MultiAssetRebalanceResult",
    "MultiAssetTrackingError",
    "RebalancePhase",
    "execute_multi_asset_rebalance",
]
