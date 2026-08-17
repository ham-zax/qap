"""Immutable descriptive relationship evidence with explicit provenance."""

import math
import string
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import cast

from qap.market import BarInterval
from qap.portfolio import AssetId, PairId, PairOrientation


class RelationshipDataError(ValueError):
    """Raised when relationship evidence cannot be built without fabrication."""


class EvidenceKind(StrEnum):
    """Transparent descriptive evidence kinds implemented in Phase 04."""

    RATIO = "ratio"
    LOG_RATIO = "log_ratio"


class FitReciprocity(StrEnum):
    """How a fitted joint object behaves when orientation reverses."""

    EXACT_TRANSFORM = "exact_transform"
    REFIT_REQUIRED = "refit_required"
    MODEL_SPECIFIC = "model_specific"


class EvidenceReciprocity(StrEnum):
    """How oriented evidence behaves when orientation reverses."""

    EXACT_TRANSFORM = "exact_transform"
    DIRECTIONAL_TRANSFORM = "directional_transform"
    MODEL_SPECIFIC = "model_specific"


class RelationshipObservationStatus(StrEnum):
    """Validity state for one fitted/model-derived relationship observation."""

    VALID = "valid"
    INSUFFICIENT_HISTORY = "insufficient_history"
    INSUFFICIENT_VARIANCE = "insufficient_variance"


def validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise RelationshipDataError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def validated_timestamps(
    values: object,
    *,
    interval: BarInterval,
) -> tuple[datetime, ...]:
    if not isinstance(values, Iterable):
        raise TypeError("timestamps must be iterable")
    timestamps = tuple(
        validated_utc(value, field=f"timestamp {position}")
        for position, value in enumerate(cast(Iterable[object], values))
    )
    if not timestamps:
        raise RelationshipDataError("relationship timestamps must be non-empty")
    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        if current != previous + interval.duration:
            raise RelationshipDataError(
                "relationship timestamps must be strictly increasing at the "
                "declared interval"
            )
    return timestamps


