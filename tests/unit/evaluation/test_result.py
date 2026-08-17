from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.evaluation import HodlBenchmark, build_economic_result
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

D = Decimal
USDT = AssetId("USDT")


def _snapshot(hour: int) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, hour, tzinfo=UTC),
        numeraire=USDT,
        prices={USDT: D("1")},
    )


def test_economic_result_accepts_explicit_non_negative_cost_fields() -> None:
    start = PortfolioState.from_holdings({USDT: D("100")})
    result = build_economic_result(
        strategy_start=start,
        strategy_states=[start, PortfolioState.from_holdings({USDT: D("105")})],
        benchmark=HodlBenchmark.from_start(start),
        price_snapshots=[_snapshot(0), _snapshot(1)],
        fees_value=D("1"),
        slippage_value=D("0.5"),
        turnover_value=D("50"),
        rebalance_count=1,
    )

    assert result.start_value == D("100")
    assert result.strategy_terminal_value == D("105")
    assert result.hodl_terminal_value == D("100")
    assert result.hodl_relative_basket_growth == D("0.05")
    assert result.fees_value == D("1")
    assert result.slippage_value == D("0.5")
    assert result.turnover_value == D("50")
    assert result.rebalance_count == 1

    with pytest.raises(ValueError, match="non-negative"):
        replace(result, fees_value=D("-0.01"))


@pytest.mark.parametrize(
    "field",
    ["fees_value", "slippage_value", "turnover_value"],
)
def test_economic_result_rejects_negative_supplied_cost_or_turnover(field: str) -> None:
    start = PortfolioState.from_holdings({USDT: D("100")})
    kwargs = {
        "fees_value": D("0"),
        "slippage_value": D("0"),
        "turnover_value": D("0"),
    }
    kwargs[field] = D("-0.01")

    with pytest.raises(ValueError, match="non-negative"):
        build_economic_result(
            strategy_start=start,
            strategy_states=[start],
            benchmark=HodlBenchmark.from_start(start),
            price_snapshots=[_snapshot(0)],
            rebalance_count=0,
            **kwargs,
        )


def test_economic_result_rejects_negative_or_non_integer_rebalance_count() -> None:
    start = PortfolioState.from_holdings({USDT: D("100")})

    with pytest.raises(ValueError, match="rebalance_count"):
        build_economic_result(
            strategy_start=start,
            strategy_states=[start],
            benchmark=HodlBenchmark.from_start(start),
            price_snapshots=[_snapshot(0)],
            rebalance_count=-1,
        )


def test_economic_result_persists_total_loss_without_log_relative_fabrication() -> None:
    start = PortfolioState.from_holdings({USDT: D("100")})
    result = build_economic_result(
        strategy_start=start,
        strategy_states=[start, PortfolioState.from_holdings({})],
        benchmark=HodlBenchmark.from_start(start),
        price_snapshots=[_snapshot(0), _snapshot(1)],
    )

    assert result.strategy_terminal_value == D("0")
    assert result.hodl_relative_basket_growth == D("-1")
    assert result.maximum_relative_drawdown == D("1")
    assert result.incremental_log_relative is None
    assert result.concentration.max_single_asset_weight is None
    assert result.concentration.herfindahl_index is None
