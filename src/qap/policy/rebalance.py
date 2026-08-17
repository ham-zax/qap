"""Pure target-allocation planning without fills or inventory mutation."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import cast

from qap.market import PriceSnapshot
from qap.policy.decision import DecisionReason
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    PortfolioState,
    holding_values_at_prices,
    value_holdings_at_prices,
)
from qap.portfolio._decimal import divide, exact_multiply, exact_subtract, exact_sum

_ZERO = Decimal("0")
_HALF = Decimal("0.5")


def _frozen_mapping(
    values: Mapping[AssetId, Decimal],
) -> Mapping[AssetId, Decimal]:
    return MappingProxyType(dict(sorted(values.items())))


def _required_price(prices: PriceSnapshot, asset: AssetId) -> Decimal:
    try:
        return prices.price(asset)
    except KeyError as exc:
        raise ValueError(
            f"explicit price is required for target asset {asset.key}"
        ) from exc


@dataclass(frozen=True, slots=True, init=False)
class RebalancePlan:
    """Desired quantities and deltas fixed at one decision-time price snapshot."""

    as_of: datetime
    numeraire: AssetId
    current_state: PortfolioState
    target: AllocationTarget
    price_snapshot: PriceSnapshot
    total_portfolio_value: Decimal
    current_values: Mapping[AssetId, Decimal]
    target_values: Mapping[AssetId, Decimal]
    target_quantities: Mapping[AssetId, Decimal]
    quantity_deltas: Mapping[AssetId, Decimal]
    one_way_rebalance_notional: Decimal

    def __init__(self) -> None:
        raise TypeError("use build_rebalance_plan()")


def _new_rebalance_plan(
    *,
    current_state: PortfolioState,
    target: AllocationTarget,
    prices: PriceSnapshot,
    total_portfolio_value: Decimal,
    current_values: Mapping[AssetId, Decimal],
    target_values: Mapping[AssetId, Decimal],
    target_quantities: Mapping[AssetId, Decimal],
    quantity_deltas: Mapping[AssetId, Decimal],
    one_way_rebalance_notional: Decimal,
) -> RebalancePlan:
    result = object.__new__(RebalancePlan)
    object.__setattr__(result, "as_of", prices.timestamp)
    object.__setattr__(result, "numeraire", prices.numeraire)
    object.__setattr__(result, "current_state", current_state)
    object.__setattr__(result, "target", target)
    object.__setattr__(result, "price_snapshot", prices)
    object.__setattr__(result, "total_portfolio_value", total_portfolio_value)
    object.__setattr__(result, "current_values", _frozen_mapping(current_values))
    object.__setattr__(result, "target_values", _frozen_mapping(target_values))
    object.__setattr__(
        result,
        "target_quantities",
        _frozen_mapping(target_quantities),
    )
    object.__setattr__(
        result,
        "quantity_deltas",
        _frozen_mapping(quantity_deltas),
    )
    object.__setattr__(
        result,
        "one_way_rebalance_notional",
        one_way_rebalance_notional,
    )
    return result


@dataclass(frozen=True, slots=True, init=False)
class RebalanceFilterResult:
    """Diagnostic result preserving a requested plan even when filtered out."""

    requested_plan: RebalancePlan
    selected_plan: RebalancePlan | None
    reason: DecisionReason | None

    def __init__(self) -> None:
        raise TypeError("use filter_minimum_notional()")

    @property
    def actionable(self) -> bool:
        return self.selected_plan is not None


def _new_filter_result(
    *,
    requested_plan: RebalancePlan,
    selected_plan: RebalancePlan | None,
    reason: DecisionReason | None,
) -> RebalanceFilterResult:
    result = object.__new__(RebalanceFilterResult)
    object.__setattr__(result, "requested_plan", requested_plan)
    object.__setattr__(result, "selected_plan", selected_plan)
    object.__setattr__(result, "reason", reason)
    return result


def build_rebalance_plan(
    *,
    current_state: PortfolioState,
    target: AllocationTarget,
    prices: PriceSnapshot,
    execution_only_bridge: AssetId | None = None,
) -> RebalancePlan:
    """Translate one target allocation into immutable desired quantities."""

    if not isinstance(cast(object, current_state), PortfolioState):
        raise TypeError("current_state must be a PortfolioState")
    if not isinstance(cast(object, target), AllocationTarget):
        raise TypeError("target must be an AllocationTarget")
    if not isinstance(cast(object, prices), PriceSnapshot):
        raise TypeError("prices must be a PriceSnapshot")

    if execution_only_bridge is not None and not isinstance(
        cast(object, execution_only_bridge), AssetId
    ):
        raise TypeError("execution_only_bridge must be AssetId or None")

    target_weights = target.weights
    missing_current_assets = sorted(
        asset
        for asset in current_state.holdings
        if asset not in target_weights and asset != execution_only_bridge
    )
    if missing_current_assets:
        missing = ", ".join(asset.key for asset in missing_current_assets)
        raise ValueError(
            "target must include an explicit zero weight for every current "
            f"holding; missing: {missing}"
        )

    held_values = holding_values_at_prices(current_state, prices.prices)
    total_value = value_holdings_at_prices(current_state, prices.prices)
    assets = tuple(sorted(set(current_state.holdings) | set(target_weights)))

    current_values: dict[AssetId, Decimal] = {}
    target_values: dict[AssetId, Decimal] = {}
    target_quantities: dict[AssetId, Decimal] = {}
    quantity_deltas: dict[AssetId, Decimal] = {}
    absolute_value_deltas: list[Decimal] = []

    for asset in assets:
        price = _required_price(prices, asset)
        current_value = held_values.get(asset, _ZERO)
        weight = target_weights.get(asset, _ZERO)
        target_value = exact_multiply(total_value, weight)
        target_quantity = divide(target_value, price)
        quantity_delta = exact_subtract(
            target_quantity,
            current_state.quantity(asset),
        )

        current_values[asset] = current_value
        target_values[asset] = target_value
        target_quantities[asset] = target_quantity
        quantity_deltas[asset] = quantity_delta
        absolute_value_deltas.append(
            exact_subtract(target_value, current_value).copy_abs()
        )

    one_way_notional = exact_multiply(exact_sum(absolute_value_deltas), _HALF)
    return _new_rebalance_plan(
        current_state=current_state,
        target=target,
        prices=prices,
        total_portfolio_value=total_value,
        current_values=current_values,
        target_values=target_values,
        target_quantities=target_quantities,
        quantity_deltas=quantity_deltas,
        one_way_rebalance_notional=one_way_notional,
    )


def filter_minimum_notional(
    plan: RebalancePlan,
    minimum_notional: Decimal,
) -> RebalanceFilterResult:
    """Select a plan only when its one-way notional meets the explicit floor."""

    if not isinstance(cast(object, plan), RebalancePlan):
        raise TypeError("plan must be a RebalancePlan")
    if not isinstance(cast(object, minimum_notional), Decimal):
        raise TypeError("minimum_notional must be Decimal")
    if not minimum_notional.is_finite() or minimum_notional < _ZERO:
        raise ValueError("minimum_notional must be finite and non-negative")

    if plan.one_way_rebalance_notional < minimum_notional:
        return _new_filter_result(
            requested_plan=plan,
            selected_plan=None,
            reason=DecisionReason.BELOW_MINIMUM_NOTIONAL,
        )
    return _new_filter_result(
        requested_plan=plan,
        selected_plan=plan,
        reason=None,
    )