def validated_fingerprint(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise RelationshipDataError(f"{field} must be a SHA-256 hex fingerprint")
    return normalized


def validated_source_fingerprints(value: object) -> Mapping[AssetId, str]:
    if not isinstance(value, Mapping):
        raise TypeError("source_fingerprints must be a mapping")
    copied: dict[AssetId, str] = {}
    for key, fingerprint in cast(Mapping[object, object], value).items():
        if not isinstance(key, AssetId):
            raise TypeError("source fingerprint keys must be AssetId values")
        copied[key] = validated_fingerprint(
            fingerprint,
            field=f"source fingerprint for {key.key}",
        )
    return copied


def validated_finite_values(values: object) -> tuple[float, ...]:
    if not isinstance(values, Iterable):
        raise TypeError("relationship values must be iterable")
    copied: list[float] = []
    for position, value in enumerate(cast(Iterable[object], values)):
        if not isinstance(value, float):
            raise TypeError(f"relationship value {position} must be a float")
        if not math.isfinite(value):
            raise RelationshipDataError("relationship values must be finite")
        copied.append(value)
    if not copied:
        raise RelationshipDataError("relationship values must be non-empty")
    return tuple(copied)


@dataclass(frozen=True, slots=True)
class RelationshipObservation:
    """One typed model observation with causal coverage and provenance."""

    pair_id: PairId
    orientation: PairOrientation
    as_of: datetime
    model_id: str
    model_version: str
    fit_reciprocity: FitReciprocity
    evidence_reciprocity: EvidenceReciprocity
    status: RelationshipObservationStatus
    window_observations: int
    required_observations: int
    coverage_observations: int
    base_source_fingerprint: str
    quote_source_fingerprint: str
    input_fingerprint: str
    values: Mapping[str, float]

    def __post_init__(self) -> None:
        if self.pair_id != self.orientation.pair_id:
            raise RelationshipDataError(
                "canonical pair identity must match the requested orientation"
            )
        if (
            not isinstance(cast(object, self.model_id), str)
            or not self.model_id.strip()
        ):
            raise TypeError("model_id must be a non-empty string")
        if (
            not isinstance(cast(object, self.model_version), str)
            or not self.model_version.strip()
        ):
            raise TypeError("model_version must be a non-empty string")
        if not isinstance(cast(object, self.fit_reciprocity), FitReciprocity):
            raise TypeError("fit_reciprocity must be a FitReciprocity")
        if not isinstance(cast(object, self.evidence_reciprocity), EvidenceReciprocity):
            raise TypeError("evidence_reciprocity must be an EvidenceReciprocity")
        if not isinstance(cast(object, self.status), RelationshipObservationStatus):
            raise TypeError("status must be a RelationshipObservationStatus")
        for field, value in (
            ("window_observations", self.window_observations),
            ("required_observations", self.required_observations),
            ("coverage_observations", self.coverage_observations),
        ):
            if isinstance(cast(object, value), bool) or not isinstance(
                cast(object, value), int
            ):
                raise TypeError(f"{field} must be an integer")
        if self.window_observations <= 0:
            raise RelationshipDataError("window_observations must be positive")
        if not 0 < self.required_observations <= self.window_observations:
            raise RelationshipDataError(
                "required_observations must be within the declared window"
            )
        if not 0 <= self.coverage_observations <= self.window_observations:
            raise RelationshipDataError(
                "coverage_observations must be within the declared window"
            )
        if (
            self.status is RelationshipObservationStatus.VALID
            and self.coverage_observations < self.required_observations
        ):
            raise RelationshipDataError(
                "valid relationship observation coverage must meet "
                "required_observations"
            )
        if (
            self.status is RelationshipObservationStatus.INSUFFICIENT_HISTORY
            and self.coverage_observations >= self.required_observations
        ):
            raise RelationshipDataError(
                "insufficient_history coverage must be below required_observations"
            )
        if (
            self.status is RelationshipObservationStatus.INSUFFICIENT_VARIANCE
            and self.coverage_observations < self.required_observations
        ):
            raise RelationshipDataError(
                "insufficient_variance coverage must meet required_observations"
            )

        normalized_values: dict[str, float] = {}
        for key, value in self.values.items():
            if not isinstance(cast(object, key), str) or not key.strip():
                raise TypeError(
                    "relationship observation value names must be non-empty"
                )
            if not isinstance(value, float):
                raise TypeError("relationship observation values must be floats")
            if not math.isfinite(value):
                raise RelationshipDataError(
                    "relationship observation values must be finite"
                )
            normalized_values[key.strip()] = value
        if self.status is RelationshipObservationStatus.VALID and not normalized_values:
            raise RelationshipDataError("valid relationship observation needs values")
        if self.status is not RelationshipObservationStatus.VALID and normalized_values:
            raise RelationshipDataError(
                "invalid relationship observation cannot carry values"
            )

        object.__setattr__(self, "as_of", validated_utc(self.as_of, field="as_of"))
        object.__setattr__(self, "model_id", self.model_id.strip())
        object.__setattr__(self, "model_version", self.model_version.strip())
        object.__setattr__(
            self,
            "base_source_fingerprint",
            validated_fingerprint(
                self.base_source_fingerprint,
                field="base source fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "quote_source_fingerprint",
            validated_fingerprint(
                self.quote_source_fingerprint,
                field="quote source fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "input_fingerprint",
            validated_fingerprint(self.input_fingerprint, field="input fingerprint"),
        )
        object.__setattr__(self, "values", MappingProxyType(normalized_values))


@dataclass(frozen=True, slots=True, init=False)
class RelationshipSeries:
    """One immutable oriented evidence series plus its causal provenance."""

    pair_id: PairId
    orientation: PairOrientation
    interval: BarInterval
    timestamps: tuple[datetime, ...]
    window_start: datetime
    window_end_exclusive: datetime
    as_of: datetime
    base_source_fingerprint: str
    quote_source_fingerprint: str
    evidence_kind: EvidenceKind
    fit_reciprocity: FitReciprocity
    evidence_reciprocity: EvidenceReciprocity
    values: tuple[float, ...]
    descriptive_only: bool

    def __init__(self) -> None:
        raise TypeError("use RelationshipSeries.from_values()")

    @classmethod
    def from_values(
        cls,
        *,
        pair_id: PairId,
        orientation: PairOrientation,
        interval: BarInterval,
        timestamps: object,
        as_of: datetime,
        base_source_fingerprint: str,
        quote_source_fingerprint: str,
        evidence_kind: EvidenceKind,
        fit_reciprocity: FitReciprocity,
        evidence_reciprocity: EvidenceReciprocity,
        values: object,
    ) -> "RelationshipSeries":
        if not isinstance(cast(object, evidence_kind), EvidenceKind):
            raise TypeError("evidence_kind must be an EvidenceKind")
        if not isinstance(cast(object, fit_reciprocity), FitReciprocity):
            raise TypeError("fit_reciprocity must be a FitReciprocity")
        if not isinstance(
            cast(object, evidence_reciprocity),
            EvidenceReciprocity,
        ):
            raise TypeError("evidence_reciprocity must be an EvidenceReciprocity")
        if pair_id != orientation.pair_id:
            raise RelationshipDataError(
                "canonical pair identity must match the requested orientation"
            )
        copied_timestamps = validated_timestamps(timestamps, interval=interval)
        copied_values = validated_finite_values(values)
        if evidence_kind is EvidenceKind.RATIO and any(
            value <= 0.0 for value in copied_values
        ):
            raise RelationshipDataError(
                "ratio values must be finite and strictly positive"
            )
        if len(copied_values) != len(copied_timestamps):
            raise RelationshipDataError(
                "relationship timestamps and values must have the same length"
            )
        normalized_as_of = validated_utc(as_of, field="as_of")
        window_end_exclusive = copied_timestamps[-1] + interval.duration
        if normalized_as_of < window_end_exclusive:
            raise RelationshipDataError(
                "as_of must include the entire completed window"
            )
        if fit_reciprocity is not FitReciprocity.EXACT_TRANSFORM:
            raise RelationshipDataError(
                "raw and log ratio fit reciprocity must be exact_transform"
            )
        if evidence_reciprocity is not EvidenceReciprocity.EXACT_TRANSFORM:
            raise RelationshipDataError(
                "raw and log ratio evidence reciprocity must be exact_transform"
            )

        result = object.__new__(cls)
        object.__setattr__(result, "pair_id", pair_id)
        object.__setattr__(result, "orientation", orientation)
        object.__setattr__(result, "interval", interval)
        object.__setattr__(result, "timestamps", copied_timestamps)
        object.__setattr__(result, "window_start", copied_timestamps[0])
        object.__setattr__(result, "window_end_exclusive", window_end_exclusive)
        object.__setattr__(result, "as_of", normalized_as_of)
        object.__setattr__(
            result,
            "base_source_fingerprint",
            validated_fingerprint(
                base_source_fingerprint,
                field="base source fingerprint",
            ),
        )
        object.__setattr__(
            result,
            "quote_source_fingerprint",
            validated_fingerprint(
                quote_source_fingerprint,
                field="quote source fingerprint",
            ),
        )
        object.__setattr__(result, "evidence_kind", evidence_kind)
        object.__setattr__(result, "fit_reciprocity", fit_reciprocity)
        object.__setattr__(result, "evidence_reciprocity", evidence_reciprocity)
        object.__setattr__(result, "values", copied_values)
        object.__setattr__(result, "descriptive_only", True)
        return result
