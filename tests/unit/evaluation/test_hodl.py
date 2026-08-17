from decimal import Decimal

import pytest

from qap.evaluation import HodlBenchmark
from qap.portfolio import AssetId, PortfolioState

D = Decimal


def test_hodl_preserves_the_exact_starting_inventory() -> None:
    start = PortfolioState.from_holdings(
        {AssetId("BTC"): D("1.25"), AssetId("ETH"): D("4")}
    )
    benchmark = HodlBenchmark.from_start(start)

    assert benchmark.starting_state == start
    assert benchmark.state == start
    assert benchmark.state is start
    benchmark.require_same_start(start)


def test_hodl_rejects_a_strategy_with_a_different_declared_start() -> None:
    start = PortfolioState.from_holdings({AssetId("BTC"): D("1")})
    different = PortfolioState.from_holdings({AssetId("BTC"): D("2")})
    benchmark = HodlBenchmark.from_start(start)

    with pytest.raises(ValueError, match="same starting inventory"):
        benchmark.require_same_start(different)
