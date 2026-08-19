"""Binance-specific historical Spot acquisition for Product market data."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import zipfile
from datetime import UTC, datetime, timedelta
from typing import Self

import httpx

from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    fingerprint_bar_series,
    validate_bar_series,
)
from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.product_market_data import (
    MarketDataGenerationInput,
    MarketDataGenerationProvenance,
    MarketDataUpstreamSource,
    ProductMarketData,
)
from qap.product_universe import ProductResearchScope, ResolvedProductInstrument

_ARCHIVE_BASE_URL = os.environ.get(
    "QAP_BINANCE_ARCHIVE_BASE_URL",
    "https://data.binance.vision",
).rstrip("/")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_DAY = timedelta(days=1)
_MAX_REST_PAGE_BARS = 1000
_NATIVE_PRODUCT_INTERVALS = frozenset({"15m", "1h", "4h", "1d"})
_ARCHIVE_IMPLEMENTATION = "qap.product.binance-daily-archive-klines.v1"
_REST_IMPLEMENTATION = "qap.product.binance-rest-klines-pages.v1"


class BinanceHistoricalAcquisitionError(RuntimeError):
    """Raised when Binance history cannot satisfy the requested Product window."""


class _ArchiveUnavailable(RuntimeError):
    """Raised only when an official daily archive object is not published."""


def _validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _window(
    *,
    interval: BarInterval,
    start: datetime,
    end_exclusive: datetime,
) -> tuple[datetime, datetime]:
    start_utc = _validated_utc(start, field="start")
    end_utc = _validated_utc(end_exclusive, field="end_exclusive")
    if start_utc >= end_utc:
        raise ValueError("start must be before end_exclusive")
    if end_utc > datetime.now(UTC):
        raise ValueError("end_exclusive must contain completed historical bars only")
    if (start_utc - _EPOCH) % interval.duration != timedelta(0):
        raise ValueError("start must align to the requested bar interval")
    if (end_utc - _EPOCH) % interval.duration != timedelta(0):
        raise ValueError("end_exclusive must align to the requested bar interval")
    return start_utc, end_utc


def _whole_utc_days(start: datetime, end_exclusive: datetime) -> bool:
    return (
        start.hour == 0
        and start.minute == 0
        and start.second == 0
        and start.microsecond == 0
        and end_exclusive.hour == 0
        and end_exclusive.minute == 0
        and end_exclusive.second == 0
        and end_exclusive.microsecond == 0
        and end_exclusive - start >= _DAY
    )


def _milliseconds(value: datetime) -> int:
    delta = value - _EPOCH
    microseconds = (
        delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    )
    if microseconds % 1000 != 0:
        raise ValueError("REST kline boundaries must align to a whole millisecond")
    return microseconds // 1000


def _archive_timestamp(value: str, *, field: str) -> datetime:
    try:
        raw = int(value)
    except ValueError as exc:
        raise BinanceHistoricalAcquisitionError(
            f"{field} must be an integer timestamp"
        ) from exc
    if raw < 0:
        raise BinanceHistoricalAcquisitionError(f"{field} must be non-negative")
    try:
        if raw >= 100_000_000_000_000:
            return _EPOCH + timedelta(microseconds=raw)
        return _EPOCH + timedelta(milliseconds=raw)
    except OverflowError as exc:
        raise BinanceHistoricalAcquisitionError(
            f"{field} is outside the supported timestamp range"
        ) from exc


def _number(value: str, *, field: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise BinanceHistoricalAcquisitionError(f"{field} must be numeric") from exc


def _exact_series(
    bars: list[MarketBar],
    *,
    start: datetime,
    end_exclusive: datetime,
    source: str,
) -> ValidatedBarSeries:
    if not bars:
        raise BinanceHistoricalAcquisitionError(f"{source} returned no bars")
    try:
        series = validate_bar_series(bars)
    except ValueError as exc:
        raise BinanceHistoricalAcquisitionError(
            f"{source} bars are not contiguous and valid: {exc}"
        ) from exc
    if (
        series.bars[0].candle_open_time != start
        or series.bars[-1].bar_end_exclusive != end_exclusive
    ):
        raise BinanceHistoricalAcquisitionError(
            f"{source} did not cover the exact requested window"
        )
    return series


def _checksum(text: str, *, file_name: str) -> str:
    parts = text.strip().split()
    if len(parts) != 2 or parts[1].lstrip("*") != file_name:
        raise BinanceHistoricalAcquisitionError(
            "Binance archive checksum file has an unexpected format"
        )
    expected = parts[0].lower()
    if len(expected) != 64 or any(
        character not in "0123456789abcdef" for character in expected
    ):
        raise BinanceHistoricalAcquisitionError(
            "Binance archive checksum is not a SHA-256 fingerprint"
        )
    return expected


class BinanceHistoricalAcquirer:
    """Acquire bounded Binance Spot history and emit the shared M3 generation input."""

    def __init__(
        self,
        *,
        rest_adapter: BinancePublicAdapter | None = None,
        archive_client: httpx.Client | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        if rest_adapter is None:
            self._rest_adapter = BinancePublicAdapter(timeout_seconds=timeout_seconds)
            self._owns_rest_adapter = True
        else:
            self._rest_adapter = rest_adapter
            self._owns_rest_adapter = False
        if archive_client is None:
            self._archive_client = httpx.Client(
                timeout=timeout_seconds,
                follow_redirects=True,
            )
            self._owns_archive_client = True
        else:
            self._archive_client = archive_client
            self._owns_archive_client = False

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
        if self._owns_rest_adapter:
            self._rest_adapter.close()
        if self._owns_archive_client:
            self._archive_client.close()

    @staticmethod
    def _archive_relative_path(
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
        day: datetime,
    ) -> str:
        symbol = instrument.instrument.venue_symbol
        date_label = day.date().isoformat()
        file_name = f"{symbol}-{interval.label}-{date_label}.zip"
        return f"data/spot/daily/klines/{symbol}/{interval.label}/{file_name}"

    def _archive_get(self, relative_path: str) -> bytes:
        url = f"{_ARCHIVE_BASE_URL}/{relative_path}"
        try:
            response = self._archive_client.get(url)
        except httpx.HTTPError as exc:
            raise BinanceHistoricalAcquisitionError(
                f"Binance archive request failed: {relative_path}"
            ) from exc
        if response.status_code == 404:
            raise _ArchiveUnavailable(relative_path)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BinanceHistoricalAcquisitionError(
                f"Binance archive request failed with HTTP {response.status_code}: "
                f"{relative_path}"
            ) from exc
        return response.content

    @staticmethod
    def _archive_rows(
        payload: bytes,
        *,
        file_name: str,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
        day_start: datetime,
    ) -> list[MarketBar]:
        csv_name = file_name.removesuffix(".zip") + ".csv"
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                members = tuple(
                    item for item in archive.infolist() if not item.is_dir()
                )
                if len(members) != 1 or members[0].filename != csv_name:
                    raise BinanceHistoricalAcquisitionError(
                        "Binance daily kline archive must contain exactly its "
                        "expected CSV"
                    )
                raw_csv = archive.read(members[0])
        except zipfile.BadZipFile as exc:
            raise BinanceHistoricalAcquisitionError(
                "Binance daily kline archive is not a valid ZIP file"
            ) from exc
        try:
            text = raw_csv.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BinanceHistoricalAcquisitionError(
                "Binance daily kline CSV is not UTF-8"
            ) from exc

        day_end = day_start + _DAY
        bars: list[MarketBar] = []
        for position, row in enumerate(csv.reader(io.StringIO(text))):
            if len(row) != 12:
                raise BinanceHistoricalAcquisitionError(
                    f"Binance daily kline row {position} must contain twelve fields"
                )
            candle_open = _archive_timestamp(
                row[0], field=f"archive row {position} open time"
            )
            source_close = _archive_timestamp(
                row[6], field=f"archive row {position} close time"
            )
            if not day_start <= candle_open < day_end:
                raise BinanceHistoricalAcquisitionError(
                    f"Binance daily kline row {position} falls outside its UTC day"
                )
            try:
                bars.append(
                    MarketBar(
                        instrument=instrument.instrument,
                        interval=interval,
                        candle_open_time=candle_open,
                        open=_number(row[1], field=f"archive row {position} open"),
                        high=_number(row[2], field=f"archive row {position} high"),
                        low=_number(row[3], field=f"archive row {position} low"),
                        close=_number(row[4], field=f"archive row {position} close"),
                        volume=_number(row[5], field=f"archive row {position} volume"),
                        source_close_time=source_close,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise BinanceHistoricalAcquisitionError(
                    f"Binance daily kline row {position} violates the QAP bar "
                    f"contract: {exc}"
                ) from exc
        return bars

    def _daily_archive(
        self,
        *,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> tuple[ValidatedBarSeries, tuple[MarketDataUpstreamSource, ...]]:
        bars: list[MarketBar] = []
        sources: list[MarketDataUpstreamSource] = []
        day = start
        while day < end_exclusive:
            relative_path = self._archive_relative_path(instrument, interval, day)
            file_name = relative_path.rsplit("/", 1)[-1]
            checksum_path = f"{relative_path}.CHECKSUM"
            checksum_payload = self._archive_get(checksum_path)
            archive_payload = self._archive_get(relative_path)
            try:
                checksum_text = checksum_payload.decode("ascii")
            except UnicodeDecodeError as exc:
                raise BinanceHistoricalAcquisitionError(
                    "Binance archive checksum file is not ASCII"
                ) from exc
            expected = _checksum(checksum_text, file_name=file_name)
            actual = hashlib.sha256(archive_payload).hexdigest()
            if actual != expected:
                raise BinanceHistoricalAcquisitionError(
                    f"Binance daily archive checksum mismatch: {relative_path}"
                )
            day_bars = self._archive_rows(
                archive_payload,
                file_name=file_name,
                instrument=instrument,
                interval=interval,
                day_start=day,
            )
            day_series = _exact_series(
                day_bars,
                start=day,
                end_exclusive=day + _DAY,
                source="Binance daily archive",
            )
            bars.extend(day_series.bars)
            sources.append(
                MarketDataUpstreamSource(
                    provider="binance",
                    source_family="official-public-data-daily-klines",
                    source_id=(
                        f"archive={relative_path};checksum={checksum_path};"
                        f"sha256={expected}"
                    ),
                    retrieved_at=datetime.now(UTC),
                    source_fingerprint=actual,
                )
            )
            day += _DAY
        return (
            _exact_series(
                bars,
                start=start,
                end_exclusive=end_exclusive,
                source="Binance daily archive",
            ),
            tuple(sources),
        )

    def _rest_pages(
        self,
        *,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> tuple[ValidatedBarSeries, tuple[MarketDataUpstreamSource, ...]]:
        bars: list[MarketBar] = []
        sources: list[MarketDataUpstreamSource] = []
        cursor = start
        while cursor < end_exclusive:
            page_end = min(
                end_exclusive,
                cursor + interval.duration * _MAX_REST_PAGE_BARS,
            )
            limit = (page_end - cursor) // interval.duration
            try:
                page = self._rest_adapter.fetch_klines(
                    instrument=instrument.instrument,
                    interval=interval,
                    start=cursor,
                    end_exclusive=page_end,
                    limit=limit,
                )
            except BinancePublicDataError as exc:
                raise BinanceHistoricalAcquisitionError(
                    "Binance REST klines could not cover one requested page"
                ) from exc
            start_millis = _milliseconds(cursor)
            end_millis = _milliseconds(page_end)
            sources.append(
                MarketDataUpstreamSource(
                    provider="binance",
                    source_family="official-public-rest-klines",
                    source_id=(
                        "binance:/api/v3/klines?"
                        f"symbol={instrument.instrument.venue_symbol}"
                        f"&interval={interval.label}"
                        f"&startTime={start_millis}"
                        f"&endTime={end_millis - 1}"
                        f"&limit={limit}"
                    ),
                    retrieved_at=datetime.now(UTC),
                    source_fingerprint=fingerprint_bar_series(page),
                )
            )
            bars.extend(page.bars)
            cursor = page_end
        return (
            _exact_series(
                bars,
                start=start,
                end_exclusive=end_exclusive,
                source="Binance REST",
            ),
            tuple(sources),
        )

    def acquire_generation_input(
        self,
        *,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> MarketDataGenerationInput:
        """Acquire one exact Binance window without publishing partial state."""

        if instrument not in scope.instruments:
            raise ValueError(
                "Binance acquisition requires an instrument in Product scope"
            )
        if instrument.instrument.venue != "binance":
            raise ValueError("Binance acquisition requires a binance instrument")
        if interval.label not in _NATIVE_PRODUCT_INTERVALS:
            raise ValueError(
                "Binance Product acquisition supports native 15m, 1h, 4h, and 1d bars"
            )
        normalized_dataset_id = dataset_id.strip()
        if not normalized_dataset_id:
            raise ValueError("dataset_id must not be empty")
        start_utc, end_utc = _window(
            interval=interval,
            start=start,
            end_exclusive=end_exclusive,
        )

        if _whole_utc_days(start_utc, end_utc):
            try:
                series, sources = self._daily_archive(
                    instrument=instrument,
                    interval=interval,
                    start=start_utc,
                    end_exclusive=end_utc,
                )
                implementation = _ARCHIVE_IMPLEMENTATION
            except _ArchiveUnavailable:
                series, sources = self._rest_pages(
                    instrument=instrument,
                    interval=interval,
                    start=start_utc,
                    end_exclusive=end_utc,
                )
                implementation = _REST_IMPLEMENTATION
        else:
            series, sources = self._rest_pages(
                instrument=instrument,
                interval=interval,
                start=start_utc,
                end_exclusive=end_utc,
            )
            implementation = _REST_IMPLEMENTATION

        return MarketDataGenerationInput(
            dataset_id=normalized_dataset_id,
            resolved_instrument=instrument,
            series=series,
            acquisition_implementation=implementation,
            upstream_sources=sources,
        )

    def acquire_and_publish(
        self,
        *,
        publisher: ProductMarketData,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
        published_at: datetime | None = None,
    ) -> MarketDataGenerationProvenance:
        """Acquire a complete Binance generation and publish through shared M3."""

        generation = self.acquire_generation_input(
            scope=scope,
            instrument=instrument,
            dataset_id=dataset_id,
            interval=interval,
            start=start,
            end_exclusive=end_exclusive,
        )
        return publisher.publish_generation(
            scope,
            generation,
            published_at=published_at,
        )


__all__ = [
    "BinanceHistoricalAcquirer",
    "BinanceHistoricalAcquisitionError",
]
