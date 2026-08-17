import string
from collections.abc import MutableMapping
from decimal import Decimal
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from qap.portfolio import AssetId, PortfolioState

D = Decimal


def test_portfolio_state_copies_holdings_and_missing_assets_read_as_zero() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    source = {btc: D("2.5")}

    state = PortfolioState.from_holdings(source)
    source[btc] = D("99")

    assert state.quantity(btc) == D("2.5")
    assert state.quantity(eth) == D("0")
    assert dict(state.holdings) == {btc: D("2.5")}


def test_portfolio_state_does_not_expose_mutable_holdings() -> None:
    btc = AssetId("BTC")
    state = PortfolioState.from_holdings({btc: D("1")})
    mutable_holdings = cast(MutableMapping[AssetId, Decimal], state.holdings)

    with pytest.raises(TypeError):
        mutable_holdings[btc] = D("2")


def test_portfolio_state_normalizes_zero_and_orders_deterministically() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    sol = AssetId("SOL")

    first = PortfolioState.from_holdings(
        {eth: D("2.00"), sol: D("-0"), btc: D("1.0")}
    )
    second = PortfolioState.from_holdings({btc: D("1"), eth: D("2")})

    assert first == second
    assert hash(first) == hash(second)
    assert repr(first) == repr(second)
    assert dict(first.holdings) == {btc: D("1"), eth: D("2")}
    assert tuple(first.holdings) == (btc, eth)
    assert sol not in first.holdings


@pytest.mark.parametrize("quantity", [D("-1"), D("NaN"), D("Infinity")])
def test_portfolio_state_rejects_invalid_decimal_quantities(quantity: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        PortfolioState.from_holdings({AssetId("BTC"): quantity})


@pytest.mark.parametrize("quantity", [1, 1.0, "1"])
def test_portfolio_state_rejects_non_decimal_quantities(quantity: object) -> None:
    with pytest.raises(TypeError, match="must be Decimal"):
        PortfolioState.from_holdings({AssetId("BTC"): cast(Decimal, quantity)})


def test_apply_deltas_returns_a_new_state_and_removes_zero_balances() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    sol = AssetId("SOL")
    state = PortfolioState.from_holdings({btc: D("1.5"), eth: D("2")})

    updated = state.apply_deltas({btc: D("-1.5"), eth: D("0.25"), sol: D("3")})

    assert dict(state.holdings) == {btc: D("1.5"), eth: D("2")}
    assert dict(updated.holdings) == {eth: D("2.25"), sol: D("3")}


def test_apply_deltas_rejects_overdraft_without_changing_the_original_state() -> None:
    btc = AssetId("BTC")
    state = PortfolioState.from_holdings({btc: D("1")})

    with pytest.raises(ValueError, match="negative balance"):
        state.apply_deltas({btc: D("-1.00000001")})

    assert state.quantity(btc) == D("1")


def test_apply_deltas_rejects_non_decimal_deltas() -> None:
    state = PortfolioState.from_holdings({AssetId("BTC"): D("1")})

    with pytest.raises(TypeError, match="must be Decimal"):
        state.apply_deltas({AssetId("BTC"): cast(Decimal, -1.0)})


_asset_keys = st.text(
    alphabet=string.ascii_uppercase + string.digits,
    min_size=1,
    max_size=8,
)
_quantities = st.decimals(
    min_value=D("0"),
    max_value=D("1000000"),
    places=8,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def _valid_transition_cases(
    draw: DrawFn,
) -> tuple[
    dict[AssetId, Decimal],
    dict[AssetId, Decimal],
    dict[AssetId, Decimal],
]:
    keys = draw(st.lists(_asset_keys, min_size=1, max_size=6, unique=True))
    initial_quantities = draw(
        st.lists(_quantities, min_size=len(keys), max_size=len(keys))
    )
    final_quantities = draw(
        st.lists(_quantities, min_size=len(keys), max_size=len(keys))
    )
    assets = [AssetId(key) for key in keys]
    initial = dict(zip(assets, initial_quantities, strict=True))
    final = dict(zip(assets, final_quantities, strict=True))
    deltas = {asset: final[asset] - initial[asset] for asset in assets}
    return initial, deltas, final


@given(case=_valid_transition_cases())
def test_valid_generated_transitions_never_return_negative_inventory(
    case: tuple[
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
    ],
) -> None:
    initial, deltas, expected = case

    result = PortfolioState.from_holdings(initial).apply_deltas(deltas)

    assert all(quantity >= D("0") for quantity in result.holdings.values())
    assert dict(result.holdings) == {
        asset: quantity for asset, quantity in expected.items() if quantity != D("0")
    }


@given(case=_valid_transition_cases())
def test_identical_state_and_deltas_produce_equal_outputs(
    case: tuple[
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
    ],
) -> None:
    initial, deltas, _ = case
    state = PortfolioState.from_holdings(initial)

    assert state.apply_deltas(deltas) == state.apply_deltas(dict(deltas))


@given(case=_valid_transition_cases())
def test_zero_deltas_preserve_state_by_equality(
    case: tuple[
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
        dict[AssetId, Decimal],
    ],
) -> None:
    initial, _, _ = case
    state = PortfolioState.from_holdings(initial)
    zero_deltas = {asset: D("0") for asset in initial}

    assert state.apply_deltas(zero_deltas) == state
