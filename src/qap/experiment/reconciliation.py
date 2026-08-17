"""Independent balance reconciliation from persisted fill deltas."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from qap.execution import Fill
from qap.portfolio import AssetId, PortfolioState
from qap.portfolio._decimal import exact_add, exact_subtract

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class ReconciliationDifference:
    """One expected-versus-recomputed asset balance mismatch."""

    asset: AssetId
    expected: Decimal
    recomputed: Decimal
    delta: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationStep:
    """Independent state reconstruction after one fill."""

    fill_id: str
    expected_state: PortfolioState
    recomputed_state: PortfolioState
    differences: tuple[ReconciliationDifference, ...]

    @property
    def matches(self) -> bool:
        return not self.differences


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Full independent reconciliation report for an ordered fill sequence."""

    starting_state: PortfolioState
    steps: tuple[ReconciliationStep, ...]
    ending_state: PortfolioState

    @property
    def matches(self) -> bool:
        return all(step.matches for step in self.steps)


def _validated_fills(values: Iterable[Fill]) -> tuple[Fill, ...]:
    try:
        copied = tuple(values)
    except TypeError as exc:
        raise TypeError("fills must be iterable") from exc
    if any(not isinstance(cast(object, fill), Fill) for fill in copied):
        raise TypeError("fills members must be Fill values")
    return copied


def _validated_states(values: Iterable[PortfolioState]) -> tuple[PortfolioState, ...]:
    try:
        copied = tuple(values)
    except TypeError as exc:
        raise TypeError("expected_states must be iterable") from exc
    if any(not isinstance(cast(object, state), PortfolioState) for state in copied):
        raise TypeError("expected_states members must be PortfolioState values")
    return copied


def _differences(
    expected: PortfolioState,
    recomputed: PortfolioState,
) -> tuple[ReconciliationDifference, ...]:
    assets = sorted(
        set(expected.holdings) | set(recomputed.holdings), key=lambda item: item.key
    )
    result: list[ReconciliationDifference] = []
    for asset in assets:
        expected_balance = expected.quantity(asset)
        recomputed_balance = recomputed.quantity(asset)
        if expected_balance == recomputed_balance:
            continue
        result.append(
            ReconciliationDifference(
                asset=asset,
                expected=expected_balance,
                recomputed=recomputed_balance,
                delta=exact_subtract(recomputed_balance, expected_balance),
            )
        )
    return tuple(result)


def reconcile_fill_sequence(
    *,
    starting_state: PortfolioState,
    fills: Iterable[Fill],
    expected_states: Iterable[PortfolioState],
) -> ReconciliationReport:
    """Replay raw fill deltas independently and compare every expected state."""

    if not isinstance(cast(object, starting_state), PortfolioState):
        raise TypeError("starting_state must be PortfolioState")
    copied_fills = _validated_fills(fills)
    copied_states = _validated_states(expected_states)
    if len(copied_fills) != len(copied_states):
        raise ValueError("fills and expected_states must have the same length")

    balances = dict(starting_state.holdings)
    steps: list[ReconciliationStep] = []
    recomputed_state = starting_state
    for fill, expected_state in zip(copied_fills, copied_states, strict=True):
        for asset, delta in fill.balance_deltas.items():
            balances[asset] = exact_add(balances.get(asset, _ZERO), delta)
        recomputed_state = PortfolioState.from_holdings(balances)
        steps.append(
            ReconciliationStep(
                fill_id=fill.fill_id,
                expected_state=expected_state,
                recomputed_state=recomputed_state,
                differences=_differences(expected_state, recomputed_state),
            )
        )

    return ReconciliationReport(
        starting_state=starting_state,
        steps=tuple(steps),
        ending_state=recomputed_state,
    )


__all__ = [
    "ReconciliationDifference",
    "ReconciliationReport",
    "ReconciliationStep",
    "reconcile_fill_sequence",
]
