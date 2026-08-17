from decimal import Decimal

from qap.portfolio import AllocationTarget, AssetId, PortfolioState

D = Decimal


def test_two_asset_inventory_transition_and_allocation_target() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    starting = PortfolioState.from_holdings({btc: D("2"), eth: D("1")})

    terminal = starting.apply_deltas({btc: D("-0.5"), eth: D("0.25")})
    target = AllocationTarget.for_basket(
        {btc: D("0.6"), eth: D("0.4")},
        basket={btc, eth},
    )

    assert dict(starting.holdings) == {btc: D("2"), eth: D("1")}
    assert dict(terminal.holdings) == {btc: D("1.5"), eth: D("1.25")}
    assert dict(target.weights) == {btc: D("0.6"), eth: D("0.4")}
