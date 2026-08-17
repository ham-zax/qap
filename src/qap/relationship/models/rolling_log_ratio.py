"""Transparent rolling standardized deviation of completed log-ratio evidence."""

from datetime import datetime
from hashlib import sha256
from typing import cast

import numpy as np

from qap.relationship.observation import (
    EvidenceKind,
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    RelationshipObservation,
    RelationshipObservationStatus,
    RelationshipSeries,
    validated_utc,
)

_MODEL_ID = "rolling_log_ratio_zscore"
_MODEL_VERSION = "1"
_NUMERICAL_STD_MULTIPLIER = 64.0


def _validated_count(value: int, *, field: str) -> int:
    raw = cast(object, value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def _visible_points(
    series: RelationshipSeries,
    *,
    as_of: datetime,
) -> tuple[datetime, tuple[tuple[datetime, float], ...]]:
    validated_time = validated_utc(as_of, field="as_of")
    if validated_time > series.as_of:
        raise RelationshipDataError("as_of cannot exceed the input series as_of")
    visible = tuple(
        (timestamp, value)
        for timestamp, value in zip(series.timestamps, series.values, strict=True)
        if timestamp + series.interval.duration <= validated_time
    )
    return validated_time, visible


def _input_fingerprint(
    series: RelationshipSeries,
    points: tuple[tuple[datetime, float], ...],
) -> str:
    digest = sha256()
    for value in (
        "qap.relationship.rolling-log-ratio-input.v1",
        series.pair_id.first.key,
        series.pair_id.second.key,
        series.orientation.base.key,
        series.orientation.quote.key,
        series.interval.label,
        series.base_source_fingerprint,
        series.quote_source_fingerprint,
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    for timestamp, value in points:
        digest.update(timestamp.isoformat().encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.hex().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _observation(
    series: RelationshipSeries,
    *,
    as_of: datetime,
    window_bars: int,
    min_observations: int,
    points: tuple[tuple[datetime, float], ...],
    status: RelationshipObservationStatus,
    score: float | None,
) -> RelationshipObservation:
    values = {} if score is None else {"score": float(score)}
    return RelationshipObservation(
        pair_id=series.pair_id,
        orientation=series.orientation,
        as_of=as_of,
        model_id=_MODEL_ID,
        model_version=_MODEL_VERSION,
        fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
        evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
        status=status,
        window_observations=window_bars,
        required_observations=min_observations,
        coverage_observations=len(points),
        base_source_fingerprint=series.base_source_fingerprint,
        quote_source_fingerprint=series.quote_source_fingerprint,
        input_fingerprint=_input_fingerprint(series, points),
        values=values,
    )


def rolling_log_ratio_observation(
    series: RelationshipSeries,
    *,
    window_bars: int,
    min_observations: int,
    as_of: datetime,
) -> RelationshipObservation:
    """Return one causal rolling z-score from completed log-ratio observations."""

    if series.evidence_kind is not EvidenceKind.LOG_RATIO:
        raise ValueError("rolling log-ratio model requires log-ratio input")
    window = _validated_count(window_bars, field="window_bars")
    minimum = _validated_count(min_observations, field="min_observations")
    if window < 2:
        raise ValueError("window_bars must be at least 2")
    if minimum < 2 or minimum > window:
        raise ValueError("min_observations must be between 2 and window_bars")

    validated_time, visible = _visible_points(series, as_of=as_of)
    points = visible[-window:]
    if len(points) < minimum:
        return _observation(
            series,
            as_of=validated_time,
            window_bars=window,
            min_observations=minimum,
            points=points,
            status=RelationshipObservationStatus.INSUFFICIENT_HISTORY,
            score=None,
        )

    values = np.asarray([value for _timestamp, value in points], dtype=np.float64)
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values, ddof=0))
    scale = max(1.0, float(np.max(np.abs(values))))
    near_zero = np.finfo(np.float64).eps * _NUMERICAL_STD_MULTIPLIER * scale
    if standard_deviation <= near_zero:
        return _observation(
            series,
            as_of=validated_time,
            window_bars=window,
            min_observations=minimum,
            points=points,
            status=RelationshipObservationStatus.INSUFFICIENT_VARIANCE,
            score=None,
        )

    score = float((values[-1] - mean) / standard_deviation)
    if not np.isfinite(score):
        raise RelationshipDataError("rolling log-ratio score must remain finite")
    return _observation(
        series,
        as_of=validated_time,
        window_bars=window,
        min_observations=minimum,
        points=points,
        status=RelationshipObservationStatus.VALID,
        score=score,
    )
