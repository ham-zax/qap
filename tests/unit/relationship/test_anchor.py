from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import (
    AnchorReduction,
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    build_anchor_lens,
    identity_source_fingerprint,
)

ETH = AssetId("ETH")
BTC = AssetId("BTC")
SOL = AssetId("SOL")
USDT = AssetId("USDT")
USDC = AssetId("USDC")
INTERVAL = BarInterval("1h")
AS_OF = datetime(2024, 1, 1, 13, tzinfo=UTC)
FINGERPRINTS = {
    ETH: "e" * 64,
    BTC: "b" * 64,
    SOL: "5" * 64,
}


def _series(
    asset: AssetId,
    closes: tuple[float, ...],
    *,
    reference: AssetId = USDT,
):
    instrument = VenueInstrument(
        venue="fixture",
        venue_symbol=f"{asset.key}{reference.key}",
        base=asset,
        quote=reference,
    )
    start = datetime(2024, 1, 1, 10, tzinfo=UTC)
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


def _aligned_three(
    base: tuple[float, ...] = (20.0, 40.0, 30.0),
    quote: tuple[float, ...] = (5.0, 10.0, 6.0),
    anchor: tuple[float, ...] = (10.0, 20.0, 15.0),
):
    return align_bar_series(
        (
            _series(ETH, base),
            _series(BTC, quote),
            _series(SOL, anchor),
        )
    )


def test_anchor_lens_reconciles_ratio_and_log_decompositions() -> None:
    aligned = _aligned_three()

    lens = build_anchor_lens(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        anchor=SOL,
        source_fingerprints=FINGERPRINTS,
        as_of=AS_OF,
    )

    assert lens.pair_id == PairOrientation(base=ETH, quote=BTC).pair_id
    assert lens.reduction is AnchorReduction.NONE
    assert lens.base_source_fingerprint == "e" * 64
    assert lens.quote_source_fingerprint == "b" * 64
    assert lens.anchor_source_fingerprint == "5" * 64
    assert lens.fit_reciprocity is FitReciprocity.EXACT_TRANSFORM
    assert lens.evidence_reciprocity is EvidenceReciprocity.EXACT_TRANSFORM
    np.testing.assert_allclose(lens.pair_ratio, [4.0, 4.0, 5.0])
    np.testing.assert_allclose(lens.base_to_anchor, [2.0, 2.0, 2.0])
    np.testing.assert_allclose(lens.quote_to_anchor, [0.5, 0.5, 0.4])
    np.testing.assert_allclose(
        np.array(lens.base_to_anchor) / np.array(lens.quote_to_anchor),
        lens.pair_ratio,
    )
    np.testing.assert_allclose(
        np.array(lens.base_to_anchor_log) - np.array(lens.quote_to_anchor_log),
        lens.pair_log_ratio,
    )
    assert lens.max_ratio_decomposition_error <= 1e-12
    assert lens.max_log_decomposition_error <= 1e-12
    assert lens.descriptive_only is True


@pytest.mark.parametrize(
    ("anchor", "reduction", "base_anchor", "quote_anchor"),
    [
        (ETH, AnchorReduction.ANCHOR_IS_BASE, [1.0, 1.0, 1.0], [0.25, 0.25, 0.2]),
        (BTC, AnchorReduction.ANCHOR_IS_QUOTE, [4.0, 4.0, 5.0], [1.0, 1.0, 1.0]),
    ],
)
def test_anchor_equal_to_pair_leg_returns_explicit_reduced_identity(
    anchor: AssetId,
    reduction: AnchorReduction,
    base_anchor: list[float],
    quote_anchor: list[float],
) -> None:
    aligned = align_bar_series(
        (
            _series(ETH, (20.0, 40.0, 30.0)),
            _series(BTC, (5.0, 10.0, 6.0)),
        )
    )

    lens = build_anchor_lens(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        anchor=anchor,
        source_fingerprints=FINGERPRINTS,
        as_of=AS_OF,
    )

    assert lens.reduction is reduction
    assert lens.anchor_source_fingerprint == FINGERPRINTS[anchor]
    np.testing.assert_allclose(lens.base_to_anchor, base_anchor)
    np.testing.assert_allclose(lens.quote_to_anchor, quote_anchor)


