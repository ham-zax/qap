"""Simple admissible experiment controls over the shared replay policy boundary."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import cast

from qap.market import BarInterval, PriceSnapshot
from qap.policy import DecisionReason, PolicyDecision
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PortfolioState,
    holding_values_at_prices,
    value_holdings_at_prices,
)
from qap.portfolio._decimal import (
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
    exact_sum,
)

_ZERO = Decimal("0")
_ONE = Decimal("1")


def _identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _non_negative_fraction(value: object, *, field: str, upper_open: bool) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite() or value < _ZERO:
        raise ValueError(f"{field} must be finite and non-negative")
    if upper_open and value >= _ONE:
        raise ValueError(f"{field} must be less than 1")
    if not upper_open and value > _ONE:
        raise ValueError(f"{field} must be at most 1")
    return value


def _positive_fraction(value: object, *, field: str) -> Decimal:
    result = _non_negative_fraction(value, field=field, upper_open=False)
    if result == _ZERO:
        raise ValueError(f"{field} must be strictly positive")
    return result


def _validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _validated_context(
    *,
    as_of: datetime,
    current_state: PortfolioState,
    price_snapshot: PriceSnapshot,
    applied_flows: tuple[ExternalInventoryFlow, ...],
) -> None:
    normalized_as_of = _validated_utc(as_of, field="as_of")
    if not isinstance(cast(object, current_state), PortfolioState):
        raise TypeError("current_state must be a PortfolioState")
    if not isinstance(cast(object, price_snapshot), PriceSnapshot):
        raise TypeError("price_snapshot must be a PriceSnapshot")
    if price_snapshot.timestamp != normalized_as_of:
        raise ValueError("price_snapshot timestamp must match as_of")
    if not isinstance(cast(object, applied_flows), tuple):
        raise TypeError("applied_flows must be a tuple")
    raw_flows = cast(tuple[object, ...], applied_flows)
    if any(not isinstance(flow, ExternalInventoryFlow) for flow in raw_flows):
        raise TypeError("applied_flows must contain ExternalInventoryFlow values")
    if any(flow.effective_time > normalized_as_of for flow in applied_flows):
        raise ValueError("applied flow cannot be effective after as_of")


def _basket(target: AllocationTarget) -> tuple[AssetId, ...]:
    if not isinstance(cast(object, target), AllocationTarget):
        raise TypeError("target must be an AllocationTarget")
    return tuple(target.weights)


def _explicit_values(
    state: PortfolioState,
    prices: PriceSnapshot,
    basket: tuple[AssetId, ...],
    *,
    ignored_assets: frozenset[AssetId] = frozenset(),
) -> Mapping[AssetId, Decimal]:
    outside = sorted(
        asset
        for asset in state.holdings
        if asset not in basket and asset not in ignored_assets
    )
    if outside:
        formatted = ", ".join(asset.key for asset in outside)
        raise ValueError(
            f"control state contains assets outside target basket: {formatted}"
        )
    held = holding_values_at_prices(state, prices.prices)
    values = {asset: held.get(asset, _ZERO) for asset in basket}
    for asset in basket:
        prices.price(asset)
    return MappingProxyType(values)


def _weights_from_values(
    values: Mapping[AssetId, Decimal],
    *,
    total: Decimal,
    basket: tuple[AssetId, ...],
) -> Mapping[AssetId, Decimal]:
    if total <= _ZERO:
        raise ValueError("control allocation requires positive portfolio value")
    if not basket:
        raise ValueError("control basket must not be empty")
    weights: dict[AssetId, Decimal] = {}
    for asset in basket[:-1]:
        weights[asset] = divide(values[asset], total)
    weights[basket[-1]] = exact_subtract(_ONE, exact_sum(weights.values()))
    if weights[basket[-1]] < _ZERO:
        raise ArithmeticError("control allocation produced a negative residual weight")
    return MappingProxyType(weights)


def _current_weights(
    state: PortfolioState,
    prices: PriceSnapshot,
    basket: tuple[AssetId, ...],
    *,
    ignored_assets: frozenset[AssetId] = frozenset(),
) -> Mapping[AssetId, Decimal]:
    values = _explicit_values(
        state,
        prices,
        basket,
        ignored_assets=ignored_assets,
    )
    total = exact_sum(values.values())
    return _weights_from_values(values, total=total, basket=basket)


def _allocation_from_weights(
    weights: Mapping[AssetId, Decimal],
    *,
    basket: tuple[AssetId, ...],
) -> AllocationTarget:
    return AllocationTarget.for_basket(weights, basket=basket)


def _allocation_from_values(
    values: Mapping[AssetId, Decimal],
    *,
    total: Decimal,
    basket: tuple[AssetId, ...],
) -> AllocationTarget:
    return _allocation_from_weights(
        _weights_from_values(values, total=total, basket=basket),
        basket=basket,
    )


def _partial_weights(
    current: Mapping[AssetId, Decimal],
    target: Mapping[AssetId, Decimal],
    *,
    fraction: Decimal,
    basket: tuple[AssetId, ...],
) -> Mapping[AssetId, Decimal]:
    values: dict[AssetId, Decimal] = {}
    for asset in basket[:-1]:
        difference = exact_subtract(target[asset], current[asset])
        values[asset] = exact_add(
            current[asset],
            exact_multiply(difference, fraction),
        )
    values[basket[-1]] = exact_subtract(_ONE, exact_sum(values.values()))
    if values[basket[-1]] < _ZERO:
        raise ArithmeticError("partial control target produced a negative residual")
    return MappingProxyType(values)


def _maximum_drift(
    current: Mapping[AssetId, Decimal],
    target: Mapping[AssetId, Decimal],
    basket: tuple[AssetId, ...],
) -> Decimal:
    return max(
        (exact_subtract(current[asset], target[asset]).copy_abs() for asset in basket),
        default=_ZERO,
    )


def _no_action(
    *,
    policy_id: str,
    as_of: datetime,
    current_state: PortfolioState,
    reason: DecisionReason,
    evidence_ids: Iterable[str],
) -> PolicyDecision:
    return PolicyDecision.no_action_decision(
        decision_id=f"{policy_id}:{as_of.isoformat()}",
        as_of=as_of,
        policy_id=policy_id,
        current_state=current_state,
        reason=reason,
        evidence_ids=evidence_ids,
    )


def _target_decision(
    *,
    policy_id: str,
    as_of: datetime,
    current_state: PortfolioState,
    target: AllocationTarget,
    evidence_ids: Iterable[str],
) -> PolicyDecision:
    return PolicyDecision.for_target(
        decision_id=f"{policy_id}:{as_of.isoformat()}",
        as_of=as_of,
        policy_id=policy_id,
        current_state=current_state,
        target=target,
        reason=DecisionReason.EVIDENCE_TARGET,
        evidence_ids=evidence_ids,
    )


def starting_value_target(
    *,
    starting_state: PortfolioState,
    price_snapshot: PriceSnapshot,
    basket: Iterable[AssetId],
) -> AllocationTarget:
    """Freeze starting value weights over the explicitly admitted basket."""

    if not isinstance(cast(object, starting_state), PortfolioState):
        raise TypeError("starting_state must be a PortfolioState")
    if not isinstance(cast(object, price_snapshot), PriceSnapshot):
        raise TypeError("price_snapshot must be a PriceSnapshot")
    raw_basket = tuple(cast(Iterable[object], basket))
    if not raw_basket or any(not isinstance(asset, AssetId) for asset in raw_basket):
        raise TypeError("basket must contain AssetId values")
    copied = cast(tuple[AssetId, ...], raw_basket)
    if len(set(copied)) != len(copied):
        raise ValueError("basket assets must be unique")
    values = _explicit_values(starting_state, price_snapshot, copied)
    total = exact_sum(values.values())
    return _allocation_from_values(values, total=total, basket=copied)


@dataclass(frozen=True, slots=True)
class StrictHodlPolicy:
    policy_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _identifier(self.policy_id, field="policy_id"),
        )

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        _validated_context(
            as_of=as_of,
            current_state=current_state,
            price_snapshot=price_snapshot,
            applied_flows=applied_flows,
        )
        return _no_action(
            policy_id=self.policy_id,
            as_of=as_of,
            current_state=current_state,
            reason=DecisionReason.NOT_SCHEDULED,
            evidence_ids=evidence_ids,
        )


@dataclass(frozen=True, slots=True)
class MatchedContributionStaticPolicy:
    policy_id: str
    target: AllocationTarget

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _identifier(self.policy_id, field="policy_id"),
        )
        _basket(self.target)

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        _validated_context(
            as_of=as_of,
            current_state=current_state,
            price_snapshot=price_snapshot,
            applied_flows=applied_flows,
        )
        contributions = tuple(
            flow for flow in applied_flows if flow.quantity_delta > _ZERO
        )
        if not contributions:
            return _no_action(
                policy_id=self.policy_id,
                as_of=as_of,
                current_state=current_state,
                reason=DecisionReason.NOT_SCHEDULED,
                evidence_ids=evidence_ids,
            )

        basket = _basket(self.target)
        reversal: dict[AssetId, Decimal] = {}
        for flow in contributions:
            reversal[flow.asset] = exact_add(
                reversal.get(flow.asset, _ZERO),
                flow.quantity_delta.copy_negate(),
            )
        pre_contribution = current_state.apply_deltas(reversal)
        pre_values = _explicit_values(pre_contribution, price_snapshot, basket)
        contribution_value = exact_sum(
            exact_multiply(
                flow.quantity_delta,
                price_snapshot.price(flow.asset),
            )
            for flow in contributions
        )
        desired_values = {
            asset: exact_add(
                pre_values[asset],
                exact_multiply(contribution_value, self.target.weights[asset]),
            )
            for asset in basket
        }
        current_values = _explicit_values(current_state, price_snapshot, basket)
        if desired_values == dict(current_values):
            return _no_action(
                policy_id=self.policy_id,
                as_of=as_of,
                current_state=current_state,
                reason=DecisionReason.BELOW_THRESHOLD,
                evidence_ids=evidence_ids,
            )
        total = value_holdings_at_prices(current_state, price_snapshot.prices)
        target = _allocation_from_values(
            desired_values,
            total=total,
            basket=basket,
        )
        return _target_decision(
            policy_id=self.policy_id,
            as_of=as_of,
            current_state=current_state,
            target=target,
            evidence_ids=evidence_ids,
        )


@dataclass(frozen=True, slots=True)
class PeriodicFixedWeightPolicy:
    policy_id: str
    target: AllocationTarget
    first_decision_time: datetime
    interval: BarInterval
    cadence_bars: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _identifier(self.policy_id, field="policy_id"),
        )
        _basket(self.target)
        object.__setattr__(
            self,
            "first_decision_time",
            _validated_utc(self.first_decision_time, field="first_decision_time"),
        )
        if not isinstance(cast(object, self.interval), BarInterval):
            raise TypeError("interval must be a BarInterval")
        cadence = cast(object, self.cadence_bars)
        if not isinstance(cadence, int) or isinstance(cadence, bool) or cadence <= 0:
            raise ValueError("cadence_bars must be a positive integer")

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        _validated_context(
            as_of=as_of,
            current_state=current_state,
            price_snapshot=price_snapshot,
            applied_flows=applied_flows,
        )
        offset = as_of - self.first_decision_time
        if offset < timedelta(0):
            scheduled = False
        else:
            bar_index, remainder = divmod(offset, self.interval.duration)
            scheduled = (
                remainder == timedelta(0)
                and bar_index > 0
                and bar_index % self.cadence_bars == 0
            )
        if not scheduled:
            return _no_action(
                policy_id=self.policy_id,
                as_of=as_of,
                current_state=current_state,
                reason=DecisionReason.NOT_SCHEDULED,
                evidence_ids=evidence_ids,
            )
        return _target_decision(
            policy_id=self.policy_id,
            as_of=as_of,
            current_state=current_state,
            target=self.target,
            evidence_ids=evidence_ids,
        )


@dataclass(frozen=True, slots=True)
class BandPartialPolicy:
    policy_id: str
    target: AllocationTarget
    band_width: Decimal
    partial_correction_fraction: Decimal
    execution_only_bridge: AssetId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _identifier(self.policy_id, field="policy_id"),
        )
        _basket(self.target)
        object.__setattr__(
            self,
            "band_width",
            _non_negative_fraction(
                self.band_width,
                field="band_width",
                upper_open=True,
            ),
        )
        object.__setattr__(
            self,
            "partial_correction_fraction",
            _positive_fraction(
                self.partial_correction_fraction,
                field="partial_correction_fraction",
            ),
        )
        if self.execution_only_bridge is not None:
            if not isinstance(cast(object, self.execution_only_bridge), AssetId):
                raise TypeError("execution_only_bridge must be AssetId or None")
            if self.execution_only_bridge in self.target.weights:
                raise ValueError("execution_only_bridge cannot be in target basket")

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        _validated_context(
            as_of=as_of,
            current_state=current_state,
            price_snapshot=price_snapshot,
            applied_flows=applied_flows,
        )
        basket = _basket(self.target)
        ignored_assets: frozenset[AssetId] = (
            frozenset()
            if self.execution_only_bridge is None
            else frozenset({self.execution_only_bridge})
        )
        current = _current_weights(
            current_state,
            price_snapshot,
            basket,
            ignored_assets=ignored_assets,
        )
        if _maximum_drift(current, self.target.weights, basket) <= self.band_width:
            return _no_action(
                policy_id=self.policy_id,
                as_of=as_of,
                current_state=current_state,
                reason=DecisionReason.BELOW_THRESHOLD,
                evidence_ids=evidence_ids,
            )
        corrected = _partial_weights(
            current,
            self.target.weights,
            fraction=self.partial_correction_fraction,
            basket=basket,
        )
        return _target_decision(
            policy_id=self.policy_id,
            as_of=as_of,
            current_state=current_state,
            target=_allocation_from_weights(corrected, basket=basket),
            evidence_ids=evidence_ids,
        )


@dataclass(frozen=True, slots=True)
class ContributionAwareBandPolicy:
    policy_id: str
    target: AllocationTarget
    band_width: Decimal
    partial_correction_fraction: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _identifier(self.policy_id, field="policy_id"),
        )
        _basket(self.target)
        object.__setattr__(
            self,
            "band_width",
            _non_negative_fraction(
                self.band_width,
                field="band_width",
                upper_open=True,
            ),
        )
        object.__setattr__(
            self,
            "partial_correction_fraction",
            _positive_fraction(
                self.partial_correction_fraction,
                field="partial_correction_fraction",
            ),
        )

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        _validated_context(
            as_of=as_of,
            current_state=current_state,
            price_snapshot=price_snapshot,
            applied_flows=applied_flows,
        )
        basket = _basket(self.target)
        current_values = dict(_explicit_values(current_state, price_snapshot, basket))
        total = exact_sum(current_values.values())
        target_values = {
            asset: exact_multiply(total, self.target.weights[asset]) for asset in basket
        }
        contribution_values: dict[AssetId, Decimal] = {asset: _ZERO for asset in basket}
        for flow in applied_flows:
            if flow.quantity_delta > _ZERO:
                contribution_values[flow.asset] = exact_add(
                    contribution_values[flow.asset],
                    exact_multiply(
                        flow.quantity_delta,
                        price_snapshot.price(flow.asset),
                    ),
                )

        projected = dict(current_values)
        deficits = {
            asset: exact_subtract(target_values[asset], current_values[asset])
            for asset in basket
            if current_values[asset] < target_values[asset]
        }
        sources = {
            asset: min(
                contribution_values[asset],
                exact_subtract(current_values[asset], target_values[asset]),
            )
            for asset in basket
            if contribution_values[asset] > _ZERO
            and current_values[asset] > target_values[asset]
        }
        ordered_sources = sorted(
            sources,
            key=lambda asset: (sources[asset].copy_negate(), asset),
        )
        ordered_deficits = sorted(
            deficits,
            key=lambda asset: (deficits[asset].copy_negate(), asset),
        )
        for source in ordered_sources:
            remaining = sources[source]
            for destination in ordered_deficits:
                deficit = deficits[destination]
                if remaining == _ZERO or deficit == _ZERO:
                    continue
                transfer = min(remaining, deficit)
                projected[source] = exact_subtract(projected[source], transfer)
                projected[destination] = exact_add(
                    projected[destination],
                    transfer,
                )
                remaining = exact_subtract(remaining, transfer)
                deficits[destination] = exact_subtract(deficit, transfer)

        projected_weights = _weights_from_values(
            projected,
            total=total,
            basket=basket,
        )
        drift = _maximum_drift(projected_weights, self.target.weights, basket)
        if drift <= self.band_width:
            if projected == current_values:
                return _no_action(
                    policy_id=self.policy_id,
                    as_of=as_of,
                    current_state=current_state,
                    reason=DecisionReason.BELOW_THRESHOLD,
                    evidence_ids=evidence_ids,
                )
            final_weights = projected_weights
        else:
            final_weights = _partial_weights(
                projected_weights,
                self.target.weights,
                fraction=self.partial_correction_fraction,
                basket=basket,
            )
        return _target_decision(
            policy_id=self.policy_id,
            as_of=as_of,
            current_state=current_state,
            target=_allocation_from_weights(final_weights, basket=basket),
            evidence_ids=evidence_ids,
        )


__all__ = [
    "BandPartialPolicy",
    "ContributionAwareBandPolicy",
    "MatchedContributionStaticPolicy",
    "PeriodicFixedWeightPolicy",
    "StrictHodlPolicy",
    "starting_value_target",
]
