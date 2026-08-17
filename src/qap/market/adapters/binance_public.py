"""Bounded unauthenticated Binance Spot public-market acquisition.

The adapter intentionally uses only the official market-data-only host and the
public ``GET /api/v3/exchangeInfo`` and ``GET /api/v3/klines`` contracts. Kline
rows preserve source open/close millisecond timestamps; QAP derives its own
exclusive completion boundary from the declared interval.
"""

import math
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Self, cast

import httpx

from qap.market.bars import BarInterval, MarketBar
from qap.market.instruments import VenueInstrument
from qap.market.validation import ValidatedBarSeries, validate_bar_series
from qap.portfolio import AssetId

_PUBLIC_BASE_URL = "https://data-api.binance.vision"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MAX_KLINE_LIMIT = 1000


class BinancePublicDataError(RuntimeError):
    """Raised for explicit public-source, response, or contract failures."""


def _as_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise BinancePublicDataError(f"{field} must be a JSON object")
    return cast(Mapping[str, object], value)


def _as_list(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise BinancePublicDataError(f"{field} must be a JSON array")
    return cast(list[object], value)


def _as_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise BinancePublicDataError(f"{field} must be a non-empty string")
    return value


def _as_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise BinancePublicDataError(f"{field} must be a boolean")
    return value


def _as_milliseconds(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BinancePublicDataError(f"{field} must be a non-negative integer")
    return value


def _as_float(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise BinancePublicDataError(f"{field} must be numeric")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise BinancePublicDataError(f"{field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise BinancePublicDataError(f"{field} must be finite")
    return parsed


def _validated_utc(timestamp: object, *, field: str) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError(f"{field} must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return timestamp.astimezone(UTC)


def _datetime_from_milliseconds(value: int) -> datetime:
    return _EPOCH + timedelta(milliseconds=value)


def _milliseconds_from_datetime(value: datetime, *, field: str) -> int:
    timestamp = _validated_utc(value, field=field)
    delta = timestamp - _EPOCH
    microseconds = (
        delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    )
    if microseconds % 1000 != 0:
        raise ValueError(f"{field} must be aligned to a whole millisecond")
    return microseconds // 1000


def _normalized_symbol(value: object) -> str:
    symbol = _as_string(value, field="venue symbol").strip().upper()
    if not symbol:
        raise BinancePublicDataError("venue symbol must not be empty")
    return symbol


def _validated_limit(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("kline limit must be an integer")
    if not 1 <= value <= _MAX_KLINE_LIMIT:
        raise ValueError(f"kline limit must be between 1 and {_MAX_KLINE_LIMIT}")
    return value


class BinancePublicAdapter:
    """Synchronous public Spot metadata/kline client with no auth capability."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if client is not None and transport is not None:
            raise ValueError("provide either client or transport, not both")
        if client is None:
            self._client = httpx.Client(
                timeout=timeout_seconds,
                headers={"Accept": "application/json"},
                transport=transport,
            )
            self._owns_client = True
        else:
            self._client = client
            self._owns_client = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close only a client created by this adapter."""

        if self._owns_client:
            self._client.close()

    def _get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str | int],
    ) -> object:
        try:
            response = self._client.get(
                f"{_PUBLIC_BASE_URL}{path}",
                params=params,
            )
        except httpx.HTTPError as exc:
            raise BinancePublicDataError(
                f"Binance public request failed: {exc}"
            ) from exc

        if response.status_code == 429:
            raise BinancePublicDataError("Binance public request returned HTTP 429")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BinancePublicDataError(
                f"Binance public request returned HTTP {response.status_code}"
            ) from exc
        try:
            payload: object = response.json()
        except ValueError as exc:
            raise BinancePublicDataError(
                "Binance public response was not valid JSON"
            ) from exc
        return payload

    def fetch_instrument(
        self,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
    ) -> VenueInstrument:
        """Verify one current Spot symbol against an explicit QAP orientation."""

        symbol = _normalized_symbol(venue_symbol)
        payload = self._get_json(
            "/api/v3/exchangeInfo",
            params={"symbol": symbol},
        )
        return self.instrument_from_payload(
            payload,
            venue_symbol=symbol,
            base=base,
            quote=quote,
        )

    @staticmethod
    def instrument_from_payload(
        payload: object,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
    ) -> VenueInstrument:
        """Map recorded exchange-info JSON without guessing inverses or history."""

        symbol = _normalized_symbol(venue_symbol)
        document = _as_mapping(payload, field="exchangeInfo response")
        symbols = _as_list(document.get("symbols"), field="exchangeInfo symbols")
        matches: list[Mapping[str, object]] = []
        for raw_symbol in symbols:
            item = _as_mapping(raw_symbol, field="exchangeInfo symbol")
            if item.get("symbol") == symbol:
                matches.append(item)
        if len(matches) != 1:
            raise BinancePublicDataError(
                f"exchangeInfo must contain exactly one {symbol} symbol"
            )

        item = matches[0]
        if _as_string(item.get("status"), field="symbol status") != "TRADING":
            raise BinancePublicDataError(f"{symbol} is not currently TRADING")
        if not _as_bool(
            item.get("isSpotTradingAllowed"),
            field="isSpotTradingAllowed",
        ):
            raise BinancePublicDataError(f"{symbol} does not allow Spot trading")

        venue_base = _as_string(item.get("baseAsset"), field="baseAsset")
        venue_quote = _as_string(item.get("quoteAsset"), field="quoteAsset")
        if venue_base != base.key or venue_quote != quote.key:
            raise BinancePublicDataError(
                "exchangeInfo orientation does not match the explicit QAP mapping: "
                f"received {venue_base}/{venue_quote}, expected {base.key}/{quote.key}"
            )

        return VenueInstrument(
            venue="binance",
            venue_symbol=symbol,
            base=base,
            quote=quote,
            valid_from=None,
            valid_to=None,
        )

    def fetch_klines(
        self,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
        limit: int = _MAX_KLINE_LIMIT,
    ) -> ValidatedBarSeries:
        """Fetch one bounded public page and return a validated contiguous series."""

        if instrument.venue != "binance":
            raise ValueError("Binance adapter requires a binance VenueInstrument")
        start_utc = _validated_utc(start, field="start")
        end_utc = _validated_utc(end_exclusive, field="end_exclusive")
        if start_utc >= end_utc:
            raise ValueError("start must be before end_exclusive")
        if end_utc > datetime.now(UTC):
            raise ValueError(
                "end_exclusive must contain completed historical bars only"
            )
        validated_limit = _validated_limit(limit)

        start_millis = _milliseconds_from_datetime(start_utc, field="start")
        end_millis = _milliseconds_from_datetime(
            end_utc,
            field="end_exclusive",
        )
        payload = self._get_json(
            "/api/v3/klines",
            params={
                "symbol": instrument.venue_symbol,
                "interval": interval.label,
                "startTime": start_millis,
                "endTime": end_millis - 1,
                "limit": validated_limit,
            },
        )
        bars = self.klines_from_payload(
            payload,
            instrument=instrument,
            interval=interval,
            start=start_utc,
            end_exclusive=end_utc,
        )
        if (
            bars[0].candle_open_time != start_utc
            or bars[-1].bar_end_exclusive != end_utc
        ):
            if len(bars) == validated_limit and bars[-1].bar_end_exclusive < end_utc:
                raise BinancePublicDataError(
                    "requested kline window exceeds one bounded public page"
                )
            raise BinancePublicDataError(
                "Binance klines did not cover the exact requested window"
            )
        try:
            return validate_bar_series(bars)
        except ValueError as exc:
            raise BinancePublicDataError(
                f"Binance kline validation failed: {exc}"
            ) from exc

    @staticmethod
    def klines_from_payload(
        payload: object,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> tuple[MarketBar, ...]:
        """Parse the documented kline array fields into QAP-owned observations."""

        rows = _as_list(payload, field="klines response")
        if not rows:
            raise BinancePublicDataError("Binance returned no klines")

        bars: list[MarketBar] = []
        for position, raw_row in enumerate(rows):
            row = _as_list(raw_row, field=f"kline row {position}")
            if len(row) != 12:
                raise BinancePublicDataError(
                    f"kline row {position} must contain exactly twelve fields"
                )
            candle_open = _datetime_from_milliseconds(
                _as_milliseconds(row[0], field=f"kline row {position} open time")
            )
            if candle_open < start or candle_open >= end_exclusive:
                raise BinancePublicDataError(
                    f"kline row {position} falls outside the requested window"
                )
            try:
                bar = MarketBar(
                    instrument=instrument,
                    interval=interval,
                    candle_open_time=candle_open,
                    open=_as_float(row[1], field=f"kline row {position} open"),
                    high=_as_float(row[2], field=f"kline row {position} high"),
                    low=_as_float(row[3], field=f"kline row {position} low"),
                    close=_as_float(row[4], field=f"kline row {position} close"),
                    volume=_as_float(
                        row[5],
                        field=f"kline row {position} volume",
                    ),
                    source_close_time=_datetime_from_milliseconds(
                        _as_milliseconds(
                            row[6],
                            field=f"kline row {position} close time",
                        )
                    ),
                )
            except (TypeError, ValueError) as exc:
                raise BinancePublicDataError(
                    f"kline row {position} violates the market-bar contract: {exc}"
                ) from exc
            if bar.bar_end_exclusive > end_exclusive:
                raise BinancePublicDataError(
                    f"kline row {position} is not completed by end_exclusive"
                )
            bars.append(bar)
        return tuple(bars)
