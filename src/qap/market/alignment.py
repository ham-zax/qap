"""Exact timestamp alignment for validated executable market series."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from qap.market.bars import BarInterval, MarketBar
from qap.market.instruments import VenueInstrument
from qap.market.validation import ValidatedBarSeries


class BarAlignmentError(ValueError):
    """Raised when validated series cannot form one exact executable index."""


def _copied_series(series: object) -> tuple[ValidatedBarSeries, ...]:
    if not isinstance(series, Iterable):
        raise TypeError("series must be iterable")

    copied: list[ValidatedBarSeries] = []
    for position, item in enumerate(cast(Iterable[object], series)):
        if not isinstance(item, ValidatedBarSeries):
            raise TypeError(
                f"series at position {position} must be a ValidatedBarSeries"
            )
        copied.append(item)
    return tuple(copied)


@dataclass(frozen=True, slots=True, init=False)
class AlignedInstrumentSeries:
    """One instrument projected onto a shared exact timestamp intersection."""

    instrument: VenueInstrument
    interval: BarInterval
    bars: tuple[MarketBar, ...]
    source_length: int
    dropped_leading: int
    dropped_trailing: int
    dropped_leading_timestamps: tuple[datetime, ...]
    dropped_trailing_timestamps: tuple[datetime, ...]

    def __init__(self) -> None:
        raise TypeError("obtain aligned instruments from align_bar_series()")

    @property
    def opens(self) -> tuple[float, ...]:
        """Return immutable aligned open values."""

        return tuple(bar.open for bar in self.bars)

    @property
    def closes(self) -> tuple[float, ...]:
        """Return immutable aligned close values."""

        return tuple(bar.close for bar in self.bars)


@dataclass(frozen=True, slots=True, init=False)
class AlignedBarSeries:
    """One or more instruments sharing one exact immutable candle-open index."""

    interval: BarInterval
    timestamps: tuple[datetime, ...]
    series: tuple[AlignedInstrumentSeries, ...]

    def __init__(self) -> None:
        raise TypeError("use align_bar_series()")

    @property
    def instruments(self) -> tuple[VenueInstrument, ...]:
        """Return aligned instruments in caller-supplied order."""

        return tuple(item.instrument for item in self.series)

    def for_instrument(self, instrument: VenueInstrument) -> AlignedInstrumentSeries:
        """Return one aligned instrument without inferring aliases or inverses."""

        for item in self.series:
            if item.instrument == instrument:
                return item
        raise KeyError(instrument)


def _aligned_instrument(
    source: ValidatedBarSeries,
    timestamps: tuple[datetime, ...],
) -> AlignedInstrumentSeries:
    by_timestamp = {bar.candle_open_time: bar for bar in source.bars}
    try:
        selected = tuple(by_timestamp[timestamp] for timestamp in timestamps)
    except KeyError as exc:
        raise BarAlignmentError(
            f"internal alignment gap for {source.instrument.venue_symbol}"
        ) from exc

    first_index = source.timestamps.index(timestamps[0])
    last_index = source.timestamps.index(timestamps[-1])
    if last_index - first_index + 1 != len(selected):
        raise BarAlignmentError(
            f"internal alignment gap for {source.instrument.venue_symbol}"
        )

    aligned = object.__new__(AlignedInstrumentSeries)
    object.__setattr__(aligned, "instrument", source.instrument)
    object.__setattr__(aligned, "interval", source.interval)
    object.__setattr__(aligned, "bars", selected)
    dropped_leading_timestamps = source.timestamps[:first_index]
    dropped_trailing_timestamps = source.timestamps[last_index + 1 :]
    object.__setattr__(aligned, "source_length", len(source))
    object.__setattr__(aligned, "dropped_leading", len(dropped_leading_timestamps))
    object.__setattr__(aligned, "dropped_trailing", len(dropped_trailing_timestamps))
    object.__setattr__(
        aligned,
        "dropped_leading_timestamps",
        dropped_leading_timestamps,
    )
    object.__setattr__(
        aligned,
        "dropped_trailing_timestamps",
        dropped_trailing_timestamps,
    )
    return aligned


def _aligned_result(
    *,
    interval: BarInterval,
    timestamps: tuple[datetime, ...],
    series: tuple[AlignedInstrumentSeries, ...],
) -> AlignedBarSeries:
    aligned = object.__new__(AlignedBarSeries)
    object.__setattr__(aligned, "interval", interval)
    object.__setattr__(aligned, "timestamps", timestamps)
    object.__setattr__(aligned, "series", series)
    return aligned


def align_bar_series(
    series: Iterable[ValidatedBarSeries],
) -> AlignedBarSeries:
    """Align validated series by exact intersection without filling any price."""

    sources = _copied_series(series)
    if not sources:
        raise BarAlignmentError("alignment requires at least one series")

    instruments = [source.instrument for source in sources]
    if len(set(instruments)) != len(instruments):
        raise BarAlignmentError("alignment received a duplicate instrument")

    interval = sources[0].interval
    if any(source.interval != interval for source in sources[1:]):
        raise BarAlignmentError("all aligned series must use the same interval")

    common = set(sources[0].timestamps)
    for source in sources[1:]:
        common.intersection_update(source.timestamps)
    timestamps = tuple(sorted(common))
    if not timestamps:
        raise BarAlignmentError("aligned series have no common timestamps")

    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        expected = previous + interval.duration
        if current != expected:
            raise BarAlignmentError(
                "common timestamp intersection contains an internal gap: "
                f"expected {expected.isoformat()}, got {current.isoformat()}"
            )

    aligned_series = tuple(
        _aligned_instrument(source, timestamps) for source in sources
    )
    return _aligned_result(
        interval=interval,
        timestamps=timestamps,
        series=aligned_series,
    )
