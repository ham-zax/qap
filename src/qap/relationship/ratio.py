"""Vectorized raw and log-ratio evidence from admitted aligned closes."""

from collections.abc import Mapping
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from qap.market import AlignedBarSeries, AlignedInstrumentSeries
from qap.portfolio import AssetId, PairOrientation
from qap.relationship.observation import (
    EvidenceKind,
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    RelationshipSeries,
    validated_source_fingerprints,
)


def positive_vector(value: object, *, field: str) -> NDArray[np.float64]:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise RelationshipDataError(f"{field} must be numeric") from exc
    if array.ndim != 1:
        raise RelationshipDataError(f"{field} must be one-dimensional")
    if array.size == 0:
        raise RelationshipDataError(f"{field} must be non-empty")
    if not np.isfinite(array).all():
        raise RelationshipDataError(f"{field} must be finite")
    if not np.greater(array, 0.0).all():
        raise RelationshipDataError(f"{field} must be strictly positive")
    return np.array(array, dtype=np.float64, copy=True)


def frozen_array(array: NDArray[np.float64]) -> NDArray[np.float64]:
    result = np.array(array, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


def _aligned_positive_vectors(
    numerator: object,
    denominator: object,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    numerator_array = positive_vector(numerator, field="numerator")
    denominator_array = positive_vector(denominator, field="denominator")
    if numerator_array.shape != denominator_array.shape:
        raise RelationshipDataError(
            "numerator and denominator must have the same shape"
        )
    return numerator_array, denominator_array


def raw_ratio(numerator: object, denominator: object) -> NDArray[np.float64]:
    """Return an immutable elementwise X/Y ratio for positive aligned values."""

    numerator_array, denominator_array = _aligned_positive_vectors(
        numerator,
        denominator,
    )
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        result = np.divide(numerator_array, denominator_array)
    if not np.isfinite(result).all() or not np.greater(result, 0.0).all():
        raise RelationshipDataError(
            "ratio output must remain finite and strictly positive"
        )
    return frozen_array(result)


def log_ratio(numerator: object, denominator: object) -> NDArray[np.float64]:
    """Return immutable log(X)-log(Y) values for positive aligned inputs."""

    numerator_array, denominator_array = _aligned_positive_vectors(
        numerator,
        denominator,
    )
    result = np.log(numerator_array) - np.log(denominator_array)
    if not np.isfinite(result).all():
        raise RelationshipDataError("log-ratio output must remain finite")
    return frozen_array(result)


def aligned_leg(
    aligned: AlignedBarSeries,
    asset: AssetId,
) -> AlignedInstrumentSeries:
    matches = tuple(item for item in aligned.series if item.instrument.base == asset)
    if len(matches) != 1:
        raise RelationshipDataError(
            f"aligned data must contain exactly one leg for {asset.key}"
        )
    return matches[0]


def _build_series(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
    kind: EvidenceKind,
) -> RelationshipSeries:
    base_leg = aligned_leg(aligned, orientation.base)
    quote_leg = aligned_leg(aligned, orientation.quote)
    if base_leg.instrument.quote != quote_leg.instrument.quote:
        raise RelationshipDataError(
            "oriented legs must share one common quote/reference coordinate"
        )
    fingerprints = validated_source_fingerprints(source_fingerprints)
    try:
        base_fingerprint = fingerprints[orientation.base]
        quote_fingerprint = fingerprints[orientation.quote]
    except KeyError as exc:
        missing = exc.args[0]
        missing_key = missing.key if isinstance(missing, AssetId) else str(missing)
        raise RelationshipDataError(
            f"missing source fingerprint for {missing_key}"
        ) from exc

    computation = raw_ratio if kind is EvidenceKind.RATIO else log_ratio
    values = computation(base_leg.closes, quote_leg.closes)
    return RelationshipSeries.from_values(
        pair_id=orientation.pair_id,
        orientation=orientation,
        interval=aligned.interval,
        timestamps=aligned.timestamps,
        as_of=as_of,
        base_source_fingerprint=base_fingerprint,
        quote_source_fingerprint=quote_fingerprint,
        evidence_kind=kind,
        fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
        evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
        values=tuple(float(value) for value in values),
    )


def build_ratio_series(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
) -> RelationshipSeries:
    """Build descriptive X/Y evidence from admitted aligned close prices."""

    return _build_series(
        aligned,
        orientation=orientation,
        source_fingerprints=source_fingerprints,
        as_of=as_of,
        kind=EvidenceKind.RATIO,
    )


def build_log_ratio_series(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
) -> RelationshipSeries:
    """Build descriptive log(X)-log(Y) evidence from aligned closes."""

    return _build_series(
        aligned,
        orientation=orientation,
        source_fingerprints=source_fingerprints,
        as_of=as_of,
        kind=EvidenceKind.LOG_RATIO,
    )
