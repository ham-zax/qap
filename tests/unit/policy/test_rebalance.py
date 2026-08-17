from collections.abc import MutableMapping
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.market import PriceSnapshot
from qap.policy import (
    DecisionReason,
    build_rebalance_plan,
    filter_minimum_notional,
)
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
AS_OF = datetime(2024, 1, 1, 12, tzinfo=UTC)


def _prices(*, btc: str = "10", eth: str = "20") -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=AS_OF,
        numeraire=USDT,
        prices={BTC: D(btc), ETH: D(eth), USDT: D("1")},
    )


def _target(btc: str, eth: str) -> AllocationTarget:
    return AllocationTarget.for_basket(
        {BTC: D(btc), ETH: D(eth)},
        basket={BTC, ETH},
    )


def test_two_asset_fifty_fifty_target_quantities_are_hand_calculable() -> None:
    state = PortfolioState.from_holdings({BTC: D("10")})

    plan = build_rebalance_plan(
        current_state=state,
        target=_target("0.5", "0.5"),
        prices=_prices(),
    )

    assert plan.as_of == AS_OF
    assert plan.total_portfolio_value == D("100")
    assert dict(plan.target_values) == {BTC: D("50"), ETH: D("50")}
    assert dict(plan.target_quantities) == {BTC: D("5"), ETH: D("2.5")}
    assert dict(plan.quantity_deltas) == {BTC: D("-5"), ETH: D("2.5")}
    assert plan.one_way_rebalance_notional == D("50")
    assert dict(state.holdings) == {BTC: D("10")}


def test_partial_seventy_thirty_rebalance_retains_residual_inventory() -> None:
    plan = build_rebalance_plan(
        current_state=PortfolioState.from_holdings({BTC: D("10")}),
        target=_target("0.7", "0.3"),
        prices=_prices(),
    )

    assert dict(plan.target_quantities) == {BTC: D("7"), ETH: D("1.5")}
    assert dict(plan.quantity_deltas) == {BTC: D("-3"), ETH: D("1.5")}
    assert plan.one_way_rebalance_notional == D("30")


def test_planner_requires_explicit_zero_weight_for_every_current_holding() -> None:
    state = PortfolioState.from_holdings({BTC: D("10")})
    target = AllocationTarget.for_basket({ETH: D("1")}, basket={ETH})

    with pytest.raises(ValueError, match="explicit zero.*BTC"):
        build_rebalance_plan(current_state=state, target=target, prices=_prices())


def test_planner_allows_only_explicitly_declared_omitted_current_assets() -> None:
    state = PortfolioState.from_holdings({BTC: D("10"), USDT: D("25")})
    target = AllocationTarget.for_basket({BTC: D("1")}, basket={BTC})

    plan = build_rebalance_plan(
        current_state=state,
        target=target,
        prices=_prices(),
        execution_only_bridge=USDT,
    )

    assert plan.target is target
    assert plan.target_quantities[USDT] == D("0")
    assert plan.quantity_deltas[USDT] == D("-25")

    with pytest.raises(ValueError, match="explicit zero.*BTC"):
        build_rebalance_plan(
            current_state=PortfolioState.from_holdings({BTC: D("10"), USDT: D("25")}),
            target=AllocationTarget.for_basket({ETH: D("1")}, basket={ETH}),
            prices=_prices(),
            execution_only_bridge=USDT,
        )


def test_plan_mappings_are_read_only_and_context_independent() -> None:
    state = PortfolioState.from_holdings({BTC: D("9.85")})
    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        context.Emin = -2
        plan = build_rebalance_plan(
            current_state=state,
            target=_target("0.7", "0.3"),
            prices=_prices(btc="1.01", eth="2.02"),
        )

    assert plan == build_rebalance_plan(
        current_state=state,
        target=_target("0.7", "0.3"),
        prices=_prices(btc="1.01", eth="2.02"),
    )
    mutable = cast(MutableMapping[AssetId, Decimal], plan.quantity_deltas)
    with pytest.raises(TypeError):
        mutable[BTC] = D("0")


@pytest.mark.parametrize(
    ("minimum", "actionable", "reason"),
    [
        ("31", False, DecisionReason.BELOW_MINIMUM_NOTIONAL),
        ("30", True, None),
        ("29", True, None),
    ],
)
def test_minimum_notional_filter_has_exact_below_equal_and_above_behavior(
    minimum: str,
    actionable: bool,
    reason: DecisionReason | None,
) -> None:
    plan = build_rebalance_plan(
        current_state=PortfolioState.from_holdings({BTC: D("10")}),
        target=_target("0.7", "0.3"),
        prices=_prices(),
    )

    result = filter_minimum_notional(plan, D(minimum))

    assert result.actionable is actionable
    assert result.reason is reason
    assert result.requested_plan is plan
    assert result.selected_plan is (plan if actionable else None)


@given(
    total_units=st.integers(min_value=1, max_value=1_000_000),
    target_percent=st.integers(min_value=0, max_value=100),
)
def test_two_asset_planner_preserves_target_and_one_way_notional_algebra(
    total_units: int,
    target_percent: int,
) -> None:
    total = D(total_units)
    btc_weight = D(target_percent) / D("100")
    eth_weight = D(100 - target_percent) / D("100")
    state = PortfolioState.from_holdings({BTC: total})
    prices = _prices(btc="1", eth="1")

    plan = build_rebalance_plan(
        current_state=state,
        target=AllocationTarget.for_basket(
            {BTC: btc_weight, ETH: eth_weight},
            basket={BTC, ETH},
        ),
        prices=prices,
    )

    expected_btc = total * btc_weight
    expected_eth = total * eth_weight
    assert plan.target_quantities[BTC] == expected_btc
    assert plan.target_quantities[ETH] == expected_eth
    assert plan.quantity_deltas[BTC] == expected_btc - total
    assert plan.quantity_deltas[ETH] == expected_eth
    assert plan.one_way_rebalance_notional == expected_eth
    assert plan.target_values[BTC] + plan.target_values[ETH] == total
    assert dict(state.holdings) == {BTC: total}


@pytest.mark.parametrize("minimum", [D("-1"), D("NaN"), D("Infinity")])
def test_minimum_notional_filter_rejects_invalid_floors(minimum: Decimal) -> None:
    plan = build_rebalance_plan(
        current_state=PortfolioState.from_holdings({BTC: D("10")}),
        target=_target("0.7", "0.3"),
        prices=_prices(),
    )

    with pytest.raises(ValueError, match="finite and non-negative"):
        filter_minimum_notional(plan, minimum)
