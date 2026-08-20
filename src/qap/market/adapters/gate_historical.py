"""Bounded unauthenticated Gate Spot historical candlestick acquisition."""

import csv
import gzip
import io
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Self, cast

import httpx

from qap.market.bars import BarInterval, MarketBar
from qap.market.instruments import VenueInstrument
from qap.market.microstructure import public_payload_fingerprint
from qap.market.validation import ValidatedBarSeries, validate_bar_series

_PUBLIC_BASE_URL = "https://api.gateio.ws/api/v4"
_ARCHIVE_BASE_URL = "https://download.gatedata.org"
_PRODUCT_CANDLE_INTERVALS = frozenset({"15m", "1h", "4h", "1d"})
_ARCHIVE_CANDLE_INTERVALS = frozenset({"1h", "4h", "1d"})
_MAX_CANDLE_POINTS = 1000


class GateHistoricalDataError(RuntimeError):
    """Raised when Gate historical data cannot satisfy an exact QAP window."""


@dataclass(frozen=True, slots=True)
class GateCandlestickSource:
    """One exact Gate upstream object/request used by an acquisition."""

    source_family: str
    source_id: str
    retrieved_at: datetime
    source_fingerprint: str


@dataclass(frozen=True, slots=True)
class GateCandlestickAcquisition:
    """Validated Gate bars plus exact upstream acquisition provenance."""

    series: ValidatedBarSeries
    sources: tuple[GateCandlestickSource, ...]


