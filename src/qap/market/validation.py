"""Fail-closed validation for executable market-bar series."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import cast

from qap.market.bars import BarInterval, MarketBar
from qap.market.instruments import VenueInstrument


class BarSeriesValidationError(ValueError):
    """Raised when ordered executable bar data violates its declared contract."""


def _validated_utc(timestamp: object, *, field: str) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError(f"{field} must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


def _copied_bars(bars: object) -> tuple[MarketBar, ...]:
    if not isinstance(bars, Iterable):
        raise TypeError("bars must be iterable")

    copied: list[MarketBar] = []
    for position, bar in enumerate(cast(Iterable[object], bars)):
        if not isinstance(bar, MarketBar):
            raise TypeError(f"bar at position {position} must be a MarketBar")
        copied.append(bar)
    return tuple(copied)


@dataclass(frozen=True, slots=True, init=False)
class CompletedBarHistory:
    """An immutable view containing only bars completed by one decision time."""

    instrument: VenueInstrument
    interval: BarInterval
    as_of: datetime
    bars: tuple[MarketBar, ...]

    def __init__(self) -> None:
        raise TypeError("obtain completed history from ValidatedBarSeries")

    @property
    def timestamps(self) -> tuple[datetime, ...]:
        """Return the candle-open index of the visible completed bars."""

        return tuple(bar.candle_open_time for bar in self.bars)


@dataclass(frozen=True, slots=True, init=False)
class ValidatedBarSeries:
    """One immutable contiguous instrument/interval series in source order."""

    instrument: VenueInstrument
    interval: BarInterval
    bars: tuple[MarketBar, ...]

    def __init__(self) -> None:
        raise TypeError("use validate_bar_series()")

    @property
    def timestamps(self) -> tuple[datetime, ...]:
        """Return the exact candle-open index."""

        return tuple(bar.candle_open_time for bar in self.bars)

    def history_through(self, decision_time: datetime) -> CompletedBarHistory:
        """Expose exactly bars whose internal completion boundary has passed."""

        as_of = _validated_utc(decision_time, field="decision time")
        visible = tuple(bar for bar in self.bars if bar.bar_end_exclusive <= as_of)
        return _completed_history(
            instrument=self.instrument,
            interval=self.interval,
            as_of=as_of,
            bars=visible,
        )

    def __len__(self) -> int:
        return len(self.bars)


def _completed_history(
    *,
    instrument: VenueInstrument,
    interval: BarInterval,
    as_of: datetime,
    bars: tuple[MarketBar, ...],
) -> CompletedBarHistory:
    history = object.__new__(CompletedBarHistory)
    object.__setattr__(history, "instrument", instrument)
    object.__setattr__(history, "interval", interval)
    object.__setattr__(history, "as_of", as_of)
    object.__setattr__(history, "bars", bars)
    return history


def _validated_series(bars: tuple[MarketBar, ...]) -> ValidatedBarSeries:
    series = object.__new__(ValidatedBarSeries)
    object.__setattr__(series, "instrument", bars[0].instrument)
    object.__setattr__(series, "interval", bars[0].interval)
    object.__setattr__(series, "bars", bars)
    return series


def validate_bar_series(bars: Iterable[MarketBar]) -> ValidatedBarSeries:
    """Validate source order, identity, and exact cadence without repairing data."""

    copied = _copied_bars(bars)
    if not copied:
        raise BarSeriesValidationError("bar series must contain at least one bar")

    instrument = copied[0].instrument
    interval = copied[0].interval
    previous = copied[0].candle_open_time

    for position, bar in enumerate(copied[1:], start=1):
        if bar.instrument != instrument:
            raise BarSeriesValidationError(
                f"bar at position {position} has a different instrument"
            )
        if bar.interval != interval:
            raise BarSeriesValidationError(
                f"bar at position {position} has a different interval"
            )

        current = bar.candle_open_time
        if current == previous:
            raise BarSeriesValidationError(
                f"duplicate bar timestamp {current.isoformat()}"
            )
        if current < previous:
            raise BarSeriesValidationError(
                f"bar timestamp out of order at {current.isoformat()}"
            )

        expected = previous + interval.duration
        if current != expected:
            raise BarSeriesValidationError(
                "bar series gap: "
                f"expected {expected.isoformat()}, got {current.isoformat()}"
            )
        previous = current

    return _validated_series(copied)
