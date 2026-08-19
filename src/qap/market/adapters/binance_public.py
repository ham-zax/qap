"""Bounded unauthenticated Binance Spot public-market acquisition.

The adapter intentionally uses only the official market-data-only host and the
public ``GET /api/v3/exchangeInfo`` and ``GET /api/v3/klines`` contracts. Kline
rows preserve source open/close millisecond timestamps; QAP derives its own
exclusive completion boundary from the declared interval.
"""

import math
import os
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Self, cast

import httpx

from qap.market.bars import BarInterval, MarketBar
from qap.market.instruments import VenueInstrument
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import PublicBookSnapshot, public_book_snapshot_from_rows
from qap.market.validation import ValidatedBarSeries, validate_bar_series
from qap.portfolio import AssetId

_PUBLIC_BASE_URL = os.environ.get(
    "QAP_BINANCE_PUBLIC_BASE_URL",
    "https://data-api.binance.vision",
).rstrip("/")
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


def _as_non_negative_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BinancePublicDataError(f"{field} must be a non-negative integer")
    return value


def _as_decimal(value: object, *, field: str) -> Decimal:
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


def _positive_decimal(value: object, *, field: str) -> Decimal:
    parsed = _as_decimal(value, field=field)
    if parsed <= 0:
        raise BinancePublicDataError(f"{field} must be positive")
    return parsed


def _enabled_decimal(value: object, *, field: str) -> Decimal | None:
    parsed = _as_decimal(value, field=field)
    return parsed if parsed > 0 else None


