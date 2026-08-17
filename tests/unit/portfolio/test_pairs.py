import string
from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.portfolio import AssetId, PairId, PairOrientation


def test_pair_id_canonicalizes_asset_order() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")

    assert PairId(btc, eth) == PairId(eth, btc)
    assert PairId(eth, btc).first == btc
    assert PairId(eth, btc).second == eth


def test_pair_orientation_preserves_requested_base_and_quote() -> None:
    btc = AssetId("BTC")
    eth = AssetId("ETH")
    orientation = PairOrientation(base=btc, quote=eth)

    assert orientation.base == btc
    assert orientation.quote == eth
    assert orientation.pair_id == PairId(btc, eth)
    assert orientation.inverted() == PairOrientation(base=eth, quote=btc)


@pytest.mark.parametrize("pair_type", [PairId, PairOrientation])
def test_pairs_reject_the_same_asset_twice(
    pair_type: type[PairId] | type[PairOrientation],
) -> None:
    btc = AssetId("BTC")

    with pytest.raises(ValueError, match="must be distinct"):
        pair_type(btc, btc)


def test_pair_values_are_frozen() -> None:
    orientation = PairOrientation(AssetId("BTC"), AssetId("ETH"))

    with pytest.raises(FrozenInstanceError):
        setattr(orientation, "base", AssetId("SOL"))


_asset_keys = st.text(
    alphabet=string.ascii_uppercase + string.digits,
    min_size=1,
    max_size=8,
)
_distinct_asset_keys = st.lists(_asset_keys, min_size=2, max_size=2, unique=True)


@given(keys=_distinct_asset_keys)
def test_pair_identity_is_orientation_independent_and_inversion_is_involutive(
    keys: list[str],
) -> None:
    first, second = (AssetId(key) for key in keys)
    orientation = PairOrientation(first, second)
    inverse = orientation.inverted()

    assert orientation.pair_id == inverse.pair_id
    assert inverse.inverted() == orientation
