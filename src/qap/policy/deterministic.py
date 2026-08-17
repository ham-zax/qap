"""Small deterministic target schedule for replay and tests."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import cast

from qap.market import PriceSnapshot
from qap.policy.decision import (
    DecisionReason,
    PolicyDecision,
    validated_identifier,
    validated_state,
    validated_utc,
)
from qap.portfolio import (
    AllocationTarget,
    ExternalInventoryFlow,
    PortfolioState,
)


@dataclass(frozen=True, slots=True, init=False)
class ScheduledTargetPolicy:
    """Emit predefined targets only at exact declared UTC timestamps."""

    policy_id: str
    _items: tuple[tuple[datetime, AllocationTarget], ...]

    def __init__(
        self,
        *,
        policy_id: str,
        schedule: Mapping[datetime, AllocationTarget],
    ) -> None:
        normalized_policy_id = validated_identifier(policy_id, field="policy_id")
        if not isinstance(cast(object, schedule), Mapping):
            raise TypeError("schedule must be a mapping")

        normalized: list[tuple[datetime, AllocationTarget]] = []
        for timestamp, target in cast(Mapping[object, object], schedule).items():
            normalized_timestamp = validated_utc(
                timestamp,
                field="schedule timestamp",
            )
            if not isinstance(target, AllocationTarget):
                raise TypeError("schedule targets must be AllocationTarget values")
            normalized.append((normalized_timestamp, target))

        ordered = tuple(sorted(normalized, key=lambda item: item[0]))
        if len({timestamp for timestamp, _ in ordered}) != len(ordered):
            raise ValueError(
                "schedule timestamps must be unique after UTC normalization"
            )
        object.__setattr__(self, "policy_id", normalized_policy_id)
        object.__setattr__(self, "_items", ordered)

    @property
    def schedule(self) -> Mapping[datetime, AllocationTarget]:
        """Return a read-only copy of the normalized schedule."""

        return MappingProxyType(dict(self._items))

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot | None = None,
        applied_flows: Iterable[ExternalInventoryFlow] = (),
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        """Return the exact scheduled target or an explicit no-action."""

        del price_snapshot, applied_flows
        normalized_as_of = validated_utc(as_of)
        current = validated_state(current_state)
        decision_id = f"{self.policy_id}:{normalized_as_of.isoformat()}"
        target = self.schedule.get(normalized_as_of)
        if target is None:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=normalized_as_of,
                policy_id=self.policy_id,
                current_state=current,
                reason=DecisionReason.NOT_SCHEDULED,
                evidence_ids=evidence_ids,
            )
        return PolicyDecision.for_target(
            decision_id=decision_id,
            as_of=normalized_as_of,
            policy_id=self.policy_id,
            current_state=current,
            target=target,
            reason=DecisionReason.SCHEDULED_TARGET,
            evidence_ids=evidence_ids,
        )
