# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""CSV fixture admission and immutable local Parquet storage."""

import csv
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

import pyarrow as pa
import pyarrow.parquet as pq

from qap.market.bars import BarInterval, MarketBar
from qap.market.fingerprint import fingerprint_bar_series
from qap.market.instruments import VenueInstrument
from qap.market.validation import ValidatedBarSeries, validate_bar_series
from qap.portfolio import AssetId

_STORAGE_SCHEMA_VERSION = "qap.market.parquet.v1"
_STORAGE_EVIDENCE_ROLE = "role_neutral_market_data"
_LEGACY_EVIDENCE_ROLES = frozenset({"development"})
_UNIVERSE_MODE = "declared_fixed_basket"
_CSV_COLUMNS = (
    "candle_open_time",
    "source_close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class MarketDataStorageError(ValueError):
    """Raised when local market data cannot satisfy the admission contract."""


def _required_value(
    row: Mapping[str, str | None],
    field: str,
    *,
    row_number: int,
) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        raise MarketDataStorageError(
            f"CSV row {row_number} is missing required field {field}"
        )
    return value.strip()


def _optional_value(row: Mapping[str, str | None], field: str) -> str | None:
    value = row.get(field)
    if value is None or not value.strip():
        return None
    return value.strip()


def _parse_datetime(value: str, *, field: str, row_number: int) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MarketDataStorageError(
            f"CSV row {row_number} has invalid {field}: {value!r}"
        ) from exc


def _parse_float(value: str, *, field: str, row_number: int) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise MarketDataStorageError(
            f"CSV row {row_number} has invalid {field}: {value!r}"
        ) from exc


def load_csv_bar_series(
    path: str | Path,
    *,
    instrument: VenueInstrument,
    interval: BarInterval,
) -> ValidatedBarSeries:
    """Load the fixed fixture schema and validate it without sorting or repair."""

    source_path = Path(path)
    bars: list[MarketBar] = []
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != _CSV_COLUMNS:
            raise MarketDataStorageError(
                "CSV columns must be exactly " + ",".join(_CSV_COLUMNS)
            )

        for row_number, raw_row in enumerate(reader, start=2):
            row = cast(Mapping[str, str | None], raw_row)
            source_close_text = _optional_value(row, "source_close_time")
            volume_text = _optional_value(row, "volume")
            try:
                bars.append(
                    MarketBar(
                        instrument=instrument,
                        interval=interval,
                        candle_open_time=_parse_datetime(
                            _required_value(
                                row,
                                "candle_open_time",
                                row_number=row_number,
                            ),
                            field="candle_open_time",
                            row_number=row_number,
                        ),
                        source_close_time=(
                            _parse_datetime(
                                source_close_text,
                                field="source_close_time",
                                row_number=row_number,
                            )
                            if source_close_text is not None
                            else None
                        ),
                        open=_parse_float(
                            _required_value(row, "open", row_number=row_number),
                            field="open",
                            row_number=row_number,
                        ),
                        high=_parse_float(
                            _required_value(row, "high", row_number=row_number),
                            field="high",
                            row_number=row_number,
                        ),
                        low=_parse_float(
                            _required_value(row, "low", row_number=row_number),
                            field="low",
                            row_number=row_number,
                        ),
                        close=_parse_float(
                            _required_value(row, "close", row_number=row_number),
                            field="close",
                            row_number=row_number,
                        ),
                        volume=(
                            _parse_float(
                                volume_text,
                                field="volume",
                                row_number=row_number,
                            )
                            if volume_text is not None
                            else None
                        ),
                    )
                )
            except (TypeError, ValueError) as exc:
                if isinstance(exc, MarketDataStorageError):
                    raise
                raise MarketDataStorageError(
                    f"CSV row {row_number} violates the market-bar contract: {exc}"
                ) from exc

    try:
        return validate_bar_series(bars)
    except ValueError as exc:
        raise MarketDataStorageError(f"CSV series validation failed: {exc}") from exc


def _encoded_datetime(value: datetime | None) -> bytes:
    return b"" if value is None else value.isoformat().encode("utf-8")


def _parquet_metadata(
    series: ValidatedBarSeries,
    fingerprint: str,
) -> dict[bytes, bytes]:
    instrument = series.instrument
    return {
        b"qap_schema_version": _STORAGE_SCHEMA_VERSION.encode("utf-8"),
        b"qap_fingerprint": fingerprint.encode("ascii"),
        b"qap_evidence_role": _STORAGE_EVIDENCE_ROLE.encode("ascii"),
        b"qap_universe_mode": _UNIVERSE_MODE.encode("ascii"),
        b"venue": instrument.venue.encode("utf-8"),
        b"venue_symbol": instrument.venue_symbol.encode("utf-8"),
        b"base_asset": instrument.base.key.encode("utf-8"),
        b"quote_asset": instrument.quote.key.encode("utf-8"),
        b"interval": series.interval.label.encode("ascii"),
        b"valid_from": _encoded_datetime(instrument.valid_from),
        b"valid_to": _encoded_datetime(instrument.valid_to),
    }


def write_parquet_bar_series(
    path: str | Path,
    series: ValidatedBarSeries,
) -> str:
    """Write one validated series and return its path-independent fingerprint."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = fingerprint_bar_series(series)
    schema = pa.schema(
        [
            pa.field("candle_open_time", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("source_close_time", pa.timestamp("us", tz="UTC")),
            pa.field("open", pa.float64(), nullable=False),
            pa.field("high", pa.float64(), nullable=False),
            pa.field("low", pa.float64(), nullable=False),
            pa.field("close", pa.float64(), nullable=False),
            pa.field("volume", pa.float64()),
        ],
        metadata=_parquet_metadata(series, fingerprint),
    )
    table = pa.Table.from_pydict(
        {
            "candle_open_time": [bar.candle_open_time for bar in series.bars],
            "source_close_time": [bar.source_close_time for bar in series.bars],
            "open": [bar.open for bar in series.bars],
            "high": [bar.high for bar in series.bars],
            "low": [bar.low for bar in series.bars],
            "close": [bar.close for bar in series.bars],
            "volume": [bar.volume for bar in series.bars],
        },
        schema=schema,
    )
    try:
        with destination.open("xb") as handle:
            pq.write_table(
                table,
                handle,
                compression="zstd",
                use_dictionary=False,
                version="2.6",
                write_statistics=True,
            )
    except FileExistsError as exc:
        raise MarketDataStorageError(
            f"Parquet artifact already exists: {destination}"
        ) from exc
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return fingerprint


def _required_metadata(metadata: Mapping[bytes, bytes], key: bytes) -> str:
    value = metadata.get(key)
    if value is None:
        raise MarketDataStorageError(
            f"Parquet metadata is missing {key.decode('ascii')}"
        )
    return value.decode("utf-8")


def _optional_metadata_datetime(
    metadata: Mapping[bytes, bytes],
    key: bytes,
) -> datetime | None:
    value = _required_metadata(metadata, key)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise MarketDataStorageError(
            f"Parquet metadata has invalid {key.decode('ascii')}"
        ) from exc


def _float_or_none(value: object, *, field: str, row_number: int) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise MarketDataStorageError(
            f"Parquet row {row_number} has invalid {field} value"
        )
    return float(value)


def _datetime_or_none(
    value: object,
    *,
    field: str,
    row_number: int,
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise MarketDataStorageError(
            f"Parquet row {row_number} has invalid {field} value"
        )
    return value


def read_parquet_bar_series(path: str | Path) -> ValidatedBarSeries:
    """Read, validate, and fingerprint-check one admitted local Parquet artifact."""

    table = pq.read_table(Path(path))
    expected_columns = list(_CSV_COLUMNS)
    if table.column_names != expected_columns:
        raise MarketDataStorageError(
            "Parquet columns must be exactly " + ",".join(_CSV_COLUMNS)
        )

    raw_metadata = table.schema.metadata
    if raw_metadata is None:
        raise MarketDataStorageError("Parquet schema metadata is required")
    metadata = cast(Mapping[bytes, bytes], raw_metadata)
    if _required_metadata(metadata, b"qap_schema_version") != _STORAGE_SCHEMA_VERSION:
        raise MarketDataStorageError("unsupported Parquet market schema version")
    evidence_role = _required_metadata(metadata, b"qap_evidence_role")
    if evidence_role not in {_STORAGE_EVIDENCE_ROLE, *_LEGACY_EVIDENCE_ROLES}:
        raise MarketDataStorageError("unexpected Parquet evidence role")
    if _required_metadata(metadata, b"qap_universe_mode") != _UNIVERSE_MODE:
        raise MarketDataStorageError("unexpected Parquet universe mode")

    instrument = VenueInstrument(
        venue=_required_metadata(metadata, b"venue"),
        venue_symbol=_required_metadata(metadata, b"venue_symbol"),
        base=AssetId(_required_metadata(metadata, b"base_asset")),
        quote=AssetId(_required_metadata(metadata, b"quote_asset")),
        valid_from=_optional_metadata_datetime(metadata, b"valid_from"),
        valid_to=_optional_metadata_datetime(metadata, b"valid_to"),
    )
    interval = BarInterval(_required_metadata(metadata, b"interval"))
    columns = cast(Mapping[str, list[object]], table.to_pydict())

    bars: list[MarketBar] = []
    for index in range(table.num_rows):
        row_number = index + 1
        candle_open = _datetime_or_none(
            columns["candle_open_time"][index],
            field="candle_open_time",
            row_number=row_number,
        )
        if candle_open is None:
            raise MarketDataStorageError(
                f"Parquet row {row_number} is missing candle_open_time"
            )
        open_price = _float_or_none(
            columns["open"][index], field="open", row_number=row_number
        )
        high = _float_or_none(
            columns["high"][index], field="high", row_number=row_number
        )
        low = _float_or_none(columns["low"][index], field="low", row_number=row_number)
        close = _float_or_none(
            columns["close"][index], field="close", row_number=row_number
        )
        if open_price is None or high is None or low is None or close is None:
            raise MarketDataStorageError(
                f"Parquet row {row_number} is missing an OHLC value"
            )
        bars.append(
            MarketBar(
                instrument=instrument,
                interval=interval,
                candle_open_time=candle_open,
                source_close_time=_datetime_or_none(
                    columns["source_close_time"][index],
                    field="source_close_time",
                    row_number=row_number,
                ),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=_float_or_none(
                    columns["volume"][index],
                    field="volume",
                    row_number=row_number,
                ),
            )
        )

    try:
        series = validate_bar_series(bars)
    except ValueError as exc:
        raise MarketDataStorageError(
            f"Parquet series validation failed: {exc}"
        ) from exc

    expected_fingerprint = _required_metadata(metadata, b"qap_fingerprint")
    actual_fingerprint = fingerprint_bar_series(series)
    if actual_fingerprint != expected_fingerprint:
        raise MarketDataStorageError(
            "Parquet semantic fingerprint does not match stored metadata"
        )
    return series
