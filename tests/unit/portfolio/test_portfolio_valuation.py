from decimal import Decimal, localcontext

import pytest

from qap.portfolio import (
    AssetId,
    PortfolioState,
    holding_values_at_prices,
    value_holdings_at_prices,
)

D = Decimal


def test_holding_values_and_total_share_one_exact_valuation_truth() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    state = PortfolioState.from_holdings({btc: D("2"), eth: D("3")})
    prices = {btc: D("10"), eth: D("4")}

    contributions = holding_values_at_prices(state, prices)

    assert dict(contributions) == {btc: D("20"), eth: D("12")}
    assert value_holdings_at_prices(state, prices) == D("32")


def test_valuation_is_independent_of_ambient_decimal_context() -> None:
    btc = AssetId("BTC")
    state = PortfolioState.from_holdings({btc: D("9.85e999")})
    prices = {btc: D("1.01e1000")}

    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        context.Emin = -2
        actual = value_holdings_at_prices(state, prices)

    assert actual == D("9.9485e1999")


def test_valuation_rejects_missing_or_invalid_prices() -> None:
    btc = AssetId("BTC")
    state = PortfolioState.from_holdings({btc: D("1")})

    with pytest.raises(ValueError, match="missing price.*BTC"):
        value_holdings_at_prices(state, {})
    with pytest.raises(ValueError, match="finite and strictly positive"):
        value_holdings_at_prices(state, {btc: D("0")})
