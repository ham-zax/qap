"""Normalized price-path evidence for admitted aligned market data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from qap.market import AlignedBarSeries, BarInterval
from qap.portfolio import AssetId
from qap.relationship.observation import (
    RelationshipDataError,
    validated_as_of,
    validated_fingerprint,
    validated_timestamps,
)
from qap.relationship.ratio import (
    aligned_asset_values,
    frozen_array,
    identity_source_fingerprint,
    positive_vector,
)


class NormalizationScale(StrEnum):
    ONE = "one"
    HUNDRED = "hundred"

    @property
    def starting_value(self) -> float:
        if self is NormalizationScale.ONE:
            return 1.0
        return 100.0


@dataclass(frozen=True, slots=True)
class NormalizedPath:
    asset: AssetId
    interval: BarInterval
    timestamps: tuple[datetime, ...]
    as_of: datetime
    source_fingerprint: str
    scale: NormalizationScale
    values: NDArray[np.float64]

    def __post_init__(self) -> None:
        if not isinstance(self.scale, NormalizationScale):
            raise TypeError("scale must be NormalizationScale")
        object.__setattr__(self, "values", frozen_array(self.values))

    @property
    def descriptive_only(self) -> bool:
        return True


def _normalize(value: object, *, scale: float) -> NDArray[np.float64]:
    values = positive_vector(value, field="values")
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        normalized = np.divide(values, values[0]) * scale
    if not np.isfinite(normalized).all() or not np.greater(normalized, 0.0).all():
        raise RelationshipDataError(
            "normalized values must remain finite and strictly positive"
        )
    return frozen_array(normalized)


def normalize_to_one(value: object) -> NDArray[np.float64]:
    """Return an immutable path rebased to 1.0 at the first observation."""

    return _normalize(value, scale=1.0)


def normalize_to_hundred(value: object) -> NDArray[np.float64]:
    """Return an immutable path rebased to 100.0 at the first observation."""

    return _normalize(value, scale=100.0)


def build_normalized_path(
    aligned: AlignedBarSeries,
    *,
    asset: AssetId,
    scale: NormalizationScale,
    source_fingerprint: str,
    as_of: datetime,
) -> NormalizedPath:
    """Build descriptive normalized evidence from one admitted aligned asset path."""

    values, _reference, identity_coordinate = aligned_asset_values(aligned, asset)
    fingerprint = validated_fingerprint(
        source_fingerprint,
        field="source fingerprint",
    )
    if identity_coordinate and fingerprint != identity_source_fingerprint(asset):
        raise RelationshipDataError(
            f"identity source fingerprint for {asset.key} must match the "
            "deterministic unit coordinate"
        )
    timestamps = validated_timestamps(aligned.timestamps, interval=aligned.interval)
    validated_time = validated_as_of(as_of, timestamps=timestamps)
    if not isinstance(scale, NormalizationScale):
        raise TypeError("scale must be NormalizationScale")
    normalized = _normalize(values, scale=scale.starting_value)
    return NormalizedPath(
        asset=asset,
        interval=aligned.interval,
        timestamps=timestamps,
        as_of=validated_time,
        source_fingerprint=fingerprint,
        scale=scale,
        values=normalized,
    )
