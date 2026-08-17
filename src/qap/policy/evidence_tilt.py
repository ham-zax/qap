"""Bounded long-only allocation tilt from one declared signed evidence score."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.policy.decision import (
    DecisionReason,
    PolicyDecision,
    validated_identifier,
    validated_state,
    validated_utc,
)
from qap.portfolio import AllocationTarget, AssetId, PairOrientation, PortfolioState
from qap.portfolio._decimal import exact_add, exact_subtract

_ZERO = Decimal("0")


class NeutralBandMode(StrEnum):
    """Declared behavior when evidence sits inside the neutral band."""

    NEUTRAL_TARGET = "neutral_target"
    NO_ACTION = "no_action"


def _validated_threshold(value: float, *, field: str) -> float:
    raw = cast(object, value)
    if isinstance(raw, bool) or not isinstance(raw, float):
        raise TypeError(f"{field} must be a float")
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{field} must be finite and non-negative")
    return value


def _validated_maximum_tilt(value: Decimal) -> Decimal:
    if not isinstance(cast(object, value), Decimal):
        raise TypeError("maximum_tilt must be Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError("maximum_tilt must be finite and positive")
    return value


@dataclass(frozen=True, slots=True, init=False)
class EvidenceTiltPolicy:
    """Transfer one bounded weight amount between the declared orientation legs."""

    policy_id: str
    orientation: PairOrientation
    neutral_target: AllocationTarget
    neutral_threshold: float
    enter_threshold: float
    maximum_tilt: Decimal
    neutral_mode: NeutralBandMode

    def __init__(
        self,
        *,
        policy_id: str,
        orientation: PairOrientation,
        neutral_target: AllocationTarget,
        neutral_threshold: float,
        enter_threshold: float,
        maximum_tilt: Decimal,
        neutral_mode: NeutralBandMode,
    ) -> None:
        normalized_policy_id = validated_identifier(policy_id, field="policy_id")
        if not isinstance(cast(object, orientation), PairOrientation):
            raise TypeError("orientation must be a PairOrientation")
        if not isinstance(cast(object, neutral_target), AllocationTarget):
            raise TypeError("neutral_target must be an AllocationTarget")
        if not isinstance(cast(object, neutral_mode), NeutralBandMode):
            raise TypeError("neutral_mode must be a NeutralBandMode")
        neutral = _validated_threshold(neutral_threshold, field="neutral_threshold")
        enter = _validated_threshold(enter_threshold, field="enter_threshold")
        if enter <= 0.0:
            raise ValueError("enter_threshold must be positive")
        if neutral > enter:
            raise ValueError("neutral_threshold must not exceed enter_threshold")
        tilt = _validated_maximum_tilt(maximum_tilt)

        weights = neutral_target.weights
        try:
            base_weight = weights[orientation.base]
            quote_weight = weights[orientation.quote]
        except KeyError as exc:
            raise ValueError(
                "neutral_target must include both orientation legs"
            ) from exc
        if tilt > min(base_weight, quote_weight):
            raise ValueError(
                "maximum_tilt must preserve long-only weights in both directions"
            )

        object.__setattr__(self, "policy_id", normalized_policy_id)
        object.__setattr__(self, "orientation", orientation)
        object.__setattr__(self, "neutral_target", neutral_target)
        object.__setattr__(self, "neutral_threshold", neutral)
        object.__setattr__(self, "enter_threshold", enter)
        object.__setattr__(self, "maximum_tilt", tilt)
        object.__setattr__(self, "neutral_mode", neutral_mode)

    def _tilted_target(self, *, toward_base: bool) -> AllocationTarget:
        weights = dict(self.neutral_target.weights)
        add_asset = self.orientation.base if toward_base else self.orientation.quote
        subtract_asset = (
            self.orientation.quote if toward_base else self.orientation.base
        )
        weights[add_asset] = exact_add(weights[add_asset], self.maximum_tilt)
        weights[subtract_asset] = exact_subtract(
            weights[subtract_asset],
            self.maximum_tilt,
        )
        return AllocationTarget.for_basket(weights, basket=weights)

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        score: float | None,
        evidence_id: str,
    ) -> PolicyDecision:
        """Map evidence to a target or explicit no-action without execution logic."""

        normalized_as_of = validated_utc(as_of)
        current = validated_state(current_state)
        evidence = validated_identifier(evidence_id, field="evidence_id")
        decision_id = f"{self.policy_id}:{normalized_as_of.isoformat()}"

        if score is None:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=normalized_as_of,
                policy_id=self.policy_id,
                current_state=current,
                reason=DecisionReason.INSUFFICIENT_EVIDENCE,
                evidence_ids=(evidence,),
            )
        if isinstance(cast(object, score), bool) or not isinstance(
            cast(object, score), float
        ):
            raise TypeError("score must be a float or None")
        if not math.isfinite(score):
            raise ValueError("score must be finite")

        magnitude = abs(score)
        if magnitude <= self.neutral_threshold:
            if self.neutral_mode is NeutralBandMode.NO_ACTION:
                return PolicyDecision.no_action_decision(
                    decision_id=decision_id,
                    as_of=normalized_as_of,
                    policy_id=self.policy_id,
                    current_state=current,
                    reason=DecisionReason.BELOW_THRESHOLD,
                    evidence_ids=(evidence,),
                )
            target = self.neutral_target
        elif magnitude < self.enter_threshold:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=normalized_as_of,
                policy_id=self.policy_id,
                current_state=current,
                reason=DecisionReason.BELOW_THRESHOLD,
                evidence_ids=(evidence,),
            )
        else:
            target = self._tilted_target(toward_base=score > 0.0)

        return PolicyDecision.for_target(
            decision_id=decision_id,
            as_of=normalized_as_of,
            policy_id=self.policy_id,
            current_state=current,
            target=target,
            reason=DecisionReason.EVIDENCE_TARGET,
            evidence_ids=(evidence,),
        )


@dataclass(frozen=True, slots=True, init=False)
class CrossSectionalTiltPolicy:
    """Pair-blind bounded transfer from the lowest to highest asset score."""

    policy_id: str
    neutral_target: AllocationTarget
    maximum_tilt: Decimal

    def __init__(
        self,
        *,
        policy_id: str,
        neutral_target: AllocationTarget,
        maximum_tilt: Decimal,
    ) -> None:
        normalized_policy_id = validated_identifier(policy_id, field="policy_id")
        if not isinstance(cast(object, neutral_target), AllocationTarget):
            raise TypeError("neutral_target must be an AllocationTarget")
        tilt = _validated_maximum_tilt(maximum_tilt)
        weights = neutral_target.weights
        if len(weights) < 2:
            raise ValueError("cross-sectional neutral_target needs at least two assets")
        if tilt > min(weights.values()):
            raise ValueError(
                "maximum_tilt must preserve long-only weights for every basket asset"
            )
        object.__setattr__(self, "policy_id", normalized_policy_id)
        object.__setattr__(self, "neutral_target", neutral_target)
        object.__setattr__(self, "maximum_tilt", tilt)

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        scores: Mapping[AssetId, float] | None,
        evidence_id: str,
    ) -> PolicyDecision:
        """Rank the whole declared basket and emit one bounded long-only target."""

        normalized_as_of = validated_utc(as_of)
        current = validated_state(current_state)
        evidence = validated_identifier(evidence_id, field="evidence_id")
        decision_id = f"{self.policy_id}:{normalized_as_of.isoformat()}"
        if scores is None or not scores:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=normalized_as_of,
                policy_id=self.policy_id,
                current_state=current,
                reason=DecisionReason.INSUFFICIENT_EVIDENCE,
                evidence_ids=(evidence,),
            )
        if not isinstance(cast(object, scores), Mapping):
            raise TypeError("scores must be a mapping or None")

        expected_assets = set(self.neutral_target.weights)
        if set(scores) != expected_assets:
            raise ValueError("scores must cover exactly the neutral target basket")
        normalized_scores: dict[AssetId, float] = {}
        for asset, score in scores.items():
            if isinstance(cast(object, score), bool) or not isinstance(
                cast(object, score), float
            ):
                raise TypeError("cross-sectional scores must be floats")
            if not math.isfinite(score):
                raise ValueError("cross-sectional scores must be finite")
            normalized_scores[asset] = score

        ranked = sorted(
            normalized_scores.items(),
            key=lambda item: (item[1], item[0].key),
        )
        low_asset, low_score = ranked[0]
        high_asset, high_score = ranked[-1]
        if high_score <= low_score:
            return PolicyDecision.no_action_decision(
                decision_id=decision_id,
                as_of=normalized_as_of,
                policy_id=self.policy_id,
                current_state=current,
                reason=DecisionReason.BELOW_THRESHOLD,
                evidence_ids=(evidence,),
            )

        weights = dict(self.neutral_target.weights)
        weights[high_asset] = exact_add(weights[high_asset], self.maximum_tilt)
        weights[low_asset] = exact_subtract(weights[low_asset], self.maximum_tilt)
        target = AllocationTarget.for_basket(weights, basket=weights)
        return PolicyDecision.for_target(
            decision_id=decision_id,
            as_of=normalized_as_of,
            policy_id=self.policy_id,
            current_state=current,
            target=target,
            reason=DecisionReason.EVIDENCE_TARGET,
            evidence_ids=(evidence,),
        )


__all__ = ["CrossSectionalTiltPolicy", "EvidenceTiltPolicy", "NeutralBandMode"]
