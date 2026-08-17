from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from qap.evaluation import (
    HodlBenchmark,
    hodl_relative_growth,
    incremental_log_relative_series,
    relative_wealth_path,
    require_incremental_log_relative,
)
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

D = Decimal
USDT = AssetId("USDT")


def _state(value: str) -> PortfolioState:
    return PortfolioState.from_holdings({USDT: D(value)})


def _snapshot(hour: int) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(hours=hour),
        numeraire=USDT,
        prices={USDT: D("1")},
    )


@pytest.mark.parametrize(
    ("terminal", "expected"),
    [
        ("100", D("0")),
        ("110", D("0.1")),
        ("90", D("-0.1")),
    ],
)
def test_terminal_hodl_relative_growth_allows_ties_gains_and_losses(
    terminal: str,
    expected: Decimal,
) -> None:
    start = _state("100")
    benchmark = HodlBenchmark.from_start(start)

    assert (
        hodl_relative_growth(
            strategy_start=start,
            strategy_terminal=_state(terminal),
            benchmark=benchmark,
            prices=_snapshot(4),
        )
        == expected
    )


def test_relative_wealth_path_reports_literal_drawdown_and_log_reconciliation() -> None:
    start = _state("100")
    benchmark = HodlBenchmark.from_start(start)
    path = relative_wealth_path(
        strategy_start=start,
        strategy_states=[start, _state("120"), _state("90"), _state("110")],
        benchmark=benchmark,
        price_snapshots=[_snapshot(0), _snapshot(1), _snapshot(2), _snapshot(3)],
    )

    assert tuple(point.relative_wealth for point in path.points) == (
        D("1"),
        D("1.2"),
        D("0.9"),
        D("1.1"),
    )
    assert path.maximum_relative_drawdown == D("0.25")
    increments = require_incremental_log_relative(path)
    assert len(increments) == 3
    with localcontext() as context:
        context.prec = 50
        expected_log_ratio = D("1.1").ln()
        incremental_sum = sum(increments, D("0"))
    assert abs(incremental_sum - expected_log_ratio) <= D("1e-45")


def test_relative_wealth_path_preserves_zero_wealth_but_refuses_log_transform() -> None:
    start = _state("100")
    benchmark = HodlBenchmark.from_start(start)

    path = relative_wealth_path(
        strategy_start=start,
        strategy_states=[start, PortfolioState.from_holdings({})],
        benchmark=benchmark,
        price_snapshots=[_snapshot(0), _snapshot(1)],
    )

    assert tuple(point.relative_wealth for point in path.points) == (D("1"), D("0"))
    assert path.maximum_relative_drawdown == D("1")
    assert path.incremental_log_relative is None
    assert path.incremental_log_relative_unavailable_reason is not None
    with pytest.raises(ValueError, match="strictly positive"):
        require_incremental_log_relative(path)


def test_relative_wealth_path_rejects_misalignment() -> None:
    start = _state("100")
    benchmark = HodlBenchmark.from_start(start)

    with pytest.raises(ValueError, match="same length"):
        relative_wealth_path(
            strategy_start=start,
            strategy_states=[start],
            benchmark=benchmark,
            price_snapshots=[_snapshot(0), _snapshot(1)],
        )

    with pytest.raises(ValueError, match="strictly increasing"):
        relative_wealth_path(
            strategy_start=start,
            strategy_states=[start, start],
            benchmark=benchmark,
            price_snapshots=[_snapshot(0), _snapshot(0)],
        )


def test_terminal_hodl_relative_growth_supports_total_strategy_loss() -> None:
    start = _state("100")

    assert hodl_relative_growth(
        strategy_start=start,
        strategy_terminal=PortfolioState.from_holdings({}),
        benchmark=HodlBenchmark.from_start(start),
        prices=_snapshot(1),
    ) == D("-1")


def test_incremental_log_relative_series_supports_a_declared_control() -> None:
    candidate = (D("100"), D("110"), D("121"))
    control = (D("100"), D("105"), D("110.25"))

    increments = incremental_log_relative_series(candidate, control)

    assert len(increments) == 2
    with localcontext() as context:
        context.prec = 50
        expected = (D("1.21") / D("1.1025")).ln()
        actual = sum(increments, D("0"))
    assert abs(actual - expected) <= D("1e-45")


def test_incremental_log_relative_series_is_context_independent() -> None:
    candidate = (D("9.85e999"), D("1.01e1000"))
    control = (D("8.25e999"), D("8.5e999"))

    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        context.Emin = -2
        actual = incremental_log_relative_series(candidate, control)

    assert actual == incremental_log_relative_series(candidate, control)


@pytest.mark.parametrize(
    ("candidate", "control", "message"),
    [
        ((D("1"),), (), "same length"),
        ((D("1"), D("0")), (D("1"), D("1")), "strictly positive"),
    ],
)
def test_incremental_log_relative_series_rejects_invalid_paths(
    candidate: tuple[Decimal, ...],
    control: tuple[Decimal, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        incremental_log_relative_series(candidate, control)
