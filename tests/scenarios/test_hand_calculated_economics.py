from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qap.evaluation import HodlBenchmark, build_economic_result
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")


def _snapshot(hour: int, *, btc: str, eth: str) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(hours=hour),
        numeraire=USDT,
        prices={USDT: D("1"), BTC: D(btc), ETH: D(eth)},
    )


def test_two_asset_economics_match_literal_hand_calculation() -> None:
    start = PortfolioState.from_holdings({BTC: D("2"), ETH: D("10")})
    middle = PortfolioState.from_holdings({BTC: D("2.5"), ETH: D("9")})
    terminal = PortfolioState.from_holdings({BTC: D("3"), ETH: D("8")})

    result = build_economic_result(
        strategy_start=start,
        strategy_states=[start, middle, terminal],
        benchmark=HodlBenchmark.from_start(start),
        price_snapshots=[
            _snapshot(0, btc="50", eth="10"),
            _snapshot(1, btc="80", eth="10"),
            _snapshot(2, btc="100", eth="10"),
        ],
        fees_value=D("2"),
        slippage_value=D("1"),
        turnover_value=D("100"),
        rebalance_count=1,
    )

    assert result.start_value == D("200")
    assert result.hodl_terminal_value == D("300")
    assert result.strategy_terminal_value == D("380")
    assert result.hodl_relative_basket_growth == D(
        "0.2666666666666666666666666666666666666666666666667"
    )
    assert result.maximum_relative_drawdown == D("0")

    by_asset = {item.asset: item for item in result.attribution}
    assert by_asset[BTC].value_delta == D("100")
    assert by_asset[ETH].value_delta == D("-20")
    assert result.concentration.max_single_asset_weight == D(
        "0.78947368421052631578947368421052631578947368421053"
    )
    assert result.concentration.herfindahl_index == D(
        "0.66759002770083102493074792243767313019390581717452"
    )
    assert result.concentration.largest_positive_contributor_share == D("1")
    assert result.fees_value == D("2")
    assert result.slippage_value == D("1")
    assert result.turnover_value == D("100")
    assert result.rebalance_count == 1
