from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId
from qap.relationship import (
    NormalizationScale,
    RelationshipDataError,
    build_normalized_path,
    normalize_to_hundred,
    normalize_to_one,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")


def _series(
    asset: AssetId,
    closes: tuple[float, ...],
    *,
    start_hour: int = 10,
):
    instrument = VenueInstrument(
        venue="fixture",
        venue_symbol=f"{asset.key}USDT",
        base=asset,
        quote=USDT,
    )
    start = datetime(2024, 1, 1, start_hour, tzinfo=UTC)
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=start + position * INTERVAL.duration,
                source_close_time=(
                    start
                    + (position + 1) * INTERVAL.duration
                    - timedelta(milliseconds=1)
                ),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1.0,
            )
            for position, close in enumerate(closes)
        )
    )


def _aligned(
    btc_closes: tuple[float, ...] = (10.0, 20.0, 5.0),
    eth_closes: tuple[float, ...] = (4.0, 5.0, 6.0),
    *,
    btc_start_hour: int = 10,
    eth_start_hour: int = 10,
):
    return align_bar_series(
        (
            _series(BTC, btc_closes, start_hour=btc_start_hour),
            _series(ETH, eth_closes, start_hour=eth_start_hour),
        )
    )


def test_normalization_starts_at_exact_declared_scale() -> None:
    values = [2.0, 4.0, 1.0]

    to_one = normalize_to_one(values)
    to_hundred = normalize_to_hundred(values)

    np.testing.assert_allclose(to_one, [1.0, 2.0, 0.5])
    np.testing.assert_allclose(to_hundred, [100.0, 200.0, 50.0])
    assert to_one[0] == 1.0
    assert to_hundred[0] == 100.0
    assert not to_one.flags.writeable
    assert not to_hundred.flags.writeable


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ([], "non-empty"),
        ([0.0, 1.0], "strictly positive"),
        ([1.0, float("inf")], "finite"),
        ([1e-308, 1e308], "finite and strictly positive"),
        ([[1.0]], "one-dimensional"),
    ],
)
def test_normalization_rejects_invalid_inputs(
    values: object,
    message: str,
) -> None:
    with pytest.raises(RelationshipDataError, match=message):
        normalize_to_one(values)


def test_normalized_path_uses_the_aligned_common_timestamp_index() -> None:
    aligned = _aligned(
        btc_closes=(10.0, 20.0, 5.0),
        eth_closes=(4.0, 5.0, 6.0),
        btc_start_hour=9,
        eth_start_hour=10,
    )

    path = build_normalized_path(
        aligned,
        asset=BTC,
        scale=NormalizationScale.ONE,
        source_fingerprint="f" * 64,
        as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
    )

    assert path.asset == BTC
    assert path.timestamps == aligned.timestamps
    assert path.window_start == datetime(2024, 1, 1, 10, tzinfo=UTC)
    assert path.window_end_exclusive == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert path.as_of == datetime(2024, 1, 1, 12, tzinfo=UTC)
    assert path.scale is NormalizationScale.ONE
    assert path.source_fingerprint == "f" * 64
    assert path.values == (1.0, 0.25)
    assert path.descriptive_only is True


def test_normalized_path_rejects_asset_not_in_aligned_pair() -> None:
    with pytest.raises(RelationshipDataError, match="exactly one leg"):
        build_normalized_path(
            _aligned(),
            asset=AssetId("SOL"),
            scale=NormalizationScale.ONE,
            source_fingerprint="f" * 64,
            as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        )
