from datetime import UTC, datetime
from decimal import Decimal, localcontext

from hypothesis import given
from hypothesis import strategies as st

from qap.evaluation import (
    QuantityRatioStatus,
    concentration_diagnostics,
    terminal_attribution,
)
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
SOL = AssetId("SOL")
USDT = AssetId("USDT")


def _prices(values: dict[AssetId, Decimal]) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        numeraire=USDT,
        prices={USDT: D("1"), **values},
    )


def test_terminal_attribution_reconciles_quantity_and_value_deltas() -> None:
    hodl = PortfolioState.from_holdings({BTC: D("2"), ETH: D("10")})
    strategy = PortfolioState.from_holdings({BTC: D("3"), ETH: D("8")})

    attribution = terminal_attribution(
        strategy,
        hodl,
        _prices({BTC: D("100"), ETH: D("10")}),
    )

    by_asset = {item.asset: item for item in attribution}
    assert by_asset[BTC].quantity_delta == D("1")
    assert by_asset[BTC].quantity_ratio == D("1.5")
    assert by_asset[BTC].quantity_ratio_status is QuantityRatioStatus.COMPARABLE
    assert by_asset[BTC].value_delta == D("100")
    assert by_asset[ETH].quantity_delta == D("-2")
    assert by_asset[ETH].quantity_ratio == D("0.8")
    assert by_asset[ETH].value_delta == D("-20")
    assert sum((item.value_delta for item in attribution), D("0")) == D("80")
    with localcontext() as context:
        context.prec = 50
        contribution_sum = sum(
            (item.relative_value_contribution for item in attribution),
            D("0"),
        )
    assert abs(
        contribution_sum - D("0.26666666666666666666666666666666666666666666666667")
    ) <= D("1e-49")


def test_attribution_marks_zero_hodl_quantity_as_non_comparable() -> None:
    hodl = PortfolioState.from_holdings({BTC: D("1")})
    strategy = PortfolioState.from_holdings({BTC: D("1"), SOL: D("2")})

    by_asset = {
        item.asset: item
        for item in terminal_attribution(
            strategy,
            hodl,
            _prices({BTC: D("100"), SOL: D("20")}),
        )
    }

    assert by_asset[SOL].quantity_ratio is None
    assert by_asset[SOL].quantity_ratio_status is QuantityRatioStatus.NO_HODL_QUANTITY


def test_concentration_reports_equal_weight_single_asset_and_contributor_share() -> (
    None
):
    prices = _prices({BTC: D("100"), ETH: D("10")})
    equal = PortfolioState.from_holdings({BTC: D("1"), ETH: D("10")})
    equal_attr = terminal_attribution(equal, equal, prices)
    equal_result = concentration_diagnostics(equal, prices, equal_attr)

    assert equal_result.max_single_asset_weight == D("0.5")
    assert equal_result.herfindahl_index == D("0.5")
    assert equal_result.largest_positive_contributor_share is None

    hodl = PortfolioState.from_holdings({BTC: D("1"), ETH: D("10")})
    strategy = PortfolioState.from_holdings({BTC: D("2"), ETH: D("5")})
    attribution = terminal_attribution(strategy, hodl, prices)
    concentrated = concentration_diagnostics(strategy, prices, attribution)

    assert concentrated.max_single_asset_weight == D("0.8")
    assert concentrated.herfindahl_index == D("0.68")
    assert concentrated.largest_positive_contributor_share == D("1")

    single = PortfolioState.from_holdings({BTC: D("1")})
    single_result = concentration_diagnostics(
        single,
        prices,
        terminal_attribution(single, single, prices),
    )
    assert single_result.max_single_asset_weight == D("1")
    assert single_result.herfindahl_index == D("1")


def test_zero_value_portfolio_has_explicitly_undefined_value_concentration() -> None:
    hodl = PortfolioState.from_holdings({BTC: D("1")})
    strategy = PortfolioState.from_holdings({})
    prices = _prices({BTC: D("100")})
    attribution = terminal_attribution(strategy, hodl, prices)

    result = concentration_diagnostics(strategy, prices, attribution)

    assert result.max_single_asset_weight is None
    assert result.herfindahl_index is None
    assert result.largest_positive_contributor_share is None


@given(
    hodl_btc=st.integers(min_value=0, max_value=100),
    hodl_eth=st.integers(min_value=0, max_value=100),
    strategy_btc=st.integers(min_value=0, max_value=100),
    strategy_eth=st.integers(min_value=0, max_value=100),
    btc_price=st.integers(min_value=1, max_value=10_000),
    eth_price=st.integers(min_value=1, max_value=10_000),
)
def test_attribution_value_deltas_reconcile_for_generated_inventories(
    hodl_btc: int,
    hodl_eth: int,
    strategy_btc: int,
    strategy_eth: int,
    btc_price: int,
    eth_price: int,
) -> None:
    if hodl_btc == 0 and hodl_eth == 0:
        hodl_btc = 1
    hodl = PortfolioState.from_holdings({BTC: D(hodl_btc), ETH: D(hodl_eth)})
    strategy = PortfolioState.from_holdings(
        {BTC: D(strategy_btc), ETH: D(strategy_eth)}
    )
    prices = _prices({BTC: D(btc_price), ETH: D(eth_price)})

    attribution = terminal_attribution(strategy, hodl, prices)

    assert sum((item.value_delta for item in attribution), D("0")) == (
        sum((item.strategy_value for item in attribution), D("0"))
        - sum((item.hodl_value for item in attribution), D("0"))
    )
