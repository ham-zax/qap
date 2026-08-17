"""HODL-relative terminal and path economics."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qap.evaluation._decimal import (
    RECONCILIATION_TOLERANCE,
    divide,
    exact_subtract,
    exact_sum,
    natural_log,
)
from qap.evaluation.hodl import HodlBenchmark
from qap.evaluation.valuation import value_portfolio
from qap.market import PriceSnapshot
from qap.portfolio import PortfolioState

_ONE = Decimal("1")
_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class RelativeWealthPoint:
    timestamp: datetime
    strategy_value: Decimal
    hodl_value: Decimal
    relative_wealth: Decimal


@dataclass(frozen=True, slots=True)
class RelativeWealthPath:
    points: tuple[RelativeWealthPoint, ...]
    maximum_relative_drawdown: Decimal
    incremental_log_relative: tuple[Decimal, ...]


def hodl_relative_growth(
    *,
    strategy_start: PortfolioState,
    strategy_terminal: PortfolioState,
    benchmark: HodlBenchmark,
    prices: PriceSnapshot,
) -> Decimal:
    """Return terminal strategy/HODL wealth growth minus one."""

    benchmark.require_same_start(strategy_start)
    strategy_value = value_portfolio(strategy_terminal, prices)
    hodl_value = value_portfolio(benchmark.state, prices)
    if hodl_value <= _ZERO:
        raise ValueError("HODL terminal value must be positive")
    return exact_subtract(divide(strategy_value, hodl_value), _ONE)


def _maximum_drawdown(points: tuple[RelativeWealthPoint, ...]) -> Decimal:
    peak = points[0].relative_wealth
    maximum_drawdown = _ZERO
    for point in points:
        if point.relative_wealth > peak:
            peak = point.relative_wealth
        drawdown = exact_subtract(divide(point.relative_wealth, peak), _ONE)
        if drawdown < maximum_drawdown:
            maximum_drawdown = drawdown
    return maximum_drawdown


def _incremental_log_relative(
    points: tuple[RelativeWealthPoint, ...],
) -> tuple[Decimal, ...]:
    increments: list[Decimal] = []
    for previous, current in zip(points, points[1:]):
        strategy_log_growth = natural_log(
            divide(current.strategy_value, previous.strategy_value)
        )
        hodl_log_growth = natural_log(divide(current.hodl_value, previous.hodl_value))
        increments.append(exact_subtract(strategy_log_growth, hodl_log_growth))

    result = tuple(increments)
    terminal_log_ratio = natural_log(
        divide(points[-1].relative_wealth, points[0].relative_wealth)
    )
    if abs(exact_subtract(exact_sum(result), terminal_log_ratio)) > (
        RECONCILIATION_TOLERANCE
    ):
        raise ArithmeticError("incremental log-relative series did not reconcile")
    return result


def relative_wealth_path(
    *,
    strategy_start: PortfolioState,
    strategy_states: Sequence[PortfolioState],
    benchmark: HodlBenchmark,
    price_snapshots: Sequence[PriceSnapshot],
) -> RelativeWealthPath:
    """Build an aligned marked strategy-vs-HODL wealth path."""

    benchmark.require_same_start(strategy_start)
    states = tuple(strategy_states)
    snapshots = tuple(price_snapshots)
    if not states:
        raise ValueError("relative wealth path requires at least one state")
    if len(states) != len(snapshots):
        raise ValueError(
            "strategy states and price snapshots must have the same length"
        )
    if states[0] != strategy_start:
        raise ValueError("relative wealth path must begin at strategy_start")

    previous_timestamp: datetime | None = None
    points: list[RelativeWealthPoint] = []
    for state, snapshot in zip(states, snapshots, strict=True):
        if previous_timestamp is not None and snapshot.timestamp <= previous_timestamp:
            raise ValueError("price snapshot timestamps must be strictly increasing")
        previous_timestamp = snapshot.timestamp

        strategy_value = value_portfolio(state, snapshot)
        hodl_value = value_portfolio(benchmark.state, snapshot)
        if strategy_value <= _ZERO or hodl_value <= _ZERO:
            raise ValueError("relative wealth paths require strictly positive wealth")
        points.append(
            RelativeWealthPoint(
                timestamp=snapshot.timestamp,
                strategy_value=strategy_value,
                hodl_value=hodl_value,
                relative_wealth=divide(strategy_value, hodl_value),
            )
        )

    frozen_points = tuple(points)
    return RelativeWealthPath(
        points=frozen_points,
        maximum_relative_drawdown=_maximum_drawdown(frozen_points),
        incremental_log_relative=_incremental_log_relative(frozen_points),
    )
