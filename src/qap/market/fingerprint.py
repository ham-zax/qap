"""Canonical semantic fingerprints for admitted market-bar series."""

import hashlib
import struct
from datetime import UTC, datetime

from qap.market.validation import ValidatedBarSeries

_SCHEMA_VERSION = "qap.market.bar-series.v1"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _validated_series(value: object) -> ValidatedBarSeries:
    if not isinstance(value, ValidatedBarSeries):
        raise TypeError("fingerprint input must be a ValidatedBarSeries")
    return value


def _append_text(payload: bytearray, value: str) -> None:
    encoded = value.encode("utf-8")
    payload.extend(struct.pack(">I", len(encoded)))
    payload.extend(encoded)


def _timestamp_microseconds(timestamp: datetime) -> int:
    normalized = timestamp.astimezone(UTC)
    delta = normalized - _EPOCH
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _append_timestamp(payload: bytearray, timestamp: datetime) -> None:
    payload.extend(struct.pack(">q", _timestamp_microseconds(timestamp)))


def _append_optional_timestamp(
    payload: bytearray,
    timestamp: datetime | None,
) -> None:
    if timestamp is None:
        payload.append(0)
        return
    payload.append(1)
    _append_timestamp(payload, timestamp)


def _append_float(payload: bytearray, value: float) -> None:
    canonical = 0.0 if value == 0.0 else value
    payload.extend(struct.pack(">d", canonical))


def _append_optional_float(payload: bytearray, value: float | None) -> None:
    if value is None:
        payload.append(0)
        return
    payload.append(1)
    _append_float(payload, value)


def fingerprint_bar_series(series: ValidatedBarSeries) -> str:
    """Hash authoritative metadata and ordered values, never paths or repr output."""

    validated = _validated_series(series)
    instrument = validated.instrument
    payload = bytearray(b"QAP-BAR-SERIES\x00")

    for text in (
        _SCHEMA_VERSION,
        instrument.venue,
        instrument.venue_symbol,
        instrument.base.key,
        instrument.quote.key,
        validated.interval.label,
    ):
        _append_text(payload, text)

    _append_optional_timestamp(payload, instrument.valid_from)
    _append_optional_timestamp(payload, instrument.valid_to)
    payload.extend(struct.pack(">Q", len(validated.bars)))

    for bar in validated.bars:
        _append_timestamp(payload, bar.candle_open_time)
        _append_optional_timestamp(payload, bar.source_close_time)
        _append_float(payload, bar.open)
        _append_float(payload, bar.high)
        _append_float(payload, bar.low)
        _append_float(payload, bar.close)
        _append_optional_float(payload, bar.volume)

    return hashlib.sha256(payload).hexdigest()
