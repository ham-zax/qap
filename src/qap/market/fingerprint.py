"""Canonical semantic fingerprints for admitted market-bar series."""

import hashlib
import struct
from collections import OrderedDict
from datetime import UTC, datetime
from threading import Lock

from qap.market.validation import ValidatedBarSeries

_SCHEMA_VERSION = "qap.market.bar-series.v1"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_ROW_SC_VOL = struct.Struct(">qBqddddBd")
_ROW_NO_SC_VOL = struct.Struct(">qBddddBd")
_ROW_SC_NO_VOL = struct.Struct(">qBqddddB")
_ROW_NO_SC_NO_VOL = struct.Struct(">qBddddB")
_FINGERPRINT_LOCK = Lock()
_FINGERPRINT_CACHE: OrderedDict[
    int, tuple[ValidatedBarSeries, object, object, object, str]
] = OrderedDict()


def _validated_series(value: object) -> ValidatedBarSeries:
    if not isinstance(value, ValidatedBarSeries):
        raise TypeError("fingerprint input must be a ValidatedBarSeries")
    return value


def _append_text(payload: bytearray, value: str) -> None:
    encoded = value.encode("utf-8")
    payload.extend(struct.pack(">I", len(encoded)))
    payload.extend(encoded)


def _timestamp_microseconds(timestamp: datetime) -> int:
    normalized = timestamp if timestamp.tzinfo is UTC else timestamp.astimezone(UTC)
    delta = normalized - _EPOCH
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _append_optional_timestamp(
    payload: bytearray,
    timestamp: datetime | None,
) -> None:
    if timestamp is None:
        payload.append(0)
        return
    payload.append(1)
    payload.extend(struct.pack(">q", _timestamp_microseconds(timestamp)))


def fingerprint_bar_series(series: ValidatedBarSeries) -> str:
    """Hash authoritative metadata and ordered values, never paths or repr output."""

    validated = _validated_series(series)
    key = id(validated)
    with _FINGERPRINT_LOCK:
        cached = _FINGERPRINT_CACHE.get(key)
        if (
            cached is not None
            and cached[0] is validated
            and cached[1] is validated.instrument
            and cached[2] is validated.interval
            and cached[3] is validated.bars
        ):
            _FINGERPRINT_CACHE.move_to_end(key)
            return cached[4]
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

    epoch = _EPOCH
    pack_sc_vol = _ROW_SC_VOL.pack
    pack_no_sc_vol = _ROW_NO_SC_VOL.pack
    pack_sc_no_vol = _ROW_SC_NO_VOL.pack
    pack_no_sc_no_vol = _ROW_NO_SC_NO_VOL.pack
    for bar in validated.bars:
        open_ts = bar.candle_open_time
        norm_open = open_ts if open_ts.tzinfo is UTC else open_ts.astimezone(UTC)
        d_open = norm_open - epoch
        open_us = (
            d_open.days * 86_400_000_000
            + d_open.seconds * 1_000_000
            + d_open.microseconds
        )
        o = 0.0 if bar.open == 0.0 else bar.open
        h = 0.0 if bar.high == 0.0 else bar.high
        low = 0.0 if bar.low == 0.0 else bar.low
        c = 0.0 if bar.close == 0.0 else bar.close
        sc = bar.source_close_time
        vol = bar.volume
        if sc is None:
            if vol is None:
                payload.extend(pack_no_sc_no_vol(open_us, 0, o, h, low, c, 0))
            else:
                v = 0.0 if vol == 0.0 else vol
                payload.extend(pack_no_sc_vol(open_us, 0, o, h, low, c, 1, v))
        else:
            norm_sc = sc if sc.tzinfo is UTC else sc.astimezone(UTC)
            d_sc = norm_sc - epoch
            sc_us = (
                d_sc.days * 86_400_000_000
                + d_sc.seconds * 1_000_000
                + d_sc.microseconds
            )
            if vol is None:
                payload.extend(pack_sc_no_vol(open_us, 1, sc_us, o, h, low, c, 0))
            else:
                v = 0.0 if vol == 0.0 else vol
                payload.extend(pack_sc_vol(open_us, 1, sc_us, o, h, low, c, 1, v))

    digest = hashlib.sha256(payload).hexdigest()
    with _FINGERPRINT_LOCK:
        _FINGERPRINT_CACHE[key] = (
            validated,
            validated.instrument,
            validated.interval,
            validated.bars,
            digest,
        )
        _FINGERPRINT_CACHE.move_to_end(key)
        while len(_FINGERPRINT_CACHE) > 32:
            _FINGERPRINT_CACHE.popitem(last=False)
    return digest
