"""Independent balance reconciliation from persisted fill deltas."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from qap.evaluation import value_portfolio
from qap.execution import Fill, FillSide
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState
from qap.portfolio._decimal import exact_add, exact_multiply, exact_subtract

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
class ReconciliationEconomicDifference:
    """One reported-versus-independently-derived fill economic mismatch."""

    fill_id: str
    field: str
    reported: Decimal
    recomputed: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Full independent reconciliation report for an ordered fill sequence."""

    starting_state: PortfolioState
    steps: tuple[ReconciliationStep, ...]
    ending_state: PortfolioState
    economic_differences: tuple[ReconciliationEconomicDifference, ...]
    reported_fee_total: Decimal
    recomputed_fee_total: Decimal
    reported_turnover: Decimal
    recomputed_turnover: Decimal
    reported_slippage_total: Decimal
    recomputed_slippage_total: Decimal
    expected_terminal_value: Decimal | None
    recomputed_terminal_value: Decimal | None

    @property
    def matches(self) -> bool:
        return (
            all(step.matches for step in self.steps)
            and not self.economic_differences
            and self.expected_terminal_value == self.recomputed_terminal_value
        )


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


def _economic_difference(
    fill: Fill,
    *,
    field: str,
    reported: Decimal,
    recomputed: Decimal,
) -> ReconciliationEconomicDifference | None:
    if reported == recomputed:
        return None
    return ReconciliationEconomicDifference(
        fill_id=fill.fill_id,
        field=field,
        reported=reported,
        recomputed=recomputed,
    )


def _fill_economics(
    fill: Fill,
) -> tuple[
    tuple[ReconciliationEconomicDifference, ...],
    Decimal,
    Decimal,
    Decimal,
]:
    gross = exact_multiply(fill.base_quantity, fill.execution_price)
    base_delta = fill.balance_deltas.get(fill.base, _ZERO)
    quote_delta = fill.balance_deltas.get(fill.quote, _ZERO)
    expected_base_delta = (
        fill.base_quantity
        if fill.side is FillSide.BUY
        else fill.base_quantity.copy_negate()
    )
    if fill.side is FillSide.BUY:
        fee = exact_subtract(quote_delta.copy_negate(), gross)
        slippage = exact_multiply(
            fill.base_quantity,
            exact_subtract(fill.execution_price, fill.reference_price),
        )
    else:
        fee = exact_subtract(gross, quote_delta)
        slippage = exact_multiply(
            fill.base_quantity,
            exact_subtract(fill.reference_price, fill.execution_price),
        )
    differences = tuple(
        item
        for item in (
            _economic_difference(
                fill,
                field="gross_quote_notional",
                reported=fill.gross_quote_notional,
                recomputed=gross,
            ),
            _economic_difference(
                fill,
                field="fee_amount",
                reported=fill.fee_amount,
                recomputed=fee,
            ),
            _economic_difference(
                fill,
                field="slippage_value",
                reported=fill.slippage_value,
                recomputed=slippage,
            ),
            _economic_difference(
                fill,
                field="base_balance_delta",
                reported=base_delta,
                recomputed=expected_base_delta,
            ),
        )
        if item is not None
    )
    return differences, fee, gross, slippage


def reconcile_fill_sequence(
    *,
    starting_state: PortfolioState,
    fills: Iterable[Fill],
    expected_states: Iterable[PortfolioState],
    valuation_prices: PriceSnapshot | None = None,
) -> ReconciliationReport:
    """Replay raw fill deltas independently and compare every expected state."""

    if not isinstance(cast(object, starting_state), PortfolioState):
        raise TypeError("starting_state must be PortfolioState")
    copied_fills = _validated_fills(fills)
    copied_states = _validated_states(expected_states)
    if len(copied_fills) != len(copied_states):
        raise ValueError("fills and expected_states must have the same length")

    if valuation_prices is not None and not isinstance(
        cast(object, valuation_prices), PriceSnapshot
    ):
        raise TypeError("valuation_prices must be PriceSnapshot or None")

    balances = dict(starting_state.holdings)
    steps: list[ReconciliationStep] = []
    economic_differences: list[ReconciliationEconomicDifference] = []
    reported_fee_total = _ZERO
    recomputed_fee_total = _ZERO
    reported_turnover = _ZERO
    recomputed_turnover = _ZERO
    reported_slippage_total = _ZERO
    recomputed_slippage_total = _ZERO
    recomputed_state = starting_state
    for fill, expected_state in zip(copied_fills, copied_states, strict=True):
        differences, fee, turnover, slippage = _fill_economics(fill)
        economic_differences.extend(differences)
        reported_fee_total = exact_add(reported_fee_total, fill.fee_amount)
        recomputed_fee_total = exact_add(recomputed_fee_total, fee)
        reported_turnover = exact_add(reported_turnover, fill.gross_quote_notional)
        recomputed_turnover = exact_add(recomputed_turnover, turnover)
        reported_slippage_total = exact_add(
            reported_slippage_total, fill.slippage_value
        )
        recomputed_slippage_total = exact_add(recomputed_slippage_total, slippage)
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

    expected_ending_state = copied_states[-1] if copied_states else starting_state
    expected_terminal_value = (
        None
        if valuation_prices is None
        else value_portfolio(expected_ending_state, valuation_prices)
    )
    recomputed_terminal_value = (
        None
        if valuation_prices is None
        else value_portfolio(recomputed_state, valuation_prices)
    )
    return ReconciliationReport(
        starting_state=starting_state,
        steps=tuple(steps),
        ending_state=recomputed_state,
        economic_differences=tuple(economic_differences),
        reported_fee_total=reported_fee_total,
        recomputed_fee_total=recomputed_fee_total,
        reported_turnover=reported_turnover,
        recomputed_turnover=recomputed_turnover,
        reported_slippage_total=reported_slippage_total,
        recomputed_slippage_total=recomputed_slippage_total,
        expected_terminal_value=expected_terminal_value,
        recomputed_terminal_value=recomputed_terminal_value,
    )


__all__ = [
    "ReconciliationDifference",
    "ReconciliationEconomicDifference",
    "ReconciliationReport",
    "ReconciliationStep",
    "reconcile_fill_sequence",
]
