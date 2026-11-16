"""Immutable completed-bar observations with explicit UTC timing semantics."""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from qap.market.instruments import VenueInstrument

_FIXED_INTERVALS: dict[str, timedelta] = {
    "1s": timedelta(seconds=1),
    "1m": timedelta(minutes=1),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
    "6h": timedelta(hours=6),
    "8h": timedelta(hours=8),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
    "3d": timedelta(days=3),
    "1w": timedelta(weeks=1),
}


def _validated_utc(timestamp: object, *, field: str) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError(f"{field} must be a datetime")
    if timestamp.tzinfo is UTC:
        return timestamp
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


def _validated_instrument(value: object) -> VenueInstrument:
    if type(value) is VenueInstrument:
        return value
    if not isinstance(value, VenueInstrument):
        raise TypeError("instrument must be a VenueInstrument")
    return value


def _validated_interval(value: object) -> "BarInterval":
    if type(value) is BarInterval:
        return value
    if not isinstance(value, BarInterval):
        raise TypeError("interval must be a BarInterval")
    return value


def _validated_price(value: object, *, field: str) -> float:
    if type(value) is not float and not isinstance(value, float):
        raise TypeError(f"{field} price must be a float")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field} price must be positive finite")
    return value


def _validated_volume(value: object) -> float | None:
    if value is None:
        return None
    if type(value) is not float and not isinstance(value, float):
        raise TypeError("volume must be a float when present")
    if not math.isfinite(value) or value < 0:
        raise ValueError("volume must be finite and non-negative")
    return value


def _normalized_interval_label(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("bar interval label must be a string")
    normalized = value.strip()
    if normalized not in _FIXED_INTERVALS:
        raise ValueError(f"unsupported fixed bar interval: {normalized!r}")
    return normalized


@dataclass(frozen=True, order=True, slots=True)
class BarInterval:
    """A fixed-duration market-bar interval with an explicit source label."""

    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _normalized_interval_label(self.label))

    @property
    def duration(self) -> timedelta:
        """Return the exact completion cadence for this interval."""

        return _FIXED_INTERVALS[self.label]


@dataclass(frozen=True, slots=True)
class MarketBar:
    """One completed-candle observation in an explicit venue orientation."""

    instrument: VenueInstrument
    interval: BarInterval
    candle_open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source_close_time: datetime | None = None

    def __post_init__(self) -> None:
        instrument = _validated_instrument(self.instrument)
        interval = _validated_interval(self.interval)
        candle_open_time = _validated_utc(
            self.candle_open_time,
            field="candle open time",
        )
        open_price = _validated_price(self.open, field="open")
        high = _validated_price(self.high, field="high")
        low = _validated_price(self.low, field="low")
        close = _validated_price(self.close, field="close")
        volume = _validated_volume(self.volume)

        if high < max(open_price, close, low):
            raise ValueError("high price contradicts OHLC values")
        if low > min(open_price, close, high):
            raise ValueError("low price contradicts OHLC values")

        source_close_time = self.source_close_time
        if source_close_time is not None:
            source_close_time = _validated_utc(
                source_close_time,
                field="source close time",
            )
            if not (
                candle_open_time
                <= source_close_time
                < candle_open_time + interval.duration
            ):
                raise ValueError("source close time must fall within the bar interval")

        object.__setattr__(self, "instrument", instrument)
        object.__setattr__(self, "interval", interval)
        object.__setattr__(self, "candle_open_time", candle_open_time)
        object.__setattr__(self, "open", open_price)
        object.__setattr__(self, "high", high)
        object.__setattr__(self, "low", low)
        object.__setattr__(self, "close", close)
        object.__setattr__(self, "volume", volume)
        object.__setattr__(self, "source_close_time", source_close_time)

    @property
    def bar_end_exclusive(self) -> datetime:
        """Return QAP's causal completion boundary, separate from source close time."""

        return self.candle_open_time + self.interval.duration
