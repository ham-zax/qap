"""Deterministic rolling OLS residual evidence for two common-reference legs."""

from collections.abc import Mapping
from datetime import datetime
from hashlib import sha256
from typing import cast

import numpy as np

from qap.market import AlignedBarSeries
from qap.portfolio import AssetId, PairOrientation
from qap.relationship.observation import (
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    RelationshipObservation,
    RelationshipObservationStatus,
    validated_source_fingerprints,
    validated_utc,
)
from qap.relationship.ratio import (
    aligned_asset_values,
    source_fingerprint_for_asset,
)

_MODEL_ID = "rolling_log_price_ols_residual_zscore"
_MODEL_VERSION = "1"
_NUMERICAL_STD_MULTIPLIER = 64.0


def _validated_count(value: int, *, field: str) -> int:
    raw = cast(object, value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def _input_fingerprint(
    *,
    aligned: AlignedBarSeries,
    orientation: PairOrientation,
    base_source_fingerprint: str,
    quote_source_fingerprint: str,
    timestamps: tuple[datetime, ...],
    numerator_values: np.ndarray,
    denominator_values: np.ndarray,
) -> str:
    digest = sha256()
    for value in (
        "qap.relationship.rolling-residual-input.v1",
        orientation.pair_id.first.key,
        orientation.pair_id.second.key,
        orientation.base.key,
        orientation.quote.key,
        aligned.interval.label,
        base_source_fingerprint,
        quote_source_fingerprint,
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    for timestamp, numerator, denominator in zip(
        timestamps,
        numerator_values,
        denominator_values,
        strict=True,
    ):
        digest.update(timestamp.isoformat().encode("utf-8"))
        digest.update(b"\0")
        digest.update(float(numerator).hex().encode("ascii"))
        digest.update(b"\0")
        digest.update(float(denominator).hex().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _observation(
    *,
    orientation: PairOrientation,
    as_of: datetime,
    window_bars: int,
    min_observations: int,
    coverage_observations: int,
    base_source_fingerprint: str,
    quote_source_fingerprint: str,
    input_fingerprint: str,
    status: RelationshipObservationStatus,
    values: Mapping[str, float],
) -> RelationshipObservation:
    return RelationshipObservation(
        pair_id=orientation.pair_id,
        orientation=orientation,
        as_of=as_of,
        model_id=_MODEL_ID,
        model_version=_MODEL_VERSION,
        fit_reciprocity=FitReciprocity.REFIT_REQUIRED,
        evidence_reciprocity=EvidenceReciprocity.MODEL_SPECIFIC,
        status=status,
        window_observations=window_bars,
        required_observations=min_observations,
        coverage_observations=coverage_observations,
        base_source_fingerprint=base_source_fingerprint,
        quote_source_fingerprint=quote_source_fingerprint,
        input_fingerprint=input_fingerprint,
        values=values,
    )


def rolling_residual_observation(
    aligned: AlignedBarSeries,
    *,
    orientation: PairOrientation,
    source_fingerprints: Mapping[AssetId, str],
    window_bars: int,
    min_observations: int,
    as_of: datetime,
) -> RelationshipObservation:
    """Fit oriented log-price OLS and standardize the latest completed residual."""

    if not isinstance(cast(object, aligned), AlignedBarSeries):
        raise TypeError("aligned must be an AlignedBarSeries")
    if not isinstance(cast(object, orientation), PairOrientation):
        raise TypeError("orientation must be a PairOrientation")
    window = _validated_count(window_bars, field="window_bars")
    minimum = _validated_count(min_observations, field="min_observations")
    if window < 3:
        raise ValueError("window_bars must be at least 3")
    if minimum < 3 or minimum > window:
        raise ValueError("min_observations must be between 3 and window_bars")

    validated_time = validated_utc(as_of, field="as_of")
    latest_completion = aligned.timestamps[-1] + aligned.interval.duration
    if validated_time > latest_completion:
        raise RelationshipDataError("as_of cannot exceed the aligned data window")

    numerator, numerator_reference, numerator_identity = aligned_asset_values(
        aligned,
        orientation.base,
    )
    denominator, denominator_reference, denominator_identity = aligned_asset_values(
        aligned,
        orientation.quote,
    )
    if numerator_reference != denominator_reference:
        raise RelationshipDataError(
            "oriented legs must share one common quote/reference coordinate"
        )

    fingerprints = validated_source_fingerprints(source_fingerprints)
    base_source_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.base,
        identity_coordinate=numerator_identity,
    )
    quote_source_fingerprint = source_fingerprint_for_asset(
        fingerprints,
        asset=orientation.quote,
        identity_coordinate=denominator_identity,
    )

    visible_count = sum(
        timestamp + aligned.interval.duration <= validated_time
        for timestamp in aligned.timestamps
    )
    selected_count = min(visible_count, window)
    start = visible_count - selected_count
    timestamps = aligned.timestamps[start:visible_count]
    numerator_window = np.asarray(numerator[start:visible_count], dtype=np.float64)
    denominator_window = np.asarray(denominator[start:visible_count], dtype=np.float64)
    fingerprint = _input_fingerprint(
        aligned=aligned,
        orientation=orientation,
        base_source_fingerprint=base_source_fingerprint,
        quote_source_fingerprint=quote_source_fingerprint,
        timestamps=timestamps,
        numerator_values=numerator_window,
        denominator_values=denominator_window,
    )

    if selected_count < minimum:
        return _observation(
            orientation=orientation,
            as_of=validated_time,
            window_bars=window,
            min_observations=minimum,
            coverage_observations=selected_count,
            base_source_fingerprint=base_source_fingerprint,
            quote_source_fingerprint=quote_source_fingerprint,
            input_fingerprint=fingerprint,
            status=RelationshipObservationStatus.INSUFFICIENT_HISTORY,
            values={},
        )

    y = np.log(numerator_window)
    x = np.log(denominator_window)
    design = np.column_stack((np.ones(selected_count, dtype=np.float64), x))
    if np.linalg.matrix_rank(design) < 2:
        return _observation(
            orientation=orientation,
            as_of=validated_time,
            window_bars=window,
            min_observations=minimum,
            coverage_observations=selected_count,
            base_source_fingerprint=base_source_fingerprint,
            quote_source_fingerprint=quote_source_fingerprint,
            input_fingerprint=fingerprint,
            status=RelationshipObservationStatus.INSUFFICIENT_VARIANCE,
            values={},
        )

    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    alpha = float(coefficients[0])
    beta = float(coefficients[1])
    residuals = y - design @ coefficients
    residual_std = float(np.std(residuals, ddof=0))
    scale = max(1.0, float(np.max(np.abs(y))))
    near_zero = np.finfo(np.float64).eps * _NUMERICAL_STD_MULTIPLIER * scale
    if residual_std <= near_zero:
        return _observation(
            orientation=orientation,
            as_of=validated_time,
            window_bars=window,
            min_observations=minimum,
            coverage_observations=selected_count,
            base_source_fingerprint=base_source_fingerprint,
            quote_source_fingerprint=quote_source_fingerprint,
            input_fingerprint=fingerprint,
            status=RelationshipObservationStatus.INSUFFICIENT_VARIANCE,
            values={},
        )

    score = float(residuals[-1] / residual_std)
    if not all(np.isfinite(value) for value in (alpha, beta, score)):
        raise RelationshipDataError("rolling residual fit must remain finite")
    return _observation(
        orientation=orientation,
        as_of=validated_time,
        window_bars=window,
        min_observations=minimum,
        coverage_observations=selected_count,
        base_source_fingerprint=base_source_fingerprint,
        quote_source_fingerprint=quote_source_fingerprint,
        input_fingerprint=fingerprint,
        status=RelationshipObservationStatus.VALID,
        values={"score": score, "alpha": alpha, "beta": beta},
    )


__all__ = ["rolling_residual_observation"]
