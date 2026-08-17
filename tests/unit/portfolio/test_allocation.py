from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
from typing import cast

import pytest

from qap.portfolio import AllocationTarget, AssetId
from qap.portfolio.allocation import ALLOCATION_SUM_TOLERANCE

D = Decimal


def test_allocation_target_accepts_exact_long_only_weights() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")

    target = AllocationTarget.for_basket(
        {btc: D("0.6"), eth: D("0.4")},
        basket={btc, eth},
    )

    assert dict(target.weights) == {btc: D("0.6"), eth: D("0.4")}


def test_allocation_target_accepts_total_at_declared_tolerance() -> None:
    btc = AssetId("BTC")

    target = AllocationTarget.for_basket(
        {btc: D("1") + ALLOCATION_SUM_TOLERANCE},
        basket={btc},
    )

    assert target.weights[btc] == D("1.000000000001")


def test_allocation_target_rejects_total_outside_declared_tolerance() -> None:
    btc = AssetId("BTC")

    with pytest.raises(ValueError, match="must sum to 1"):
        AllocationTarget.for_basket(
            {btc: D("1.0000000000011")},
            basket={btc},
        )


def test_allocation_target_rejects_negative_weights() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")

    with pytest.raises(ValueError, match="finite and non-negative"):
        AllocationTarget.for_basket(
            {btc: D("1.1"), eth: D("-0.1")},
            basket={btc, eth},
        )


@pytest.mark.parametrize("weight", [D("NaN"), D("Infinity")])
def test_allocation_target_rejects_non_finite_weights(weight: Decimal) -> None:
    btc = AssetId("BTC")

    with pytest.raises(ValueError, match="finite and non-negative"):
        AllocationTarget.for_basket({btc: weight}, basket={btc})


def test_allocation_target_rejects_non_decimal_weights() -> None:
    btc = AssetId("BTC")

    with pytest.raises(TypeError, match="must be Decimal"):
        AllocationTarget.for_basket(
            {btc: cast(Decimal, 1.0)},
            basket={btc},
        )


def test_allocation_target_rejects_empty_weights() -> None:
    with pytest.raises(ValueError, match="at least one asset"):
        AllocationTarget.for_basket({}, basket={AssetId("BTC")})


def test_allocation_target_rejects_assets_outside_the_declared_basket() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")

    with pytest.raises(ValueError, match="outside the declared basket.*ETH"):
        AllocationTarget.for_basket({btc: D("0.5"), eth: D("0.5")}, basket={btc})


def test_allocation_target_preserves_explicit_zero_weights() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")

    target = AllocationTarget.for_basket(
        {btc: D("1"), eth: D("0")},
        basket={btc, eth},
    )

    assert dict(target.weights) == {btc: D("1"), eth: D("0")}


def test_allocation_target_copies_and_orders_weights_deterministically() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    source = {eth: D("0.400"), btc: D("0.60")}

    first = AllocationTarget.for_basket(source, basket={eth, btc})
    source[btc] = D("1")
    second = AllocationTarget.for_basket(
        {btc: D("0.6"), eth: D("0.4")},
        basket={btc, eth},
    )

    assert first == second
    assert hash(first) == hash(second)
    assert repr(first) == repr(second)
    assert tuple(first.weights) == (btc, eth)
    assert first.weights[btc] == D("0.6")


def test_allocation_validation_is_independent_of_mapping_insertion_order() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    sol = AssetId("SOL")
    basket = {btc, eth, sol}

    with localcontext() as context:
        context.prec = 2
        first = AllocationTarget.for_basket(
            {btc: D("0.001"), eth: D("0.014"), sol: D("0.985")},
            basket=basket,
        )
        second = AllocationTarget.for_basket(
            {sol: D("0.985"), eth: D("0.014"), btc: D("0.001")},
            basket=basket,
        )

    assert first == second


def test_allocation_target_does_not_expose_mutable_weights() -> None:
    btc = AssetId("BTC")
    target = AllocationTarget.for_basket({btc: D("1")}, basket={btc})
    mutable_weights = cast(MutableMapping[AssetId, Decimal], target.weights)

    with pytest.raises(TypeError):
        mutable_weights[btc] = D("0")

    with pytest.raises(FrozenInstanceError):
        setattr(target, "_items", ())


def test_allocation_target_rejects_non_asset_basket_members() -> None:
    btc = AssetId("BTC")

    with pytest.raises(TypeError, match="basket members must be AssetId"):
        AllocationTarget.for_basket(
            {btc: D("1")},
            basket=[btc, cast(AssetId, "ETH")],
        )
