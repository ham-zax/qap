"""Deterministic graph-opinion state and long-only basket target resolution."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from qap.portfolio import AllocationTarget, AssetId, PairOrientation
from qap.portfolio._decimal import divide, exact_add, exact_multiply, exact_sum

_ZERO = Decimal("0")
_ONE = Decimal("1")
_DEFAULT_TILT = Decimal("0.10")
_NEUTRAL_THRESHOLD = 0.5
_ENTRY_THRESHOLD = 1.5


@dataclass(frozen=True, slots=True)
class BasketGraphEdge:
    """One canonical unordered edge plus the frozen candidate orientation."""

    edge_id: str
    asset_a: AssetId
    asset_b: AssetId
    candidate_orientation: PairOrientation

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.edge_id), str) or not self.edge_id.strip():
            raise ValueError("edge_id must be non-empty")
        if not isinstance(cast(object, self.asset_a), AssetId) or not isinstance(
            cast(object, self.asset_b), AssetId
        ):
            raise TypeError("edge assets must be AssetId values")
        if self.asset_a >= self.asset_b:
            raise ValueError("edge assets must use canonical ascending order")
        if not isinstance(cast(object, self.candidate_orientation), PairOrientation):
            raise TypeError("candidate_orientation must be a PairOrientation")
        if {
            self.candidate_orientation.base,
            self.candidate_orientation.quote,
        } != {self.asset_a, self.asset_b}:
            raise ValueError("candidate orientation must contain the edge assets")
        object.__setattr__(self, "edge_id", self.edge_id.strip())


@dataclass(frozen=True, slots=True)
class EdgeOpinionUpdate:
    """All-or-nothing edge-state update for one basket decision boundary."""

    opinions: Mapping[str, int]
    complete: bool
    invalid_edge_ids: tuple[str, ...] = ()


def _edges_by_id(edges: Sequence[BasketGraphEdge]) -> dict[str, BasketGraphEdge]:
    copied = tuple(edges)
    by_id = {edge.edge_id: edge for edge in copied}
    if len(by_id) != len(copied):
        raise ValueError("basket graph edge IDs must be unique")
    pairs = {(edge.asset_a, edge.asset_b) for edge in copied}
    if len(pairs) != len(copied):
        raise ValueError("basket graph must contain at most one edge per pair")
    return by_id


def _validated_previous(
    edge_ids: set[str],
    previous: Mapping[str, int] | None,
) -> dict[str, int]:
    if previous is None:
        return {edge_id: 0 for edge_id in edge_ids}
    copied = dict(previous)
    if set(copied) != edge_ids:
        raise ValueError("previous opinions must cover exactly the selected edge set")
    if any(value not in {-1, 0, 1} for value in copied.values()):
        raise ValueError("edge opinions must be -1, 0, or +1")
    return copied


def _candidate_preference(edge: BasketGraphEdge, score: float) -> int:
    """Map the candidate's own z-score orientation into canonical pair sign."""

    prefer_candidate_base = score < 0.0
    preferred = (
        edge.candidate_orientation.base
        if prefer_candidate_base
        else edge.candidate_orientation.quote
    )
    return 1 if preferred == edge.asset_a else -1


def update_edge_opinions(
    edges: Sequence[BasketGraphEdge],
    *,
    previous: Mapping[str, int] | None,
    scores: Mapping[str, float | None],
) -> EdgeOpinionUpdate:
    """Apply Slice-1 hysteresis atomically; missing evidence preserves prior state."""

    by_id = _edges_by_id(edges)
    edge_ids = set(by_id)
    prior = _validated_previous(edge_ids, previous)
    if set(scores) != edge_ids:
        missing = tuple(sorted(edge_ids - set(scores)))
        extra = tuple(sorted(set(scores) - edge_ids))
        if extra:
            raise ValueError("scores contain edges outside the selected basket graph")
        return EdgeOpinionUpdate(prior, complete=False, invalid_edge_ids=missing)

    invalid: list[str] = []
    numeric: dict[str, float] = {}
    for edge_id, score in scores.items():
        if score is None:
            invalid.append(edge_id)
            continue
        if isinstance(cast(object, score), bool) or not isinstance(
            cast(object, score), float
        ):
            raise TypeError("edge scores must be float or None")
        if not math.isfinite(score):
            invalid.append(edge_id)
            continue
        numeric[edge_id] = score
    if invalid:
        return EdgeOpinionUpdate(
            prior,
            complete=False,
            invalid_edge_ids=tuple(sorted(invalid)),
        )

    updated = dict(prior)
    for edge_id in sorted(by_id):
        score = numeric[edge_id]
        magnitude = abs(score)
        if magnitude <= _NEUTRAL_THRESHOLD:
            updated[edge_id] = 0
        elif magnitude >= _ENTRY_THRESHOLD:
            updated[edge_id] = _candidate_preference(by_id[edge_id], score)
    return EdgeOpinionUpdate(updated, complete=True)


