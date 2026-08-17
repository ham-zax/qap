from datetime import UTC, datetime
from decimal import Decimal

from qap.policy import DecisionReason, ScheduledTargetPolicy
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
STATE = PortfolioState.from_holdings({BTC: D("10")})
TARGET = AllocationTarget.for_basket(
    {BTC: D("0.6"), ETH: D("0.4")},
    basket={BTC, ETH},
)
TRIGGER = datetime(2024, 1, 1, 12, tzinfo=UTC)


def test_scheduled_policy_triggers_only_at_the_exact_declared_timestamp() -> None:
    policy = ScheduledTargetPolicy(
        policy_id="fixture-schedule-v1",
        schedule={TRIGGER: TARGET},
    )

    triggered = policy.decide(as_of=TRIGGER, current_state=STATE)
    not_triggered = policy.decide(
        as_of=datetime(2024, 1, 1, 12, 0, 0, 1, tzinfo=UTC),
        current_state=STATE,
    )

    assert triggered.target == TARGET
    assert triggered.reason is DecisionReason.SCHEDULED_TARGET
    assert triggered.decision_id == "fixture-schedule-v1:2024-01-01T12:00:00+00:00"
    assert not_triggered.target is None
    assert not_triggered.reason is DecisionReason.NOT_SCHEDULED


def test_scheduled_policy_copies_configuration_and_is_repeatable() -> None:
    source = {TRIGGER: TARGET}
    policy = ScheduledTargetPolicy(policy_id="fixture-schedule-v1", schedule=source)
    source.clear()

    first = policy.decide(as_of=TRIGGER, current_state=STATE, evidence_ids=("b", "a"))
    second = policy.decide(as_of=TRIGGER, current_state=STATE, evidence_ids=("a", "b"))

    assert first == second