def _filter(
    filters: list[object],
    *,
    filter_type: str,
    required: bool,
) -> Mapping[str, object] | None:
    matches: list[Mapping[str, object]] = []
    for raw_filter in filters:
        item = _as_mapping(raw_filter, field="symbol filter")
        if item.get("filterType") == filter_type:
            matches.append(item)
    if len(matches) > 1 or (required and len(matches) != 1):
        raise BinancePublicDataError(
            f"exchangeInfo must contain exactly one {filter_type} filter"
        )
    return matches[0] if matches else None


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
        venue_base_asset: str,
        venue_quote_asset: str,
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
            venue_base_asset=venue_base_asset,
            venue_quote_asset=venue_quote_asset,
        )

    def fetch_market_metadata(
        self,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
        venue_base_asset: str,
        venue_quote_asset: str,
        require_trading: bool = True,
    ) -> MarketMetadata:
        """Fetch normalized public Spot precision/filter metadata for one symbol."""

        symbol = _normalized_symbol(venue_symbol)
        payload = self._get_json(
            "/api/v3/exchangeInfo",
            params={"symbol": symbol},
        )
        return self.market_metadata_from_payload(
            payload,
            venue_symbol=symbol,
            base=base,
            quote=quote,
            venue_base_asset=venue_base_asset,
            venue_quote_asset=venue_quote_asset,
            require_trading=require_trading,
        )

    def fetch_l1_book(
        self,
        *,
        instrument: VenueInstrument,
        observed_at: datetime | None = None,
    ) -> PublicBookSnapshot:
        """Capture one public best-bid/ask observation with quantities."""

        if instrument.venue != "binance":
            raise ValueError("Binance adapter requires a binance VenueInstrument")
        payload = self._get_json(
            "/api/v3/ticker/bookTicker",
            params={"symbol": instrument.venue_symbol},
        )
        item = _as_mapping(payload, field="bookTicker response")
        if _normalized_symbol(item.get("symbol")) != instrument.venue_symbol.upper():
            raise BinancePublicDataError("bookTicker symbol does not match instrument")
        timestamp = (
            datetime.now(UTC)
            if observed_at is None
            else _validated_utc(observed_at, field="observed_at")
        )
        return public_book_snapshot_from_rows(
            instrument=instrument,
            observed_at=timestamp,
            source_id="binance:/api/v3/ticker/bookTicker",
            source_payload=payload,
            bids=[[item.get("bidPrice"), item.get("bidQty")]],
            asks=[[item.get("askPrice"), item.get("askQty")]],
        )

    def fetch_shallow_depth(
        self,
        *,
        instrument: VenueInstrument,
        limit: int,
        observed_at: datetime | None = None,
    ) -> PublicBookSnapshot:
        """Capture one bounded public depth snapshot."""

        if instrument.venue != "binance":
            raise ValueError("Binance adapter requires a binance VenueInstrument")
        if isinstance(limit, bool) or not 1 <= limit <= 5000:
            raise ValueError("depth limit must be an integer between 1 and 5000")
        payload = self._get_json(
            "/api/v3/depth",
            params={"symbol": instrument.venue_symbol, "limit": limit},
        )
        item = _as_mapping(payload, field="depth response")
        timestamp = (
            datetime.now(UTC)
            if observed_at is None
            else _validated_utc(observed_at, field="observed_at")
        )
        return public_book_snapshot_from_rows(
            instrument=instrument,
            observed_at=timestamp,
            source_id=f"binance:/api/v3/depth?limit={limit}",
            source_payload=payload,
            bids=_as_list(item.get("bids"), field="depth bids"),
            asks=_as_list(item.get("asks"), field="depth asks"),
        )

    @staticmethod
    def instrument_from_payload(
        payload: object,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
        venue_base_asset: str,
        venue_quote_asset: str,
        require_trading: bool = True,
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
        if require_trading:
            if _as_string(item.get("status"), field="symbol status") != "TRADING":
                raise BinancePublicDataError(f"{symbol} is not currently TRADING")
            if not _as_bool(
                item.get("isSpotTradingAllowed"),
                field="isSpotTradingAllowed",
            ):
                raise BinancePublicDataError(f"{symbol} does not allow Spot trading")

        expected_venue_base = _normalized_symbol(venue_base_asset)
        expected_venue_quote = _normalized_symbol(venue_quote_asset)
        venue_base = (
            _as_string(item.get("baseAsset"), field="baseAsset").strip().upper()
        )
        venue_quote = (
            _as_string(item.get("quoteAsset"), field="quoteAsset").strip().upper()
        )
        if venue_base != expected_venue_base or venue_quote != expected_venue_quote:
            raise BinancePublicDataError(
                "exchangeInfo orientation does not match the explicit venue mapping: "
                f"received {venue_base}/{venue_quote}, expected "
                f"{expected_venue_base}/{expected_venue_quote}"
            )

        return VenueInstrument(
            venue="binance",
            venue_symbol=symbol,
            base=base,
            quote=quote,
            valid_from=None,
            valid_to=None,
        )

    @staticmethod
    def market_metadata_from_payload(
        payload: object,
        *,
        venue_symbol: str,
        base: AssetId,
        quote: AssetId,
        venue_base_asset: str,
        venue_quote_asset: str,
        require_trading: bool = True,
    ) -> MarketMetadata:
        """Normalize the precision/notional filters required by paper execution."""

        instrument = BinancePublicAdapter.instrument_from_payload(
            payload,
            venue_symbol=venue_symbol,
            base=base,
            quote=quote,
            venue_base_asset=venue_base_asset,
            venue_quote_asset=venue_quote_asset,
            require_trading=require_trading,
        )
        document = _as_mapping(payload, field="exchangeInfo response")
        symbols = _as_list(document.get("symbols"), field="exchangeInfo symbols")
        symbol = _normalized_symbol(venue_symbol)
        matches: list[Mapping[str, object]] = []
        for raw_item in symbols:
            symbol_item = _as_mapping(raw_item, field="exchangeInfo symbol")
            if symbol_item.get("symbol") == symbol:
                matches.append(symbol_item)
        if len(matches) != 1:
            raise BinancePublicDataError(
                f"exchangeInfo must contain exactly one {symbol} symbol"
            )
        item = matches[0]
        filters = _as_list(item.get("filters"), field="symbol filters")
        status = _as_string(item.get("status"), field="symbol status")
        if not _as_bool(
            item.get("isSpotTradingAllowed"),
            field="isSpotTradingAllowed",
        ):
            status = f"{status}_SPOT_DISABLED"
        price_filter = _filter(filters, filter_type="PRICE_FILTER", required=True)
        lot_filter = _filter(filters, filter_type="LOT_SIZE", required=True)
        market_lot_filter = _filter(
            filters,
            filter_type="MARKET_LOT_SIZE",
            required=False,
        )
        assert price_filter is not None
        assert lot_filter is not None

        notional_filter = _filter(filters, filter_type="NOTIONAL", required=False)
        legacy_notional = _filter(
            filters,
            filter_type="MIN_NOTIONAL",
            required=False,
        )
        minimum_notional: Decimal | None = None
        maximum_notional: Decimal | None = None
        minimum_applies_to_market = False
        maximum_applies_to_market = False
        average_price_minutes = 0
        if notional_filter is not None:
            minimum_notional = _enabled_decimal(
                notional_filter.get("minNotional"),
                field="NOTIONAL minNotional",
            )
            maximum_notional = _enabled_decimal(
                notional_filter.get("maxNotional"),
                field="NOTIONAL maxNotional",
            )
            minimum_applies_to_market = _as_bool(
                notional_filter.get("applyMinToMarket"),
                field="NOTIONAL applyMinToMarket",
            )
            maximum_applies_to_market = _as_bool(
                notional_filter.get("applyMaxToMarket"),
                field="NOTIONAL applyMaxToMarket",
            )
            average_price_minutes = _as_non_negative_int(
                notional_filter.get("avgPriceMins"),
                field="NOTIONAL avgPriceMins",
            )
        elif legacy_notional is not None:
            minimum_notional = _enabled_decimal(
                legacy_notional.get("minNotional"),
                field="MIN_NOTIONAL minNotional",
            )
            minimum_applies_to_market = _as_bool(
                legacy_notional.get("applyToMarket"),
                field="MIN_NOTIONAL applyToMarket",
            )
            average_price_minutes = _as_non_negative_int(
                legacy_notional.get("avgPriceMins"),
                field="MIN_NOTIONAL avgPriceMins",
            )

        try:
            return MarketMetadata(
                instrument=instrument,
                status=status,
                price_tick=_positive_decimal(
                    price_filter.get("tickSize"),
                    field="PRICE_FILTER tickSize",
                ),
                minimum_price=_enabled_decimal(
                    price_filter.get("minPrice"),
                    field="PRICE_FILTER minPrice",
                ),
                maximum_price=_enabled_decimal(
                    price_filter.get("maxPrice"),
                    field="PRICE_FILTER maxPrice",
                ),
                quantity_step=_positive_decimal(
                    lot_filter.get("stepSize"),
                    field="LOT_SIZE stepSize",
                ),
                minimum_quantity=_enabled_decimal(
                    lot_filter.get("minQty"),
                    field="LOT_SIZE minQty",
                ),
                maximum_quantity=_enabled_decimal(
                    lot_filter.get("maxQty"),
                    field="LOT_SIZE maxQty",
                ),
                minimum_notional=minimum_notional,
                maximum_notional=maximum_notional,
                minimum_notional_applies_to_market=minimum_applies_to_market,
                maximum_notional_applies_to_market=maximum_applies_to_market,
                notional_average_price_minutes=average_price_minutes,
                market_quantity_step=(
                    None
                    if market_lot_filter is None
                    else _enabled_decimal(
                        market_lot_filter.get("stepSize"),
                        field="MARKET_LOT_SIZE stepSize",
                    )
                ),
                market_minimum_quantity=(
                    None
                    if market_lot_filter is None
                    else _enabled_decimal(
                        market_lot_filter.get("minQty"),
                        field="MARKET_LOT_SIZE minQty",
                    )
                ),
                market_maximum_quantity=(
                    None
                    if market_lot_filter is None
                    else _enabled_decimal(
                        market_lot_filter.get("maxQty"),
                        field="MARKET_LOT_SIZE maxQty",
                    )
                ),
            )
        except (TypeError, ValueError) as exc:
            raise BinancePublicDataError(
                f"exchangeInfo precision metadata is invalid: {exc}"
            ) from exc

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
