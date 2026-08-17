"""Vectorized raw and log-ratio evidence from admitted aligned closes."""

from collections.abc import Mapping
from datetime import datetime
from hashlib import sha256

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


def identity_source_fingerprint(asset: AssetId) -> str:
    """Fingerprint a deterministic unit coordinate, not a market dataset."""

    if not isinstance(asset, AssetId):
        raise TypeError("asset must be an AssetId")
    payload = f"qap.relationship.identity-coordinate.v1\0{asset.key}".encode()
    return sha256(payload).hexdigest()


def aligned_asset_values(
    aligned: AlignedBarSeries,
    asset: AssetId,
) -> tuple[NDArray[np.float64], AssetId, bool]:
    """Return one admitted asset path, its reference, and identity-path flag."""

    matches = tuple(item for item in aligned.series if item.instrument.base == asset)
    if len(matches) == 1:
        leg = matches[0]
        return (
            positive_vector(leg.closes, field=f"{asset.key} close"),
            leg.instrument.quote,
            False,
        )
    if len(matches) > 1:
        raise RelationshipDataError(
            f"aligned data must contain exactly one leg for {asset.key}"
        )

    references = {item.instrument.quote for item in aligned.series}
    if len(references) == 1 and asset in references:
        return (
            frozen_array(np.ones(len(aligned.timestamps), dtype=np.float64)),
            asset,
            True,
        )
    raise RelationshipDataError(
        f"aligned data must contain exactly one leg for {asset.key}"
    )


def source_fingerprint_for_asset(
    source_fingerprints: Mapping[AssetId, str],
    *,
    asset: AssetId,
    identity_coordinate: bool,
) -> str:
    """Resolve real-source provenance or the deterministic unit coordinate."""

    if identity_coordinate:
        expected = identity_source_fingerprint(asset)
        supplied = source_fingerprints.get(asset)
        if supplied is not None and supplied != expected:
            raise RelationshipDataError(
                f"identity source fingerprint for {asset.key} must match the "
                "deterministic unit coordinate"
            )
        return expected
    try:
        return source_fingerprints[asset]
    except KeyError as exc:
        raise RelationshipDataError(
            f"missing source fingerprint for {asset.key}"
        ) from exc


def _build_series(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    source_fingerprints: Mapping[AssetId, str],
    as_of: datetime,
    kind: EvidenceKind,
) -> RelationshipSeries:
    base_values, base_reference, base_identity = aligned_asset_values(
        aligned,
        orientation.base,
    )
    quote_values, quote_reference, quote_identity = aligned_asset_values(
        aligned,
        orientation.quote,
    )
    if base_reference != quote_reference:
        raise RelationshipDataError(
            "oriented legs must share one common quote/reference coordinate"
        )
    fingerprints = validated_source_fingerprints(source_fingerprints)
    base_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.base,
        identity_coordinate=base_identity,
    )
    quote_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.quote,
        identity_coordinate=quote_identity,
    )

    computation = raw_ratio if kind is EvidenceKind.RATIO else log_ratio
    values = computation(base_values, quote_values)
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
