"""Compact immutable economic evaluation result."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qap.evaluation._decimal import canonical_decimal, exact_subtract
from qap.evaluation.attribution import (
    AssetAttribution,
    ConcentrationDiagnostics,
    concentration_diagnostics,
    terminal_attribution,
)
from qap.evaluation.hodl import HodlBenchmark
from qap.evaluation.metrics import RelativeWealthPath, relative_wealth_path
from qap.market import PriceSnapshot
from qap.portfolio import PortfolioState

_ZERO = Decimal("0")
_ONE = Decimal("1")


@dataclass(frozen=True, slots=True)
class EconomicResult:
    start_timestamp: datetime
    terminal_timestamp: datetime
    start_value: Decimal
    strategy_terminal_value: Decimal
    hodl_terminal_value: Decimal
    hodl_relative_basket_growth: Decimal
    relative_wealth_path: RelativeWealthPath
    attribution: tuple[AssetAttribution, ...]
    concentration: ConcentrationDiagnostics
    fees_value: Decimal
    slippage_value: Decimal
    turnover_value: Decimal
    rebalance_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fees_value",
            _non_negative_decimal(self.fees_value, field="fees_value"),
        )
        object.__setattr__(
            self,
            "slippage_value",
            _non_negative_decimal(self.slippage_value, field="slippage_value"),
        )
        object.__setattr__(
            self,
            "turnover_value",
            _non_negative_decimal(self.turnover_value, field="turnover_value"),
        )
        object.__setattr__(
            self,
            "rebalance_count",
            _validated_rebalance_count(self.rebalance_count),
        )

    @property
    def maximum_relative_drawdown(self) -> Decimal:
        return self.relative_wealth_path.maximum_relative_drawdown

    @property
    def incremental_log_relative(self) -> tuple[Decimal, ...] | None:
        return self.relative_wealth_path.incremental_log_relative


def _non_negative_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value < _ZERO:
        raise ValueError(f"{field} must be finite and non-negative")
    return canonical_decimal(value)


def _validated_rebalance_count(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("rebalance_count must be an integer")
    if value < 0:
        raise ValueError("rebalance_count must be non-negative")
    return value


def build_economic_result(
    *,
    strategy_start: PortfolioState,
    strategy_states: Sequence[PortfolioState],
    benchmark: HodlBenchmark,
    price_snapshots: Sequence[PriceSnapshot],
    fees_value: Decimal = _ZERO,
    slippage_value: Decimal = _ZERO,
    turnover_value: Decimal = _ZERO,
    rebalance_count: int = 0,
) -> EconomicResult:
    """Build one read-only economic result from aligned states and marks."""

    validated_rebalance_count = _validated_rebalance_count(rebalance_count)
    fees = _non_negative_decimal(fees_value, field="fees_value")
    slippage = _non_negative_decimal(slippage_value, field="slippage_value")
    turnover = _non_negative_decimal(turnover_value, field="turnover_value")

    states = tuple(strategy_states)
    snapshots = tuple(price_snapshots)
    path = relative_wealth_path(
        strategy_start=strategy_start,
        strategy_states=states,
        benchmark=benchmark,
        price_snapshots=snapshots,
    )
    terminal_state = states[-1]
    terminal_prices = snapshots[-1]
    attribution = terminal_attribution(terminal_state, benchmark.state, terminal_prices)
    concentration = concentration_diagnostics(
        terminal_state,
        terminal_prices,
        attribution,
    )
    first = path.points[0]
    terminal = path.points[-1]
    return EconomicResult(
        start_timestamp=first.timestamp,
        terminal_timestamp=terminal.timestamp,
        start_value=first.strategy_value,
        strategy_terminal_value=terminal.strategy_value,
        hodl_terminal_value=terminal.hodl_value,
        hodl_relative_basket_growth=exact_subtract(terminal.relative_wealth, _ONE),
        relative_wealth_path=path,
        attribution=attribution,
        concentration=concentration,
        fees_value=fees,
        slippage_value=slippage,
        turnover_value=turnover,
        rebalance_count=validated_rebalance_count,
    )