def _list(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise GateHistoricalDataError(f"{field} must be a JSON array")
    return cast(list[object], value)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateHistoricalDataError(f"{field} must be a non-empty string")
    return value.strip()


def _float_text(value: object, *, field: str, positive: bool) -> float:
    text = _text(value, field=field)
    try:
        parsed = float(text)
    except ValueError as exc:
        raise GateHistoricalDataError(
            f"{field} must be a finite decimal string"
        ) from exc
    if not math.isfinite(parsed) or parsed < 0 or (positive and parsed == 0):
        qualifier = "positive finite" if positive else "finite and non-negative"
        raise GateHistoricalDataError(f"{field} must be {qualifier}")
    return parsed


def _timestamp(value: object, *, field: str) -> datetime:
    text = _text(value, field=field)
    try:
        seconds = int(text)
    except ValueError as exc:
        raise GateHistoricalDataError(f"{field} must be Unix seconds") from exc
    if seconds < 0:
        raise GateHistoricalDataError(f"{field} must be non-negative Unix seconds")
    return datetime.fromtimestamp(seconds, UTC)


def _closed_flag(value: object, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise GateHistoricalDataError(f"{field} must be a boolean")


def _validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _unix_seconds(value: datetime, *, field: str) -> int:
    timestamp = _validated_utc(value, field=field)
    if timestamp.microsecond:
        raise ValueError(f"{field} must use whole-second precision")
    return int(timestamp.timestamp())


def _month_start(value: datetime) -> datetime:
    return datetime(value.year, value.month, 1, tzinfo=UTC)


def _next_month(value: datetime) -> datetime:
    if value.month == 12:
        return datetime(value.year + 1, 1, 1, tzinfo=UTC)
    return datetime(value.year, value.month + 1, 1, tzinfo=UTC)


def _validate_window(
    *,
    interval: BarInterval,
    start: datetime,
    end_exclusive: datetime,
    completed_by: datetime,
) -> tuple[datetime, datetime]:
    if interval.label not in _PRODUCT_CANDLE_INTERVALS:
        raise ValueError("Gate Product acquisition supports only 15m, 1h, 4h, and 1d")
    start_utc = _validated_utc(start, field="start")
    end_utc = _validated_utc(end_exclusive, field="end_exclusive")
    completed_utc = _validated_utc(completed_by, field="completed_by")
    if start_utc >= end_utc:
        raise ValueError("start must be before end_exclusive")
    if end_utc > completed_utc:
        raise ValueError("end_exclusive must contain completed historical bars only")
    start_seconds = _unix_seconds(start_utc, field="start")
    end_seconds = _unix_seconds(end_utc, field="end_exclusive")
    step_seconds = int(interval.duration.total_seconds())
    if start_seconds % step_seconds or end_seconds % step_seconds:
        raise ValueError("Gate candlestick window must align to interval boundaries")
    if (end_seconds - start_seconds) % step_seconds:
        raise ValueError("Gate candlestick window must contain whole interval bars")
    return start_utc, end_utc


def _validated_exact_series(
    bars: tuple[MarketBar, ...],
    *,
    start: datetime,
    end_exclusive: datetime,
    source: str,
) -> ValidatedBarSeries:
    try:
        series = validate_bar_series(bars)
    except (TypeError, ValueError) as exc:
        raise GateHistoricalDataError(
            f"{source} candlestick validation failed: {exc}"
        ) from exc
    if (
        series.bars[0].candle_open_time != start
        or series.bars[-1].bar_end_exclusive != end_exclusive
    ):
        raise GateHistoricalDataError(
            f"{source} candlesticks did not cover the exact requested window"
        )
    return series


class GateHistoricalAdapter:
    """Gate Spot historical REST/archive reader with no auth capability."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 20.0,
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
        if self._owns_client:
            self._client.close()

    def _get_json(self, path: str, *, params: dict[str, str | int]) -> object:
        try:
            response = self._client.get(f"{_PUBLIC_BASE_URL}{path}", params=params)
        except httpx.HTTPError as exc:
            raise GateHistoricalDataError(f"Gate REST request failed: {exc}") from exc
        if response.status_code == 429:
            raise GateHistoricalDataError("Gate REST request returned HTTP 429")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GateHistoricalDataError(
                f"Gate REST request returned HTTP {response.status_code}"
            ) from exc
        try:
            payload: object = response.json()
        except ValueError as exc:
            raise GateHistoricalDataError(
                "Gate REST response was not valid JSON"
            ) from exc
        return payload

    def _get_archive_bytes(self, url: str) -> tuple[bytes, datetime] | None:
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise GateHistoricalDataError(
                f"Gate archive request failed: {exc}"
            ) from exc
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            raise GateHistoricalDataError("Gate archive request returned HTTP 429")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GateHistoricalDataError(
                f"Gate archive request returned HTTP {response.status_code}"
            ) from exc
        return response.content, datetime.now(UTC)

    @staticmethod
    def candlesticks_from_payload(
        payload: object,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
        source: str,
    ) -> tuple[MarketBar, ...]:
        """Parse Gate REST/archive candlestick rows into QAP observations."""

        rows = _list(payload, field=f"{source} candlesticks")
        if not rows:
            raise GateHistoricalDataError(f"{source} returned no candlesticks")
        bars: list[MarketBar] = []
        for position, raw_row in enumerate(rows):
            row = _list(raw_row, field=f"{source} candlestick row {position}")
            if len(row) not in {6, 7, 8}:
                raise GateHistoricalDataError(
                    f"{source} candlestick row {position} must contain "
                    "6, 7, or 8 fields"
                )
            candle_open = _timestamp(
                row[0], field=f"{source} candlestick row {position} timestamp"
            )
            if candle_open < start or candle_open >= end_exclusive:
                raise GateHistoricalDataError(
                    f"{source} candlestick row {position} falls outside "
                    "the requested window"
                )
            if len(row) == 8 and not _closed_flag(
                row[7], field=f"{source} candlestick row {position} closed"
            ):
                raise GateHistoricalDataError(
                    f"{source} candlestick row {position} is not a completed candle"
                )
            try:
                bar = MarketBar(
                    instrument=instrument,
                    interval=interval,
                    candle_open_time=candle_open,
                    open=_float_text(
                        row[5],
                        field=f"{source} candlestick row {position} open",
                        positive=True,
                    ),
                    high=_float_text(
                        row[3],
                        field=f"{source} candlestick row {position} high",
                        positive=True,
                    ),
                    low=_float_text(
                        row[4],
                        field=f"{source} candlestick row {position} low",
                        positive=True,
                    ),
                    close=_float_text(
                        row[2],
                        field=f"{source} candlestick row {position} close",
                        positive=True,
                    ),
                    volume=_float_text(
                        row[1],
                        field=f"{source} candlestick row {position} quote volume",
                        positive=False,
                    ),
                )
            except (TypeError, ValueError) as exc:
                raise GateHistoricalDataError(
                    f"{source} candlestick row {position} violates the "
                    f"market-bar contract: {exc}"
                ) from exc
            if bar.bar_end_exclusive > end_exclusive:
                raise GateHistoricalDataError(
                    f"{source} candlestick row {position} is not completed "
                    "by end_exclusive"
                )
            bars.append(bar)
        return tuple(sorted(bars, key=lambda item: item.candle_open_time))

    def _fetch_rest_page(
        self,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> tuple[ValidatedBarSeries, GateCandlestickSource]:
        params: dict[str, str | int] = {
            "currency_pair": instrument.venue_symbol,
            "from": _unix_seconds(start, field="start"),
            "to": _unix_seconds(end_exclusive, field="end_exclusive") - 1,
            "interval": interval.label,
        }
        payload = self._get_json("/spot/candlesticks", params=params)
        retrieved_at = datetime.now(UTC)
        source_id = f"{_PUBLIC_BASE_URL}/spot/candlesticks?{httpx.QueryParams(params)}"
        bars = self.candlesticks_from_payload(
            payload,
            instrument=instrument,
            interval=interval,
            start=start,
            end_exclusive=end_exclusive,
            source="Gate REST",
        )
        series = _validated_exact_series(
            bars,
            start=start,
            end_exclusive=end_exclusive,
            source="Gate REST",
        )
        return series, GateCandlestickSource(
            source_family="spot-rest-candlesticks-v4",
            source_id=source_id,
            retrieved_at=retrieved_at,
            source_fingerprint=public_payload_fingerprint(payload),
        )

    def _fetch_archive_month(
        self,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> tuple[ValidatedBarSeries, GateCandlestickSource] | None:
        month = start.strftime("%Y%m")
        url = (
            f"{_ARCHIVE_BASE_URL}/spot/candlesticks_{interval.label}/"
            f"{month}/{instrument.venue_symbol}-{month}.csv.gz"
        )
        downloaded = self._get_archive_bytes(url)
        if downloaded is None:
            return None
        compressed, retrieved_at = downloaded
        try:
            text = gzip.decompress(compressed).decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise GateHistoricalDataError(
                "Gate candlestick archive is not valid gzip CSV"
            ) from exc
        rows = [row for row in csv.reader(io.StringIO(text)) if row]
        bars = self.candlesticks_from_payload(
            rows,
            instrument=instrument,
            interval=interval,
            start=start,
            end_exclusive=end_exclusive,
            source="Gate archive",
        )
        series = _validated_exact_series(
            bars,
            start=start,
            end_exclusive=end_exclusive,
            source="Gate archive",
        )
        return series, GateCandlestickSource(
            source_family="spot-historical-quotation-candlesticks-monthly",
            source_id=url,
            retrieved_at=retrieved_at,
            source_fingerprint=sha256(compressed).hexdigest(),
        )

    def fetch_candlesticks(
        self,
        *,
        instrument: VenueInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> GateCandlestickAcquisition:
        """Acquire one exact completed Gate window via archive/REST pages."""

        if instrument.venue != "gate":
            raise ValueError("Gate historical adapter requires a gate VenueInstrument")
        completed_by = datetime.now(UTC)
        start_utc, end_utc = _validate_window(
            interval=interval,
            start=start,
            end_exclusive=end_exclusive,
            completed_by=completed_by,
        )
        current_month = _month_start(completed_by)

        bars: list[MarketBar] = []
        sources: list[GateCandlestickSource] = []
        cursor = start_utc
        while cursor < end_utc:
            can_use_archive = (
                interval.label in _ARCHIVE_CANDLE_INTERVALS
                and cursor == _month_start(cursor)
            )
            if can_use_archive:
                month_end = _next_month(cursor)
                if month_end <= end_utc and month_end <= current_month:
                    try:
                        archived = self._fetch_archive_month(
                            instrument=instrument,
                            interval=interval,
                            start=cursor,
                            end_exclusive=month_end,
                        )
                    except GateHistoricalDataError:
                        archived = None
                    if archived is not None:
                        series, source = archived
                        bars.extend(series.bars)
                        sources.append(source)
                        cursor = month_end
                        continue

            segment_end = (
                min(end_utc, _next_month(cursor))
                if interval.label in _ARCHIVE_CANDLE_INTERVALS
                else end_utc
            )
            while cursor < segment_end:
                page_end = min(
                    segment_end,
                    cursor + interval.duration * _MAX_CANDLE_POINTS,
                )
                series, source = self._fetch_rest_page(
                    instrument=instrument,
                    interval=interval,
                    start=cursor,
                    end_exclusive=page_end,
                )
                bars.extend(series.bars)
                sources.append(source)
                cursor = page_end

        series = _validated_exact_series(
            tuple(bars),
            start=start_utc,
            end_exclusive=end_utc,
            source="Gate historical acquisition",
        )
        return GateCandlestickAcquisition(series=series, sources=tuple(sources))


__all__ = [
    "GateCandlestickAcquisition",
    "GateCandlestickSource",
    "GateHistoricalAdapter",
    "GateHistoricalDataError",
]
