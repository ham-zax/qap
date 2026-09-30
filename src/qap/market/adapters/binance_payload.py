"""Validation primitives shared by Binance public response parsers."""

import math
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import cast

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MAX_KLINE_LIMIT = 1000


class BinancePublicDataError(RuntimeError):
    """Raised for explicit public-source, response, or contract failures."""


def as_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise BinancePublicDataError(f"{field} must be a JSON object")
    return cast(Mapping[str, object], value)


def as_list(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise BinancePublicDataError(f"{field} must be a JSON array")
    return cast(list[object], value)


def as_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise BinancePublicDataError(f"{field} must be a non-empty string")
    return value


def as_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise BinancePublicDataError(f"{field} must be a boolean")
    return value


def as_milliseconds(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BinancePublicDataError(f"{field} must be a non-negative integer")
    return value


def as_non_negative_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BinancePublicDataError(f"{field} must be a non-negative integer")
    return value


def as_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise BinancePublicDataError(f"{field} must be an exact decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise BinancePublicDataError(
            f"{field} must be an exact decimal string"
        ) from exc
    if not parsed.is_finite() or parsed < 0:
        raise BinancePublicDataError(f"{field} must be finite and non-negative")
    return parsed


def positive_decimal(value: object, *, field: str) -> Decimal:
    parsed = as_decimal(value, field=field)
    if parsed <= 0:
        raise BinancePublicDataError(f"{field} must be positive")
    return parsed


def enabled_decimal(value: object, *, field: str) -> Decimal | None:
    parsed = as_decimal(value, field=field)
    return parsed if parsed > 0 else None


def filter(
    filters: list[object],
    *,
    filter_type: str,
    required: bool,
) -> Mapping[str, object] | None:
    matches: list[Mapping[str, object]] = []
    for raw_filter in filters:
        item = as_mapping(raw_filter, field="symbol filter")
        if item.get("filterType") == filter_type:
            matches.append(item)
    if len(matches) > 1 or (required and len(matches) != 1):
        raise BinancePublicDataError(
            f"exchangeInfo must contain exactly one {filter_type} filter"
        )
    return matches[0] if matches else None


def as_float(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise BinancePublicDataError(f"{field} must be numeric")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise BinancePublicDataError(f"{field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise BinancePublicDataError(f"{field} must be finite")
    return parsed


def validated_utc(timestamp: object, *, field: str) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError(f"{field} must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


def datetime_from_milliseconds(value: int) -> datetime:
    return _EPOCH + timedelta(milliseconds=value)


def milliseconds_from_datetime(value: datetime, *, field: str) -> int:
    timestamp = validated_utc(value, field=field)
    delta = timestamp - _EPOCH
    microseconds = (
        delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    )
    if microseconds % 1000 != 0:
        raise ValueError(f"{field} must be aligned to a whole millisecond")
    return microseconds // 1000


def normalized_symbol(value: object) -> str:
    symbol = as_string(value, field="venue symbol").strip().upper()
    if not symbol:
        raise BinancePublicDataError("venue symbol must not be empty")
    return symbol


def validate_limit(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("kline limit must be an integer")
    if not 1 <= value <= _MAX_KLINE_LIMIT:
        raise ValueError(f"kline limit must be between 1 and {_MAX_KLINE_LIMIT}")
    return value
