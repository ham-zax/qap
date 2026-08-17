from dataclasses import FrozenInstanceError

import pytest

from qap.portfolio import AssetId


def test_asset_id_normalizes_the_stable_key() -> None:
    assert AssetId(" btc ") == AssetId("BTC")
    assert AssetId(" btc ").key == "BTC"


def test_asset_id_order_is_deterministic_by_normalized_key() -> None:
    assert sorted([AssetId("eth"), AssetId("btc")]) == [
        AssetId("BTC"),
        AssetId("ETH"),
    ]


@pytest.mark.parametrize("key", ["", "   "])
def test_asset_id_rejects_empty_keys(key: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        AssetId(key)


@pytest.mark.parametrize("key", ["BTC/USDT", " / "])
def test_asset_id_rejects_pair_separators(key: str) -> None:
    with pytest.raises(ValueError, match="must not contain"):
        AssetId(key)


def test_asset_id_rejects_non_string_keys() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        AssetId(123)  # type: ignore[arg-type]


def test_asset_id_is_frozen() -> None:
    asset = AssetId("BTC")

    with pytest.raises(FrozenInstanceError):
        setattr(asset, "key", "ETH")
