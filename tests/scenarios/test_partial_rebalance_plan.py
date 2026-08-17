from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qap.market import PriceSnapshot
from qap.policy import (
    DecisionReason,
    ScheduledTargetPolicy,
    build_rebalance_plan,
)
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal
X = AssetId("X")
Y = AssetId("Y")
USD = AssetId("USD")
PRICES = PriceSnapshot.from_prices(
    timestamp=datetime(2024, 1, 1, tzinfo=UTC),
    numeraire=USD,
    prices={X: D("10"), Y: D("20"), USD: D("1")},
)
START = PortfolioState.from_holdings({X: D("10")})


def _target(x: str, y: str) -> AllocationTarget:
    return AllocationTarget.for_basket(
        {X: D(x), Y: D(y)},
        basket={X, Y},
    )


def test_partial_and_full_rotation_use_the_same_allocation_planner() -> None:
    partial = build_rebalance_plan(
        current_state=START,
        target=_target("0.6", "0.4"),
        prices=PRICES,
    )
    full_rotation = build_rebalance_plan(
        current_state=START,
        target=_target("0", "1"),
        prices=PRICES,
    )

    assert partial.target_quantities[X] == D("6")
    assert partial.target_quantities[Y] == D("2")
    assert partial.quantity_deltas[X] == D("-4")
    assert partial.quantity_deltas[Y] == D("2")
    assert full_rotation.target_quantities[X] == D("0")
    assert full_rotation.target_quantities[Y] == D("5")
    assert full_rotation.quantity_deltas[X] == D("-10")
    assert full_rotation.quantity_deltas[Y] == D("5")
    assert dict(START.holdings) == {X: D("10")}


def test_unscheduled_time_is_explicit_no_action_without_inventory_mutation() -> None:
    trigger = datetime(2024, 1, 1, 12, tzinfo=UTC)
    policy = ScheduledTargetPolicy(
        policy_id="scenario-schedule-v1",
        schedule={trigger: _target("0.6", "0.4")},
    )

    decision = policy.decide(
        as_of=trigger + timedelta(hours=1),
        current_state=START,
    )

    assert decision.no_action is True
    assert decision.target is None
    assert decision.reason is DecisionReason.NOT_SCHEDULED
    assert dict(START.holdings) == {X: D("10")}
