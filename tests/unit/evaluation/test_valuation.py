from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.evaluation import value_portfolio
from qap.market import PriceSnapshot
from qap.portfolio import AssetId, PortfolioState

D = Decimal


def _prices(values: dict[AssetId, Decimal]) -> PriceSnapshot:
    return PriceSnapshot.from_prices(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        numeraire=AssetId("USDT"),
        prices=values,
    )


def test_value_portfolio_uses_every_explicit_held_asset_price() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    usdt = AssetId("USDT")
    state = PortfolioState.from_holdings({btc: D("1"), eth: D("2"), usdt: D("100")})

    value = value_portfolio(
        state,
        _prices({btc: D("10"), eth: D("5"), usdt: D("1")}),
    )

    assert value == D("120")


def test_value_portfolio_fails_closed_for_missing_held_asset_price() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    usdt = AssetId("USDT")
    state = PortfolioState.from_holdings({btc: D("1"), eth: D("2")})

    with pytest.raises(ValueError, match="explicit price.*ETH"):
        value_portfolio(state, _prices({btc: D("10"), usdt: D("1")}))


def test_value_portfolio_empty_inventory_is_exact_zero() -> None:
    usdt = AssetId("USDT")
    state = PortfolioState.from_holdings({})

    assert value_portfolio(state, _prices({usdt: D("1")})) == D("0")
