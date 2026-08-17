from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from qap.evaluation import (
    HodlBenchmark,
    hodl_relative_growth,
    relative_wealth_path,
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
    assert path.maximum_relative_drawdown == D("-0.25")
    assert len(path.incremental_log_relative) == 3
    with localcontext() as context:
        context.prec = 50
        expected_log_ratio = D("1.1").ln()
        incremental_sum = sum(path.incremental_log_relative, D("0"))
    assert abs(incremental_sum - expected_log_ratio) <= D("1e-45")


def test_relative_wealth_path_rejects_non_positive_wealth_and_misalignment() -> None:
    start = _state("100")
    benchmark = HodlBenchmark.from_start(start)

    with pytest.raises(ValueError, match="strictly positive"):
        relative_wealth_path(
            strategy_start=start,
            strategy_states=[start, PortfolioState.from_holdings({})],
            benchmark=benchmark,
            price_snapshots=[_snapshot(0), _snapshot(1)],
        )

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
