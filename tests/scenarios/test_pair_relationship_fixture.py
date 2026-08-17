from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

from qap.market import (
    BarInterval,
    VenueInstrument,
    align_bar_series,
    fingerprint_bar_series,
    load_csv_bar_series,
)
from qap.portfolio import AssetId, PairOrientation, PortfolioState
from qap.relationship import (
    AnchorReduction,
    NormalizationScale,
    build_anchor_lens,
    build_log_ratio_series,
    build_normalized_path,
    build_ratio_series,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "market"
BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")


def _instrument(base: AssetId) -> VenueInstrument:
    return VenueInstrument(
        venue="binance",
        venue_symbol=f"{base.key}USDT",
        base=base,
        quote=USDT,
    )


def test_committed_pair_fixture_builds_reciprocal_descriptive_evidence() -> None:
    interval = BarInterval("1h")
    btc = load_csv_bar_series(
        FIXTURES / "BTCUSDT_1h.csv",
        instrument=_instrument(BTC),
        interval=interval,
    )
    eth = load_csv_bar_series(
        FIXTURES / "ETHUSDT_1h.csv",
        instrument=_instrument(ETH),
        interval=interval,
    )
    aligned = align_bar_series([btc, eth])
    fingerprints = {
        BTC: fingerprint_bar_series(btc),
        ETH: fingerprint_bar_series(eth),
    }
    as_of = datetime(2024, 1, 1, 12, tzinfo=UTC)
    starting_inventory = PortfolioState.from_holdings(
        {BTC: Decimal("1"), ETH: Decimal("2")}
    )

    eth_btc = build_ratio_series(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    btc_eth = build_ratio_series(
        aligned,
        orientation=PairOrientation(base=BTC, quote=ETH),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    eth_btc_log = build_log_ratio_series(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    btc_eth_log = build_log_ratio_series(
        aligned,
        orientation=PairOrientation(base=BTC, quote=ETH),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    btc_normalized = build_normalized_path(
        aligned,
        asset=BTC,
        scale=NormalizationScale.ONE,
        source_fingerprint=fingerprints[BTC],
        as_of=as_of,
    )
    eth_normalized = build_normalized_path(
        aligned,
        asset=ETH,
        scale=NormalizationScale.ONE,
        source_fingerprint=fingerprints[ETH],
        as_of=as_of,
    )
    lens = build_anchor_lens(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        anchor=USDT,
        source_fingerprints={
            ETH: fingerprints[ETH],
            BTC: fingerprints[BTC],
        },
        as_of=as_of,
    )

    assert eth_btc.pair_id == btc_eth.pair_id
    np.testing.assert_allclose(
        np.array(eth_btc.values) * np.array(btc_eth.values),
        1.0,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        np.array(eth_btc_log.values),
        -np.array(btc_eth_log.values),
        rtol=1e-12,
        atol=1e-12,
    )
    assert eth_btc.base_source_fingerprint == fingerprints[ETH]
    assert eth_btc.quote_source_fingerprint == fingerprints[BTC]
    assert btc_normalized.values[0] == 1.0
    assert eth_normalized.values[0] == 1.0
    assert lens.reduction is AnchorReduction.NONE
    np.testing.assert_allclose(lens.pair_ratio, eth_btc.values)
    assert starting_inventory == PortfolioState.from_holdings(
        {BTC: Decimal("1"), ETH: Decimal("2")}
    )
