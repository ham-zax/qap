from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from qap.policy import DecisionReason, PolicyDecision
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
STATE = PortfolioState.from_holdings({BTC: D("1")})
TARGET = AllocationTarget.for_basket(
    {BTC: D("0.6"), ETH: D("0.4")},
    basket={BTC, ETH},
)


def test_target_decision_is_immutable_and_canonicalizes_evidence_ids() -> None:
    zero_offset = timezone(timedelta(0), name="ZERO")
    decision = PolicyDecision.for_target(
        decision_id="decision-1",
        as_of=datetime(2024, 1, 1, 12, tzinfo=zero_offset),
        policy_id="scheduled-v1",
        current_state=STATE,
        target=TARGET,
        reason=DecisionReason.SCHEDULED_TARGET,
        evidence_ids=("z", "a", "z"),
    )

    assert decision.as_of == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert decision.as_of.tzinfo is UTC
    assert decision.target == TARGET
    assert decision.evidence_ids == ("a", "z")
    assert decision.no_action is False
    with pytest.raises(FrozenInstanceError):
        setattr(decision, "target", None)


def test_no_action_is_explicit_without_a_fake_current_target() -> None:
    decision = PolicyDecision.no_action_decision(
        decision_id="decision-2",
        as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
        policy_id="scheduled-v1",
        current_state=STATE,
        reason=DecisionReason.NOT_SCHEDULED,
    )

    assert decision.target is None
    assert decision.no_action is True
    assert decision.reason is DecisionReason.NOT_SCHEDULED


def test_decision_rejects_target_and_reason_mismatches() -> None:
    with pytest.raises(ValueError, match="target reason"):
        PolicyDecision.no_action_decision(
            decision_id="bad",
            as_of=datetime(2024, 1, 1, tzinfo=UTC),
            policy_id="scheduled-v1",
            current_state=STATE,
            reason=DecisionReason.SCHEDULED_TARGET,
        )
    with pytest.raises(ValueError, match="no-action reason"):
        PolicyDecision.for_target(
            decision_id="bad",
            as_of=datetime(2024, 1, 1, tzinfo=UTC),
            policy_id="scheduled-v1",
            current_state=STATE,
            target=TARGET,
            reason=DecisionReason.NOT_SCHEDULED,
        )
