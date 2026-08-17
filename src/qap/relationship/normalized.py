"""Pure descriptive price-path normalization over admitted aligned data."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from qap.market import AlignedBarSeries, BarInterval
from qap.portfolio import AssetId
from qap.relationship.observation import (
    RelationshipDataError,
    validated_fingerprint,
    validated_timestamps,
    validated_utc,
)
from qap.relationship.ratio import aligned_leg, frozen_array, positive_vector


class NormalizationScale(StrEnum):
    """Supported descriptive starting scales."""

    ONE = "one"
    HUNDRED = "hundred"

    @property
    def starting_value(self) -> float:
        return 1.0 if self is NormalizationScale.ONE else 100.0


def _normalize(values: object, *, scale: float) -> NDArray[np.float64]:
    array = positive_vector(values, field="normalization values")
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        normalized = np.divide(array, array[0]) * scale
    if not np.isfinite(normalized).all() or not np.greater(normalized, 0.0).all():
        raise RelationshipDataError(
            "normalized output must remain finite and strictly positive"
        )
    normalized[0] = scale
    return frozen_array(normalized)


def normalize_to_one(values: object) -> NDArray[np.float64]:
    """Normalize positive values to an exact initial value of 1.0."""

    return _normalize(values, scale=1.0)


def normalize_to_hundred(values: object) -> NDArray[np.float64]:
    """Normalize positive values to an exact initial value of 100.0."""

    return _normalize(values, scale=100.0)


@dataclass(frozen=True, slots=True, init=False)
class NormalizedPath:
    """One immutable visual-only normalized asset path with provenance."""

    asset: AssetId
    interval: BarInterval
    timestamps: tuple[datetime, ...]
    window_start: datetime
    window_end_exclusive: datetime
    as_of: datetime
    source_fingerprint: str
    scale: NormalizationScale
    values: tuple[float, ...]
    descriptive_only: bool

    def __init__(self) -> None:
        raise TypeError("use build_normalized_path()")


def build_normalized_path(
    aligned: AlignedBarSeries,
    *,
    asset: AssetId,
    scale: NormalizationScale,
    source_fingerprint: str,
    as_of: datetime,
) -> NormalizedPath:
    """Build one visual path on the admitted common timestamp index."""

    leg = aligned_leg(aligned, asset)
    timestamps = validated_timestamps(aligned.timestamps, interval=aligned.interval)
    normalized_as_of = validated_utc(as_of, field="as_of")
    window_end_exclusive = timestamps[-1] + aligned.interval.duration
    if normalized_as_of < window_end_exclusive:
        raise RelationshipDataError("as_of must include the entire completed window")
    normalized = _normalize(leg.closes, scale=scale.starting_value)

    result = object.__new__(NormalizedPath)
    object.__setattr__(result, "asset", asset)
    object.__setattr__(result, "interval", aligned.interval)
    object.__setattr__(result, "timestamps", timestamps)
    object.__setattr__(result, "window_start", timestamps[0])
    object.__setattr__(result, "window_end_exclusive", window_end_exclusive)
    object.__setattr__(result, "as_of", normalized_as_of)
    object.__setattr__(
        result,
        "source_fingerprint",
        validated_fingerprint(source_fingerprint, field="source fingerprint"),
    )
    object.__setattr__(result, "scale", scale)
    object.__setattr__(
        result,
        "values",
        tuple(float(value) for value in normalized),
    )
    object.__setattr__(result, "descriptive_only", True)
    return result
