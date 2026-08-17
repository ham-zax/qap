"""Causal scanner data slicing and exact evaluated-slice identity."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import cast

from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    fingerprint_bar_series,
)
from qap.market.instruments import VenueInstrument


class ScannerSliceError(ValueError):
    """Raised when a requested scanner slice cannot be defined deterministically."""


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ScannerSliceError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _timedelta_micros(value: timedelta) -> int:
    return value.days * 86_400_000_000 + value.seconds * 1_000_000 + value.microseconds


def _expected_completion_times(
    *,
    anchor: datetime,
    window_start: datetime,
    cutoff: datetime,
    interval: BarInterval,
) -> tuple[datetime, ...]:
    step = _timedelta_micros(interval.duration)
    start_delta = _timedelta_micros(window_start - anchor)
    end_delta = _timedelta_micros(cutoff - anchor)
    first_index = start_delta // step + 1
    last_index = end_delta // step
    if first_index > last_index:
        return ()
    return tuple(
        anchor + interval.duration * index
        for index in range(first_index, last_index + 1)
    )


def _longest_missing_run(
    expected: tuple[datetime, ...],
    observed: frozenset[datetime],
) -> int:
    longest = 0
    current = 0
    for timestamp in expected:
        if timestamp in observed:
            current = 0
        else:
            current += 1
            longest = max(longest, current)
    return longest


def _float_text(value: float | None) -> str:
    return "" if value is None else value.hex()


def selection_slice_fingerprint(
    *,
    instrument: VenueInstrument,
    interval: BarInterval,
    bars: tuple[MarketBar, ...],
) -> str:
    """Hash only the exact canonical rows visible to scanner computation."""

    digest = sha256()
    header = (
        "qap.scanner.selection-slice.v1",
        instrument.venue,
        instrument.venue_symbol,
        instrument.base.key,
        instrument.quote.key,
        interval.label,
    )
    for value in header:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    for bar in bars:
        values = (
            bar.candle_open_time.isoformat(),
            bar.bar_end_exclusive.isoformat(),
            bar.bar_end_exclusive.isoformat(),
            "" if bar.source_close_time is None else bar.source_close_time.isoformat(),
            bar.open.hex(),
            bar.high.hex(),
            bar.low.hex(),
            bar.close.hex(),
            _float_text(bar.volume),
        )
        for value in values:
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class EvaluatedSeries:
    dataset_id: str
    instrument: VenueInstrument
    interval: BarInterval
    source_artifact_fingerprint: str
    selection_slice_fingerprint: str
    window_start: datetime
    eligible_information_end: datetime
    bars: tuple[MarketBar, ...]
    expected_bar_count: int
    bar_coverage: float
    longest_missing_run: int


def evaluate_series(
    series: ValidatedBarSeries,
    *,
    dataset_id: str,
    eligible_information_end: datetime,
    lookback: timedelta,
) -> EvaluatedSeries:
    """Select completed trailing rows and derive source/slice identities separately."""

    if not isinstance(cast(object, series), ValidatedBarSeries):
        raise TypeError("series must be a ValidatedBarSeries")
    if not isinstance(cast(object, dataset_id), str) or not dataset_id.strip():
        raise ValueError("dataset_id must be a non-empty string")
    cutoff = _utc(eligible_information_end, field="eligible_information_end")
    if not isinstance(cast(object, lookback), timedelta):
        raise TypeError("lookback must be a timedelta")
    if lookback <= timedelta(0):
        raise ScannerSliceError("lookback must be positive")
    if lookback % series.interval.duration != timedelta(0):
        raise ScannerSliceError("lookback must divide exactly into interval bars")

    window_start = cutoff - lookback
    selected = tuple(
        bar for bar in series.bars if window_start < bar.bar_end_exclusive <= cutoff
    )
    expected = _expected_completion_times(
        anchor=series.bars[0].bar_end_exclusive,
        window_start=window_start,
        cutoff=cutoff,
        interval=series.interval,
    )
    expected_count = len(expected)
    if expected_count == 0:
        raise ScannerSliceError("lookback produced no expected interval bars")
    observed = frozenset(bar.bar_end_exclusive for bar in selected)
    covered = sum(timestamp in observed for timestamp in expected)

    return EvaluatedSeries(
        dataset_id=dataset_id.strip(),
        instrument=series.instrument,
        interval=series.interval,
        source_artifact_fingerprint=fingerprint_bar_series(series),
        selection_slice_fingerprint=selection_slice_fingerprint(
            instrument=series.instrument,
            interval=series.interval,
            bars=selected,
        ),
        window_start=window_start,
        eligible_information_end=cutoff,
        bars=selected,
        expected_bar_count=expected_count,
        bar_coverage=covered / expected_count,
        longest_missing_run=_longest_missing_run(expected, observed),
    )


__all__ = [
    "EvaluatedSeries",
    "ScannerSliceError",
    "evaluate_series",
    "selection_slice_fingerprint",
]
