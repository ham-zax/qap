"""Deterministic direct-or-one-bridge routing over declared spot instruments."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.execution.costs import CostModel
from qap.execution.direct import DirectExecutionReason, execute_direct_rebalance_leg
from qap.execution.fills import Fill, FillSide
from qap.market import MarketMetadata, VenueInstrument
from qap.portfolio import AssetId, PortfolioState
from qap.portfolio._decimal import canonical_decimal, exact_subtract


class RoutingReason(StrEnum):
    """Stable reasons an explicit paper route cannot be produced."""

    UNSUPPORTED_ROUTE = "unsupported_route"
    UNDECLARED_BRIDGE = "undeclared_bridge"
    AMBIGUOUS_ROUTE = "ambiguous_route"


class RoutedExecutionReason(StrEnum):
    """Stable reasons a fully planned route did not complete."""

    MISSING_REFERENCE_PRICE = "missing_reference_price"
    MISSING_MARKET_METADATA = "missing_market_metadata"
    LEG_NO_FILL = "leg_no_fill"


class RoutePlanningError(ValueError):
    """Raised when the declared route set cannot produce one deterministic route."""

    def __init__(self, reason: RoutingReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


@dataclass(frozen=True, slots=True)
class ExecutionRouteLeg:
    """One real spot-market conversion in a declared execution route."""

    source: AssetId
    destination: AssetId
    instrument: VenueInstrument
    side: FillSide

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.source), AssetId):
            raise TypeError("source must be AssetId")
        if not isinstance(cast(object, self.destination), AssetId):
            raise TypeError("destination must be AssetId")
        if self.source == self.destination:
            raise ValueError("route leg source and destination must differ")
        if not isinstance(cast(object, self.instrument), VenueInstrument):
            raise TypeError("instrument must be VenueInstrument")
        if not isinstance(cast(object, self.side), FillSide):
            raise TypeError("side must be FillSide")
        if self.side is FillSide.SELL:
            matches = (
                self.instrument.base == self.source
                and self.instrument.quote == self.destination
            )
        else:
            matches = (
                self.instrument.quote == self.source
                and self.instrument.base == self.destination
            )
        if not matches:
            raise ValueError("route leg side must match instrument orientation")

    @property
    def identity(self) -> str:
        return (
            f"{self.instrument.venue}:{self.instrument.venue_symbol}:{self.side.value}"
        )


@dataclass(frozen=True, slots=True)
class ExecutionRoute:
    """One direct route or exactly two legs through one declared bridge."""

    source: AssetId
    destination: AssetId
    bridge: AssetId | None
    legs: tuple[ExecutionRouteLeg, ...]

    def __post_init__(self) -> None:
        if self.source == self.destination:
            raise ValueError("route source and destination must differ")
        if len(self.legs) not in (1, 2):
            raise ValueError("execution route must contain one or two legs")
        if self.legs[0].source != self.source:
            raise ValueError("first route leg must start at route source")
        if self.legs[-1].destination != self.destination:
            raise ValueError("last route leg must end at route destination")
        if len(self.legs) == 1:
            if self.bridge is not None:
                raise ValueError("direct route cannot declare a bridge")
        else:
            if self.bridge is None:
                raise ValueError("two-leg route requires a bridge")
            if self.bridge in (self.source, self.destination):
                raise ValueError("bridge must differ from route endpoints")
            if self.legs[0].destination != self.bridge:
                raise ValueError("first route leg must end at bridge")
            if self.legs[1].source != self.bridge:
                raise ValueError("second route leg must start at bridge")

    @property
    def route_id(self) -> str:
        if self.bridge is None:
            return (
                f"direct:{self.source.key}>{self.destination.key}:"
                f"{self.legs[0].identity}"
            )
        leg_identity = "|".join(leg.identity for leg in self.legs)
        return (
            f"bridge:{self.source.key}>{self.bridge.key}>{self.destination.key}:"
            f"{leg_identity}"
        )


@dataclass(frozen=True, slots=True)
class RoutedExecutionResult:
    """Immutable direct/two-leg result with any owned bridge residue exposed."""

    route: ExecutionRoute
    fills: tuple[Fill, ...]
    ending_state: PortfolioState
    intermediate_state: PortfolioState | None
    bridge_residue: Decimal
    reason: RoutedExecutionReason | None
    failed_leg_index: int | None
    leg_reason: DirectExecutionReason | None


def _validated_assets(values: Iterable[AssetId]) -> frozenset[AssetId]:
    try:
        copied = tuple(values)
    except TypeError as exc:
        raise TypeError("declared_assets must be iterable") from exc
    if any(not isinstance(cast(object, asset), AssetId) for asset in copied):
        raise TypeError("declared_assets members must be AssetId")
    return frozenset(copied)


def _validated_instruments(
    values: Iterable[VenueInstrument],
) -> tuple[VenueInstrument, ...]:
    try:
        copied = tuple(values)
    except TypeError as exc:
        raise TypeError("instruments must be iterable") from exc
    if any(not isinstance(cast(object, item), VenueInstrument) for item in copied):
        raise TypeError("instruments members must be VenueInstrument")
    return copied


def _find_leg(
    instruments: tuple[VenueInstrument, ...],
    *,
    source: AssetId,
    destination: AssetId,
) -> ExecutionRouteLeg | None:
    matches: list[ExecutionRouteLeg] = []
    for instrument in instruments:
        if instrument.base == source and instrument.quote == destination:
            matches.append(
                ExecutionRouteLeg(
                    source=source,
                    destination=destination,
                    instrument=instrument,
                    side=FillSide.SELL,
                )
            )
        elif instrument.quote == source and instrument.base == destination:
            matches.append(
                ExecutionRouteLeg(
                    source=source,
                    destination=destination,
                    instrument=instrument,
                    side=FillSide.BUY,
                )
            )
    if len(matches) > 1:
        raise RoutePlanningError(RoutingReason.AMBIGUOUS_ROUTE)
    return matches[0] if matches else None


def plan_execution_route(
    *,
    source: AssetId,
    destination: AssetId,
    instruments: Iterable[VenueInstrument],
    declared_assets: Iterable[AssetId],
    bridge: AssetId | None = None,
) -> ExecutionRoute:
    """Return a direct route or exactly one explicitly declared bridge route."""

    if not isinstance(cast(object, source), AssetId):
        raise TypeError("source must be AssetId")
    if not isinstance(cast(object, destination), AssetId):
        raise TypeError("destination must be AssetId")
    if source == destination:
        raise ValueError("route source and destination must differ")
    available = _validated_instruments(instruments)
    assets = _validated_assets(declared_assets)
    if source not in assets or destination not in assets:
        raise RoutePlanningError(RoutingReason.UNSUPPORTED_ROUTE)

    direct = _find_leg(available, source=source, destination=destination)
    if direct is not None:
        return ExecutionRoute(
            source=source,
            destination=destination,
            bridge=None,
            legs=(direct,),
        )

    if bridge is None:
        raise RoutePlanningError(RoutingReason.UNSUPPORTED_ROUTE)
    if not isinstance(cast(object, bridge), AssetId):
        raise TypeError("bridge must be AssetId or None")
    if bridge not in assets:
        raise RoutePlanningError(RoutingReason.UNDECLARED_BRIDGE)
    if bridge in (source, destination):
        raise ValueError("bridge must differ from route endpoints")

    first = _find_leg(available, source=source, destination=bridge)
    second = _find_leg(available, source=bridge, destination=destination)
    if first is None or second is None:
        raise RoutePlanningError(RoutingReason.UNSUPPORTED_ROUTE)
    return ExecutionRoute(
        source=source,
        destination=destination,
        bridge=bridge,
        legs=(first, second),
    )


def _validated_source_quantity(value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError("source_quantity must be Decimal")
    if not value.is_finite() or value <= 0:
        raise ValueError("source_quantity must be positive finite")
    return canonical_decimal(value)


def _preflight_route(
    route: ExecutionRoute,
    *,
    reference_prices: Mapping[VenueInstrument, Decimal],
    market_metadata: Mapping[VenueInstrument, MarketMetadata],
    current_state: PortfolioState,
) -> RoutedExecutionResult | None:
    for index, leg in enumerate(route.legs):
        if leg.instrument not in reference_prices:
            return RoutedExecutionResult(
                route=route,
                fills=(),
                ending_state=current_state,
                intermediate_state=None,
                bridge_residue=Decimal("0"),
                reason=RoutedExecutionReason.MISSING_REFERENCE_PRICE,
                failed_leg_index=index,
                leg_reason=None,
            )
        metadata = market_metadata.get(leg.instrument)
        if metadata is None:
            return RoutedExecutionResult(
                route=route,
                fills=(),
                ending_state=current_state,
                intermediate_state=None,
                bridge_residue=Decimal("0"),
                reason=RoutedExecutionReason.MISSING_MARKET_METADATA,
                failed_leg_index=index,
                leg_reason=None,
            )
        if metadata.instrument != leg.instrument:
            raise ValueError("market metadata key must match metadata instrument")
    return None


def _quantity_deltas_for_leg(
    leg: ExecutionRouteLeg,
    *,
    source_quantity: Decimal,
) -> dict[AssetId, Decimal]:
    return {leg.source: -source_quantity, leg.destination: Decimal("1")}


def execute_routed_conversion(
    *,
    route: ExecutionRoute,
    fill_id_prefix: str,
    decision_id: str,
    execution_timestamp: datetime,
    source_quantity: Decimal,
    current_state: PortfolioState,
    reference_prices: Mapping[VenueInstrument, Decimal],
    market_metadata: Mapping[VenueInstrument, MarketMetadata],
    cost_model: CostModel,
) -> RoutedExecutionResult:
    """Execute one planned route sequentially after atomic data preflight."""

    if not isinstance(cast(object, route), ExecutionRoute):
        raise TypeError("route must be ExecutionRoute")
    if not isinstance(cast(object, current_state), PortfolioState):
        raise TypeError("current_state must be PortfolioState")
    if not isinstance(cast(object, cost_model), CostModel):
        raise TypeError("cost_model must be CostModel")
    quantity = _validated_source_quantity(source_quantity)
    preflight = _preflight_route(
        route,
        reference_prices=reference_prices,
        market_metadata=market_metadata,
        current_state=current_state,
    )
    if preflight is not None:
        return preflight

    state = current_state
    intermediate: PortfolioState | None = None
    fills: list[Fill] = []
    leg_source_quantity = quantity
    for index, leg in enumerate(route.legs):
        result = execute_direct_rebalance_leg(
            fill_id=f"{fill_id_prefix}:leg-{index + 1}",
            decision_id=decision_id,
            execution_timestamp=execution_timestamp,
            instrument=leg.instrument,
            quantity_deltas=_quantity_deltas_for_leg(
                leg,
                source_quantity=leg_source_quantity,
            ),
            current_state=state,
            reference_price=reference_prices[leg.instrument],
            cost_model=cost_model,
            market_metadata=market_metadata[leg.instrument],
        )
        if result.fill is None:
            bridge_residue = Decimal("0")
            if route.bridge is not None:
                bridge_residue = exact_subtract(
                    state.quantity(route.bridge),
                    current_state.quantity(route.bridge),
                )
            return RoutedExecutionResult(
                route=route,
                fills=tuple(fills),
                ending_state=state,
                intermediate_state=intermediate,
                bridge_residue=bridge_residue,
                reason=RoutedExecutionReason.LEG_NO_FILL,
                failed_leg_index=index,
                leg_reason=result.reason,
            )

        fill = result.fill
        fills.append(fill)
        state = state.apply_deltas(fill.balance_deltas)
        if index == 0 and len(route.legs) == 2:
            intermediate = state
            assert route.bridge is not None
            leg_source_quantity = fill.balance_deltas[route.bridge]
            if leg_source_quantity <= 0:
                raise ValueError(
                    "first bridge leg must produce positive bridge inventory"
                )

    bridge_residue = Decimal("0")
    if route.bridge is not None:
        bridge_residue = exact_subtract(
            state.quantity(route.bridge),
            current_state.quantity(route.bridge),
        )
    return RoutedExecutionResult(
        route=route,
        fills=tuple(fills),
        ending_state=state,
        intermediate_state=intermediate,
        bridge_residue=bridge_residue,
        reason=None,
        failed_leg_index=None,
        leg_reason=None,
    )


__all__ = [
    "ExecutionRoute",
    "ExecutionRouteLeg",
    "RoutedExecutionReason",
    "RoutedExecutionResult",
    "RoutePlanningError",
    "RoutingReason",
    "execute_routed_conversion",
    "plan_execution_route",
]