def _connected_components(
    assets: tuple[AssetId, ...],
    edges: tuple[BasketGraphEdge, ...],
) -> tuple[tuple[AssetId, ...], ...]:
    neighbors: dict[AssetId, set[AssetId]] = {asset: set() for asset in assets}
    for edge in edges:
        neighbors[edge.asset_a].add(edge.asset_b)
        neighbors[edge.asset_b].add(edge.asset_a)
    remaining = set(assets)
    components: list[tuple[AssetId, ...]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component: set[AssetId] = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(sorted(neighbors[current] - component, reverse=True))
        remaining -= component
        components.append(tuple(sorted(component)))
    return tuple(components)


def resolve_graph_target(
    neutral_target: AllocationTarget,
    economic_assets: Sequence[AssetId],
    edges: Sequence[BasketGraphEdge],
    opinions: Mapping[str, int],
    *,
    maximum_tilt: Decimal = _DEFAULT_TILT,
) -> AllocationTarget:
    """Resolve the frozen graph into one component-neutral long-only target."""

    if not isinstance(cast(object, neutral_target), AllocationTarget):
        raise TypeError("neutral_target must be an AllocationTarget")
    assets = tuple(sorted(economic_assets))
    if not 2 <= len(assets) <= 6 or len(set(assets)) != len(assets):
        raise ValueError("economic_assets must contain 2-6 unique assets")
    by_id = _edges_by_id(edges)
    edge_tuple = tuple(by_id[edge_id] for edge_id in sorted(by_id))
    asset_set = set(assets)
    if any({edge.asset_a, edge.asset_b} - asset_set for edge in edge_tuple):
        raise ValueError("graph edge contains an asset outside the economic basket")
    state = _validated_previous(set(by_id), opinions)
    if not isinstance(cast(object, maximum_tilt), Decimal):
        raise TypeError("maximum_tilt must be Decimal")
    if not maximum_tilt.is_finite() or maximum_tilt <= _ZERO:
        raise ValueError("maximum_tilt must be finite and positive")

    neutral = divide(_ONE, Decimal(len(assets)))
    if set(neutral_target.weights) != set(assets) or any(
        neutral_target.weights[asset] != neutral for asset in assets
    ):
        raise ValueError("neutral_target must be equal weight over economic_assets")
    if maximum_tilt > neutral:
        raise ValueError("maximum_tilt must preserve long-only basket weights")
    pressure = {asset: 0 for asset in assets}
    degree = {asset: 0 for asset in assets}
    for edge in edge_tuple:
        degree[edge.asset_a] += 1
        degree[edge.asset_b] += 1
        opinion = state[edge.edge_id]
        pressure[edge.asset_a] += opinion
        pressure[edge.asset_b] -= opinion

    normalized = {
        asset: (
            _ZERO
            if degree[asset] == 0
            else divide(Decimal(pressure[asset]), Decimal(degree[asset]))
        )
        for asset in assets
    }
    centered = {asset: _ZERO for asset in assets}
    for component in _connected_components(assets, edge_tuple):
        if len(component) == 1 and degree[component[0]] == 0:
            continue
        mean = divide(
            exact_sum(normalized[asset] for asset in component),
            Decimal(len(component)),
        )
        for asset in component:
            centered[asset] = exact_add(normalized[asset], mean.copy_negate())

    scale = max(value.copy_abs() for value in centered.values())
    weights = dict(neutral_target.weights)
    if scale != _ZERO:
        for asset in assets:
            signed_scale = divide(centered[asset], scale)
            weights[asset] = exact_add(
                neutral,
                exact_multiply(maximum_tilt, signed_scale),
            )
    return AllocationTarget.for_basket(weights, basket=assets)


__all__ = [
    "BasketGraphEdge",
    "EdgeOpinionUpdate",
    "resolve_graph_target",
    "update_edge_opinions",
]