def test_common_reference_asset_is_an_explicit_unit_anchor() -> None:
    aligned = align_bar_series(
        (
            _series(ETH, (20.0, 40.0, 30.0)),
            _series(BTC, (5.0, 10.0, 6.0)),
        )
    )

    lens = build_anchor_lens(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        anchor=USDT,
        source_fingerprints=FINGERPRINTS,
        as_of=AS_OF,
    )

    assert lens.reduction is AnchorReduction.NONE
    assert lens.anchor_source_fingerprint is None
    np.testing.assert_allclose(lens.base_to_anchor, [20.0, 40.0, 30.0])
    np.testing.assert_allclose(lens.quote_to_anchor, [5.0, 10.0, 6.0])


def test_pair_leg_can_be_the_common_reference_identity_coordinate() -> None:
    aligned = align_bar_series(
        (
            _series(ETH, (20.0, 40.0, 30.0)),
            _series(BTC, (5.0, 10.0, 6.0)),
        )
    )

    lens = build_anchor_lens(
        aligned,
        orientation=PairOrientation(base=ETH, quote=USDT),
        anchor=USDT,
        source_fingerprints=FINGERPRINTS,
        as_of=AS_OF,
    )

    identity_fingerprint = identity_source_fingerprint(USDT)
    assert lens.reduction is AnchorReduction.ANCHOR_IS_QUOTE
    assert lens.base_source_fingerprint == FINGERPRINTS[ETH]
    assert lens.quote_source_fingerprint == identity_fingerprint
    assert lens.anchor_source_fingerprint == identity_fingerprint
    np.testing.assert_allclose(lens.pair_ratio, [20.0, 40.0, 30.0])
    np.testing.assert_allclose(lens.base_to_anchor, [20.0, 40.0, 30.0])
    np.testing.assert_allclose(lens.quote_to_anchor, [1.0, 1.0, 1.0])


def test_anchor_lens_rejects_mismatched_reference_coordinates() -> None:
    aligned = align_bar_series(
        (
            _series(ETH, (20.0, 40.0, 30.0), reference=USDT),
            _series(BTC, (5.0, 10.0, 6.0), reference=USDC),
        )
    )

    with pytest.raises(RelationshipDataError, match="common quote"):
        build_anchor_lens(
            aligned,
            orientation=PairOrientation(base=ETH, quote=BTC),
            anchor=USDT,
            source_fingerprints=FINGERPRINTS,
            as_of=AS_OF,
        )


def test_anchor_lens_requires_a_distinct_anchor_leg_or_common_reference() -> None:
    aligned = align_bar_series(
        (
            _series(ETH, (20.0, 40.0, 30.0)),
            _series(BTC, (5.0, 10.0, 6.0)),
        )
    )

    with pytest.raises(RelationshipDataError, match="exactly one leg"):
        build_anchor_lens(
            aligned,
            orientation=PairOrientation(base=ETH, quote=BTC),
            anchor=SOL,
            source_fingerprints=FINGERPRINTS,
            as_of=AS_OF,
        )


_positive_price_triples = st.lists(
    st.tuples(
        st.floats(
            min_value=1e-9,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
        ),
        st.floats(
            min_value=1e-9,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
        ),
        st.floats(
            min_value=1e-9,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
        ),
    ),
    min_size=1,
    max_size=12,
)


@given(price_triples=_positive_price_triples)
def test_anchor_identities_hold_for_positive_price_paths(
    price_triples: list[tuple[float, float, float]],
) -> None:
    base = tuple(point[0] for point in price_triples)
    quote = tuple(point[1] for point in price_triples)
    anchor = tuple(point[2] for point in price_triples)
    as_of = (
        datetime(2024, 1, 1, 10, tzinfo=UTC) + len(price_triples) * INTERVAL.duration
    )

    lens = build_anchor_lens(
        _aligned_three(base, quote, anchor),
        orientation=PairOrientation(base=ETH, quote=BTC),
        anchor=SOL,
        source_fingerprints=FINGERPRINTS,
        as_of=as_of,
    )
    np.testing.assert_allclose(
        np.array(lens.base_to_anchor) / np.array(lens.quote_to_anchor),
        lens.pair_ratio,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        np.array(lens.base_to_anchor_log) - np.array(lens.quote_to_anchor_log),
        lens.pair_log_ratio,
        rtol=1e-12,
        atol=1e-12,
    )
