"""Single mutable owner for deterministic replay inventory state."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Protocol, cast, runtime_checkable

from qap.portfolio.assets import AssetId
from qap.portfolio.flows import ExternalInventoryFlow
from qap.portfolio.state import PortfolioState


class InventoryDeltaEvent(Protocol):
    """Structural boundary for an audited event that changes inventory."""

    @property
    def event_id(self) -> str: ...

    @property
    def balance_deltas(self) -> Mapping[AssetId, Decimal]: ...


@runtime_checkable
class FillEvent(InventoryDeltaEvent, Protocol):
    """Structural execution event admitted through the fill-only ledger path."""

    @property
    def decision_id(self) -> str: ...

    @property
    def execution_timestamp(self) -> datetime: ...


class DuplicateLedgerEventError(ValueError):
    """Raised when replay attempts to apply an event identity twice."""


def _validated_starting_state(value: object) -> PortfolioState:
    if not isinstance(value, PortfolioState):
        raise TypeError("starting_state must be a PortfolioState")
    return value


def _validated_event_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("event_id must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("event_id must not be empty")
    return normalized


class PortfolioLedger:
    """Apply explicit deltas atomically and idempotently to owned inventory."""

    def __init__(self, starting_state: PortfolioState) -> None:
        self._current_state = _validated_starting_state(starting_state)
        self._applied_ids: set[str] = set()
        self._event_ids: list[str] = []
        self._fills: list[FillEvent] = []
        self._flows: list[ExternalInventoryFlow] = []

    @property
    def current_state(self) -> PortfolioState:
        return self._current_state

    @property
    def applied_event_ids(self) -> tuple[str, ...]:
        return tuple(self._event_ids)

    @property
    def applied_fills(self) -> tuple[FillEvent, ...]:
        return tuple(self._fills)

    @property
    def applied_flows(self) -> tuple[ExternalInventoryFlow, ...]:
        return tuple(self._flows)

    def _apply_event(self, event: InventoryDeltaEvent) -> PortfolioState:
        event_id = _validated_event_id(event.event_id)
        if event_id in self._applied_ids:
            raise DuplicateLedgerEventError(
                f"ledger event {event_id!r} was already applied"
            )

        next_state = self._current_state.apply_deltas(event.balance_deltas)
        self._current_state = next_state
        self._applied_ids.add(event_id)
        self._event_ids.append(event_id)
        return next_state

    def apply_fill(self, fill: InventoryDeltaEvent) -> PortfolioState:
        """Apply one unseen fill; reject duplicates and invalid balances."""

        if not isinstance(cast(object, fill), FillEvent):
            raise TypeError(
                "fill event must provide decision_id, execution_timestamp, "
                "event_id, and balance_deltas"
            )
        validated_fill = cast(FillEvent, fill)
        next_state = self._apply_event(validated_fill)
        self._fills.append(validated_fill)
        return next_state

    def apply_flow(self, flow: ExternalInventoryFlow) -> PortfolioState:
        """Apply one unseen declared exogenous inventory flow."""

        if not isinstance(cast(object, flow), ExternalInventoryFlow):
            raise TypeError("flow must be an ExternalInventoryFlow")
        next_state = self._apply_event(flow)
        self._flows.append(flow)
        return next_state
