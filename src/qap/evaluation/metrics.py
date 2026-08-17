"""HODL-relative terminal and path economics."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

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
_LOG_UNAVAILABLE = (
    "incremental log-relative performance requires strictly positive "
    "candidate and control wealth"
)


@dataclass(frozen=True, slots=True)
class RelativeWealthPoint:
    """One aligned strategy-versus-HODL marked-wealth observation."""

    timestamp: datetime
    strategy_value: Decimal
    hodl_value: Decimal
    relative_wealth: Decimal


@dataclass(frozen=True, slots=True)
class RelativeWealthPath:
    """Aligned wealth path plus drawdown and optional log-relative increments."""

    points: tuple[RelativeWealthPoint, ...]
    maximum_relative_drawdown: Decimal
    incremental_log_relative: tuple[Decimal, ...] | None
    incremental_log_relative_unavailable_reason: str | None

    @property
    def timestamps(self) -> tuple[datetime, ...]:
        return tuple(point.timestamp for point in self.points)

    @property
    def relative_wealth(self) -> tuple[Decimal, ...]:
        return tuple(point.relative_wealth for point in self.points)

    @property
    def incremental_log_ending_timestamps(self) -> tuple[datetime, ...]:
        return self.timestamps[1:]


def _copied_states(values: object) -> tuple[PortfolioState, ...]:
    if not isinstance(values, Sequence):
        raise TypeError("strategy_states must be a sequence")
    copied: list[PortfolioState] = []
    for position, value in enumerate(cast(Sequence[object], values)):
        if not isinstance(value, PortfolioState):
            raise TypeError(f"strategy state {position} must be a PortfolioState")
        copied.append(value)
    return tuple(copied)


def _copied_snapshots(values: object) -> tuple[PriceSnapshot, ...]:
    if not isinstance(values, Sequence):
        raise TypeError("price_snapshots must be a sequence")
    copied: list[PriceSnapshot] = []
    for position, value in enumerate(cast(Sequence[object], values)):
        if not isinstance(value, PriceSnapshot):
            raise TypeError(f"price snapshot {position} must be a PriceSnapshot")
        copied.append(value)
    return tuple(copied)


def _copied_decimal_values(values: object, *, field: str) -> tuple[Decimal, ...]:
    if not isinstance(values, Sequence):
        raise TypeError(f"{field} values must be a sequence")
    copied: list[Decimal] = []
    for position, value in enumerate(cast(Sequence[object], values)):
        if not isinstance(value, Decimal):
            raise TypeError(f"{field} value {position} must be Decimal")
        copied.append(value)
    return tuple(copied)


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
        drawdown = exact_subtract(_ONE, divide(point.relative_wealth, peak))
        if drawdown > maximum_drawdown:
            maximum_drawdown = drawdown
    return maximum_drawdown


def incremental_log_relative_series(
    candidate_values: Sequence[Decimal],
    control_values: Sequence[Decimal],
) -> tuple[Decimal, ...]:
    """Return aligned candidate-minus-control incremental log performance."""

    candidates = _copied_decimal_values(candidate_values, field="candidate")
    controls = _copied_decimal_values(control_values, field="control")
    if not candidates:
        raise ValueError("incremental log-relative performance requires values")
    if len(candidates) != len(controls):
        raise ValueError("candidate and control values must have the same length")
    for value in (*candidates, *controls):
        if not value.is_finite() or value <= _ZERO:
            raise ValueError(_LOG_UNAVAILABLE)

    candidate_logs = tuple(natural_log(value) for value in candidates)
    control_logs = tuple(natural_log(value) for value in controls)
    result = tuple(
        exact_sum(
            (
                candidate_logs[position],
                candidate_logs[position - 1].copy_negate(),
                control_logs[position].copy_negate(),
                control_logs[position - 1],
            )
        )
        for position in range(1, len(candidates))
    )
    terminal_log_ratio = exact_sum(
        (
            candidate_logs[-1],
            candidate_logs[0].copy_negate(),
            control_logs[-1].copy_negate(),
            control_logs[0],
        )
    )
    reconciliation_error = exact_subtract(
        exact_sum(result), terminal_log_ratio
    ).copy_abs()
    if reconciliation_error > RECONCILIATION_TOLERANCE:
        raise ArithmeticError("incremental log-relative series did not reconcile")
    return result


def _incremental_log_relative(
    points: tuple[RelativeWealthPoint, ...],
) -> tuple[Decimal, ...]:
    return incremental_log_relative_series(
        tuple(point.strategy_value for point in points),
        tuple(point.hodl_value for point in points),
    )


def require_incremental_log_relative(path: RelativeWealthPath) -> tuple[Decimal, ...]:
    """Return aligned log-relative increments or fail explicitly."""

    increments = path.incremental_log_relative
    if increments is None:
        raise ValueError(
            path.incremental_log_relative_unavailable_reason or _LOG_UNAVAILABLE
        )
    return increments


def relative_wealth_path(
    *,
    strategy_start: PortfolioState,
    strategy_states: Sequence[PortfolioState],
    benchmark: HodlBenchmark,
    price_snapshots: Sequence[PriceSnapshot],
) -> RelativeWealthPath:
    """Build an aligned marked strategy-vs-HODL wealth path."""

    benchmark.require_same_start(strategy_start)
    states = _copied_states(strategy_states)
    snapshots = _copied_snapshots(price_snapshots)
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
        if hodl_value <= _ZERO:
            raise ValueError("relative wealth paths require positive HODL wealth")
        points.append(
            RelativeWealthPoint(
                timestamp=snapshot.timestamp,
                strategy_value=strategy_value,
                hodl_value=hodl_value,
                relative_wealth=divide(strategy_value, hodl_value),
            )
        )

    frozen_points = tuple(points)
    if all(point.strategy_value > _ZERO for point in frozen_points):
        increments: tuple[Decimal, ...] | None = _incremental_log_relative(
            frozen_points
        )
        unavailable_reason: str | None = None
    else:
        increments = None
        unavailable_reason = _LOG_UNAVAILABLE

    return RelativeWealthPath(
        points=frozen_points,
        maximum_relative_drawdown=_maximum_drawdown(frozen_points),
        incremental_log_relative=increments,
        incremental_log_relative_unavailable_reason=unavailable_reason,
    )
