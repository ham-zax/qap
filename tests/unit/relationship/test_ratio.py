from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from qap.market import (
    AlignedBarSeries,
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PairId, PairOrientation
from qap.relationship import (
    EvidenceKind,
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    RelationshipSeries,
    build_log_ratio_series,
    build_ratio_series,
    identity_source_fingerprint,
    log_ratio,
    raw_ratio,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")


def _instrument(base: AssetId) -> VenueInstrument:
    return VenueInstrument(
        venue="binance",
        venue_symbol=f"{base.key}USDT",
        base=base,
        quote=USDT,
    )


def _aligned() -> AlignedBarSeries:
    btc_instrument = _instrument(BTC)
    eth_instrument = _instrument(ETH)
    btc_closes = (100.0, 200.0, 300.0)
    eth_closes = (10.0, 20.0, 15.0)

    def series(
        instrument: VenueInstrument,
        closes: tuple[float, ...],
    ) -> ValidatedBarSeries:
        return validate_bar_series(
            [
                MarketBar(
                    instrument=instrument,
                    interval=INTERVAL,
                    candle_open_time=datetime(2024, 1, 1, 10 + index, tzinfo=UTC),
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=1.0,
                )
                for index, close in enumerate(closes)
            ]
        )

    return align_bar_series(
        [series(btc_instrument, btc_closes), series(eth_instrument, eth_closes)]
    )


def test_reciprocity_enums_are_explicit_and_closed() -> None:
    assert {member.value for member in FitReciprocity} == {
        "exact_transform",
        "refit_required",
        "model_specific",
    }
    assert {member.value for member in EvidenceReciprocity} == {
        "exact_transform",
        "directional_transform",
        "model_specific",
    }


def test_raw_and_log_ratio_obey_reciprocal_identities() -> None:
    x = np.array([2.0, 3.0, 5.0], dtype=np.float64)
    y = np.array([4.0, 6.0, 2.5], dtype=np.float64)

    xy = raw_ratio(x, y)
    yx = raw_ratio(y, x)
    log_xy = log_ratio(x, y)
    log_yx = log_ratio(y, x)

    np.testing.assert_allclose(xy * yx, np.ones(3), rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(log_yx, -log_xy, rtol=1e-12, atol=1e-12)
    assert xy.flags.writeable is False
    assert log_xy.flags.writeable is False


def test_seeded_positive_arrays_preserve_reciprocal_and_log_inverse_relations() -> None:
    generator = np.random.default_rng(20260817)
    x = generator.lognormal(mean=0.0, sigma=1.0, size=512)
    y = generator.lognormal(mean=0.0, sigma=1.0, size=512)

    np.testing.assert_allclose(
        raw_ratio(x, y) * raw_ratio(y, x),
        np.ones(512),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        log_ratio(x, y),
        -log_ratio(y, x),
        rtol=1e-12,
        atol=1e-12,
    )


_price_pairs = st.lists(
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
    ),
    min_size=1,
    max_size=64,
)


@given(price_pairs=_price_pairs)
def test_positive_price_paths_preserve_exact_orientation_laws(
    price_pairs: list[tuple[float, float]],
) -> None:
    x = np.array([pair[0] for pair in price_pairs], dtype=np.float64)
    y = np.array([pair[1] for pair in price_pairs], dtype=np.float64)

    np.testing.assert_allclose(
        raw_ratio(x, y) * raw_ratio(y, x),
        np.ones(len(price_pairs)),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        log_ratio(x, y),
        -log_ratio(y, x),
        rtol=1e-12,
        atol=1e-12,
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "message"),
    [
        ([], [], "non-empty"),
        ([1.0, 2.0], [1.0], "same shape"),
        ([1.0, 0.0], [1.0, 1.0], "strictly positive"),
        ([1.0, float("nan")], [1.0, 1.0], "finite"),
        ([1e308], [1e-308], "finite and strictly positive"),
        ([[1.0]], [[1.0]], "one-dimensional"),
    ],
)
def test_ratio_rejects_invalid_inputs(
    numerator: object,
    denominator: object,
    message: str,
) -> None:
    with pytest.raises(RelationshipDataError, match=message):
        raw_ratio(numerator, denominator)


def test_raw_ratio_rejects_finite_inputs_that_overflow_the_output() -> None:
    with pytest.raises(RelationshipDataError, match="finite"):
        raw_ratio([1e308], [1e-308])


def test_relationship_series_preserves_pair_orientation_and_provenance() -> None:
    aligned = _aligned()
    orientation = PairOrientation(base=ETH, quote=BTC)
    fingerprints = {BTC: "a" * 64, ETH: "b" * 64}
    as_of = datetime(2024, 1, 1, 13, tzinfo=UTC)

    ratio = build_ratio_series(
        aligned,
        orientation=orientation,
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    reverse = build_ratio_series(
        aligned,
        orientation=orientation.inverted(),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    logged = build_log_ratio_series(
        aligned,
        orientation=orientation,
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    reverse_logged = build_log_ratio_series(
        aligned,
        orientation=orientation.inverted(),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )

    assert ratio.pair_id == PairId(BTC, ETH)
    assert reverse.pair_id == ratio.pair_id
    assert ratio.orientation == orientation
    assert ratio.interval == INTERVAL
    assert ratio.timestamps == aligned.timestamps
    assert ratio.window_start == aligned.timestamps[0]
    assert ratio.window_end_exclusive == as_of
    assert ratio.as_of == as_of
    assert ratio.base_source_fingerprint == "b" * 64
    assert ratio.quote_source_fingerprint == "a" * 64
    assert reverse.base_source_fingerprint == "a" * 64
    assert reverse.quote_source_fingerprint == "b" * 64
    assert ratio.evidence_kind is EvidenceKind.RATIO
    assert logged.evidence_kind is EvidenceKind.LOG_RATIO
    assert ratio.fit_reciprocity is FitReciprocity.EXACT_TRANSFORM
    assert ratio.evidence_reciprocity is EvidenceReciprocity.EXACT_TRANSFORM
    assert ratio.descriptive_only is True
    np.testing.assert_allclose(np.array(ratio.values) * np.array(reverse.values), 1.0)
    np.testing.assert_allclose(
        np.array(logged.values),
        -np.array(reverse_logged.values),
    )

    with pytest.raises(FrozenInstanceError):
        ratio.as_of = datetime(2024, 1, 1, 14, tzinfo=UTC)  # type: ignore[misc]


def test_common_quote_is_a_deterministic_identity_coordinate() -> None:
    aligned = _aligned()
    fingerprints = {BTC: "a" * 64, ETH: "b" * 64}
    as_of = datetime(2024, 1, 1, 13, tzinfo=UTC)
    identity_fingerprint = identity_source_fingerprint(USDT)

    direct = build_ratio_series(
        aligned,
        orientation=PairOrientation(base=BTC, quote=USDT),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    reverse = build_ratio_series(
        aligned,
        orientation=PairOrientation(base=USDT, quote=BTC),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    direct_log = build_log_ratio_series(
        aligned,
        orientation=PairOrientation(base=BTC, quote=USDT),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )
    reverse_log = build_log_ratio_series(
        aligned,
        orientation=PairOrientation(base=USDT, quote=BTC),
        source_fingerprints=fingerprints,
        as_of=as_of,
    )

    assert direct.values == (100.0, 200.0, 300.0)
    assert direct.base_source_fingerprint == "a" * 64
    assert direct.quote_source_fingerprint == identity_fingerprint
    assert reverse.base_source_fingerprint == identity_fingerprint
    assert reverse.quote_source_fingerprint == "a" * 64
    np.testing.assert_allclose(
        np.array(direct.values) * np.array(reverse.values),
        np.ones(3),
    )
    np.testing.assert_allclose(
        np.array(direct_log.values),
        -np.array(reverse_log.values),
    )


def test_relationship_series_rejects_plain_strings_for_enum_metadata() -> None:
    orientation = PairOrientation(base=ETH, quote=BTC)
    timestamps = (
        datetime(2024, 1, 1, 10, tzinfo=UTC),
        datetime(2024, 1, 1, 11, tzinfo=UTC),
    )

    with pytest.raises(TypeError, match="evidence_kind"):
        RelationshipSeries.from_values(
            pair_id=orientation.pair_id,
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind="ratio",  # type: ignore[arg-type]
            fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
            evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
            values=(0.1, 0.2),
        )

    with pytest.raises(TypeError, match="fit_reciprocity"):
        RelationshipSeries.from_values(
            pair_id=orientation.pair_id,
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind=EvidenceKind.RATIO,
            fit_reciprocity="exact_transform",  # type: ignore[arg-type]
            evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
            values=(0.1, 0.2),
        )

    with pytest.raises(TypeError, match="evidence_reciprocity"):
        RelationshipSeries.from_values(
            pair_id=orientation.pair_id,
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind=EvidenceKind.RATIO,
            fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
            evidence_reciprocity="exact_transform",  # type: ignore[arg-type]
            values=(0.1, 0.2),
        )


def test_relationship_series_rejects_pair_or_time_metadata_mismatch() -> None:
    orientation = PairOrientation(base=ETH, quote=BTC)
    timestamps = (
        datetime(2024, 1, 1, 10, tzinfo=UTC),
        datetime(2024, 1, 1, 11, tzinfo=UTC),
    )

    with pytest.raises(RelationshipDataError, match="canonical pair"):
        RelationshipSeries.from_values(
            pair_id=PairId(BTC, USDT),
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind=EvidenceKind.RATIO,
            fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
            evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
            values=(0.1, 0.2),
        )

    with pytest.raises(RelationshipDataError, match="completed window"):
        RelationshipSeries.from_values(
            pair_id=orientation.pair_id,
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 11, 30, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind=EvidenceKind.RATIO,
            fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
            evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
            values=(0.1, 0.2),
        )

    with pytest.raises(RelationshipDataError, match="ratio values"):
        RelationshipSeries.from_values(
            pair_id=orientation.pair_id,
            orientation=orientation,
            interval=INTERVAL,
            timestamps=timestamps,
            as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
            base_source_fingerprint="b" * 64,
            quote_source_fingerprint="a" * 64,
            evidence_kind=EvidenceKind.RATIO,
            fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
            evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
            values=(0.1, -0.2),
        )
