"""Immutable policy intent with explicit reasons and evidence provenance."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Self, cast

from qap.portfolio import AllocationTarget, PortfolioState


class DecisionReason(StrEnum):
    """Finite reasons for target or no-action policy decisions."""

    SCHEDULED_TARGET = "scheduled_target"
    EVIDENCE_TARGET = "evidence_target"
    NOT_SCHEDULED = "not_scheduled"
    BELOW_THRESHOLD = "below_threshold"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BELOW_MINIMUM_NOTIONAL = "below_minimum_notional"


_TARGET_REASONS = frozenset(
    {
        DecisionReason.SCHEDULED_TARGET,
        DecisionReason.EVIDENCE_TARGET,
    }
)
_NO_ACTION_REASONS = frozenset(
    {
        DecisionReason.NOT_SCHEDULED,
        DecisionReason.BELOW_THRESHOLD,
        DecisionReason.INSUFFICIENT_EVIDENCE,
        DecisionReason.BELOW_MINIMUM_NOTIONAL,
    }
)


def validated_utc(value: object, *, field: str = "as_of") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def validated_identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def validated_state(value: object) -> PortfolioState:
    if not isinstance(value, PortfolioState):
        raise TypeError("current_state must be a PortfolioState")
    return value


def _validated_reason(value: object) -> DecisionReason:
    if not isinstance(value, DecisionReason):
        raise TypeError("reason must be a DecisionReason")
    return value


def _canonical_evidence_ids(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("evidence_ids must be an iterable of strings")
    normalized: set[str] = set()
    for position, value in enumerate(cast(Iterable[object], values)):
        normalized.add(validated_identifier(value, field=f"evidence ID {position}"))
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True, init=False)
class PolicyDecision:
    """One pure policy result: a validated target or explicit no-action."""

    decision_id: str
    as_of: datetime
    policy_id: str
    current_state: PortfolioState
    target: AllocationTarget | None
    reason: DecisionReason
    evidence_ids: tuple[str, ...]

    def __init__(self) -> None:
        raise TypeError("use PolicyDecision.for_target() or no_action_decision()")

    @property
    def no_action(self) -> bool:
        """Return whether the policy deliberately emitted no target."""

        return self.target is None

    @classmethod
    def for_target(
        cls,
        *,
        decision_id: str,
        as_of: datetime,
        policy_id: str,
        current_state: PortfolioState,
        target: AllocationTarget,
        reason: DecisionReason,
        evidence_ids: Iterable[str] = (),
    ) -> Self:
        """Construct a target-bearing decision without mutating inventory."""

        validated_reason = _validated_reason(cast(object, reason))
        if validated_reason not in _TARGET_REASONS:
            raise ValueError("no-action reason cannot be used for a target decision")
        if not isinstance(cast(object, target), AllocationTarget):
            raise TypeError("target must be an AllocationTarget")
        return cls._build(
            decision_id=decision_id,
            as_of=as_of,
            policy_id=policy_id,
            current_state=current_state,
            target=target,
            reason=validated_reason,
            evidence_ids=evidence_ids,
        )

    @classmethod
    def no_action_decision(
        cls,
        *,
        decision_id: str,
        as_of: datetime,
        policy_id: str,
        current_state: PortfolioState,
        reason: DecisionReason,
        evidence_ids: Iterable[str] = (),
    ) -> Self:
        """Construct an explicit no-action decision without a fake target."""

        validated_reason = _validated_reason(cast(object, reason))
        if validated_reason not in _NO_ACTION_REASONS:
            raise ValueError("target reason cannot be used for a no-action decision")
        return cls._build(
            decision_id=decision_id,
            as_of=as_of,
            policy_id=policy_id,
            current_state=current_state,
            target=None,
            reason=validated_reason,
            evidence_ids=evidence_ids,
        )

    @classmethod
    def _build(
        cls,
        *,
        decision_id: object,
        as_of: object,
        policy_id: object,
        current_state: object,
        target: AllocationTarget | None,
        reason: DecisionReason,
        evidence_ids: object,
    ) -> Self:
        result = object.__new__(cls)
        object.__setattr__(
            result,
            "decision_id",
            validated_identifier(decision_id, field="decision_id"),
        )
        object.__setattr__(result, "as_of", validated_utc(as_of))
        object.__setattr__(
            result,
            "policy_id",
            validated_identifier(policy_id, field="policy_id"),
        )
        object.__setattr__(result, "current_state", validated_state(current_state))
        object.__setattr__(result, "target", target)
        object.__setattr__(result, "reason", reason)
        object.__setattr__(
            result,
            "evidence_ids",
            _canonical_evidence_ids(evidence_ids),
        )
        return result
