# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Strict Parquet persistence for public microstructure evidence."""

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from qap.market.instruments import VenueInstrument
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import (
    BookLevel,
    PublicBookSnapshot,
    PublicMarketMetadataSnapshot,
)
from qap.portfolio import AssetId


class MicrostructureStorageError(ValueError):
    """Raised when persisted public microstructure evidence is malformed."""


_LEVEL_TYPE = pa.struct(
    [
        ("price", pa.float64()),
        ("quantity", pa.float64()),
    ]
)
_PUBLIC_BOOK_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("snapshot_id", pa.string()),
        ("venue", pa.string()),
        ("venue_symbol", pa.string()),
        ("base_asset", pa.string()),
        ("quote_asset", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_id", pa.string()),
        ("source_fingerprint", pa.string()),
        ("bids", pa.list_(_LEVEL_TYPE)),
        ("asks", pa.list_(_LEVEL_TYPE)),
    ]
)
_SCHEMA_VERSION = "qap.market.public-book-snapshot.v1"
_METADATA_SCHEMA_VERSION = "qap.market.public-metadata-snapshot.v1"
_PUBLIC_METADATA_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("snapshot_id", pa.string()),
        ("venue", pa.string()),
        ("venue_symbol", pa.string()),
        ("base_asset", pa.string()),
        ("quote_asset", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_id", pa.string()),
        ("source_fingerprint", pa.string()),
        ("metadata_json", pa.string()),
    ]
)


def _snapshot_row(snapshot: PublicBookSnapshot) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "venue": snapshot.instrument.venue,
        "venue_symbol": snapshot.instrument.venue_symbol,
        "base_asset": snapshot.instrument.base.key,
        "quote_asset": snapshot.instrument.quote.key,
        "observed_at": snapshot.observed_at,
        "source_id": snapshot.source_id,
        "source_fingerprint": snapshot.source_fingerprint,
        "bids": [
            {"price": level.price, "quantity": level.quantity}
            for level in snapshot.bids
        ],
        "asks": [
            {"price": level.price, "quantity": level.quantity}
            for level in snapshot.asks
        ],
    }


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _metadata_payload(metadata: MarketMetadata) -> dict[str, object]:
    return {
        "status": metadata.status,
        "price_tick": str(metadata.price_tick),
        "minimum_price": _decimal_text(metadata.minimum_price),
        "maximum_price": _decimal_text(metadata.maximum_price),
        "quantity_step": str(metadata.quantity_step),
        "minimum_quantity": _decimal_text(metadata.minimum_quantity),
        "maximum_quantity": _decimal_text(metadata.maximum_quantity),
        "minimum_notional": _decimal_text(metadata.minimum_notional),
        "maximum_notional": _decimal_text(metadata.maximum_notional),
        "minimum_notional_applies_to_market": (
            metadata.minimum_notional_applies_to_market
        ),
        "maximum_notional_applies_to_market": (
            metadata.maximum_notional_applies_to_market
        ),
        "notional_average_price_minutes": metadata.notional_average_price_minutes,
        "market_quantity_step": _decimal_text(metadata.market_quantity_step),
        "market_minimum_quantity": _decimal_text(metadata.market_minimum_quantity),
        "market_maximum_quantity": _decimal_text(metadata.market_maximum_quantity),
    }


def _metadata_row(snapshot: PublicMarketMetadataSnapshot) -> dict[str, object]:
    metadata = snapshot.metadata
    return {
        "schema_version": _METADATA_SCHEMA_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "venue": metadata.instrument.venue,
        "venue_symbol": metadata.instrument.venue_symbol,
        "base_asset": metadata.instrument.base.key,
        "quote_asset": metadata.instrument.quote.key,
        "observed_at": snapshot.observed_at,
        "source_id": snapshot.source_id,
        "source_fingerprint": snapshot.source_fingerprint,
        "metadata_json": json.dumps(
            _metadata_payload(metadata),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ),
    }


def _atomic_write(path: Path, table: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        pq.write_table(table, temporary)
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise MicrostructureStorageError(
            f"failed to write microstructure parquet: {path}"
        ) from exc


def write_public_book_snapshots(
    path: str | Path,
    snapshots: tuple[PublicBookSnapshot, ...],
) -> None:
    """Write exact public-book evidence in deterministic order."""

    copied = tuple(snapshots)
    if not copied:
        raise MicrostructureStorageError(
            "at least one public book snapshot is required"
        )
    if any(
        not isinstance(cast(object, snapshot), PublicBookSnapshot)
        for snapshot in copied
    ):
        raise TypeError("snapshots must contain PublicBookSnapshot values")
    ordered = tuple(
        sorted(copied, key=lambda item: (item.observed_at, item.snapshot_id))
    )
    ids = tuple(item.snapshot_id for item in ordered)
    if len(set(ids)) != len(ids):
        raise MicrostructureStorageError("duplicate public book snapshot_id")
    table = pa.Table.from_pylist(
        [_snapshot_row(snapshot) for snapshot in ordered],
        schema=_PUBLIC_BOOK_SCHEMA,
    )
    _atomic_write(Path(path), table)


def append_public_book_snapshot(
    path: str | Path,
    snapshot: PublicBookSnapshot,
) -> None:
    """Append one immutable observation, rejecting conflicting same-time evidence."""

    target = Path(path)
    existing = read_public_book_snapshots(target) if target.is_file() else ()
    for item in existing:
        if item.snapshot_id == snapshot.snapshot_id:
            return
        if (
            item.instrument == snapshot.instrument
            and item.observed_at == snapshot.observed_at
        ):
            raise MicrostructureStorageError(
                "conflicting public book observation at the same timestamp"
            )
    write_public_book_snapshots(target, (*existing, snapshot))


def _levels(value: object, *, side: str) -> tuple[BookLevel, ...]:
    if not isinstance(value, list):
        raise MicrostructureStorageError(f"{side} must be a list")
    levels: list[BookLevel] = []
    for position, item in enumerate(value):
        if not isinstance(item, dict):
            raise MicrostructureStorageError(
                f"{side} level {position} must be a struct"
            )
        try:
            levels.append(
                BookLevel(
                    price=float(item["price"]),
                    quantity=float(item["quantity"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MicrostructureStorageError(
                f"invalid {side} level at position {position}"
            ) from exc
    return tuple(levels)


def read_public_book_snapshots(path: str | Path) -> tuple[PublicBookSnapshot, ...]:
    """Read and revalidate exact public-book evidence and semantic IDs."""

    source = Path(path)
    try:
        table = pq.read_table(source)
    except (OSError, pa.ArrowException) as exc:
        raise MicrostructureStorageError(
            f"failed to read microstructure parquet: {source}"
        ) from exc
    if not table.schema.equals(_PUBLIC_BOOK_SCHEMA):
        raise MicrostructureStorageError("microstructure parquet schema mismatch")

    snapshots: list[PublicBookSnapshot] = []
    for position, row in enumerate(table.to_pylist()):
        if row["schema_version"] != _SCHEMA_VERSION:
            raise MicrostructureStorageError(
                "unsupported microstructure schema_version"
            )
        try:
            snapshot = PublicBookSnapshot(
                instrument=VenueInstrument(
                    venue=row["venue"],
                    venue_symbol=row["venue_symbol"],
                    base=AssetId(row["base_asset"]),
                    quote=AssetId(row["quote_asset"]),
                ),
                observed_at=row["observed_at"],
                source_id=row["source_id"],
                source_fingerprint=row["source_fingerprint"],
                bids=_levels(row["bids"], side="bids"),
                asks=_levels(row["asks"], side="asks"),
            )
        except (TypeError, ValueError) as exc:
            raise MicrostructureStorageError(
                f"invalid public book snapshot at row {position}"
            ) from exc
        if row["snapshot_id"] != snapshot.snapshot_id:
            raise MicrostructureStorageError(f"snapshot_id mismatch at row {position}")
        snapshots.append(snapshot)

    if not snapshots:
        raise MicrostructureStorageError(
            "microstructure parquet must contain snapshots"
        )
    ids = tuple(item.snapshot_id for item in snapshots)
    if len(set(ids)) != len(ids):
        raise MicrostructureStorageError("duplicate public book snapshot_id")
    ordered = tuple(
        sorted(snapshots, key=lambda item: (item.observed_at, item.snapshot_id))
    )
    if tuple(snapshots) != ordered:
        raise MicrostructureStorageError(
            "microstructure parquet rows must be deterministically ordered"
        )
    return ordered


def _maybe_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MicrostructureStorageError(f"{field} must be a decimal string or null")
    try:
        return Decimal(value)
    except Exception as exc:
        raise MicrostructureStorageError(f"invalid decimal field: {field}") from exc


def _metadata_from_row(row: dict[str, object]) -> PublicMarketMetadataSnapshot:
    if row["schema_version"] != _METADATA_SCHEMA_VERSION:
        raise MicrostructureStorageError("unsupported metadata schema_version")
    try:
        payload = json.loads(cast(str, row["metadata_json"]))
    except (TypeError, json.JSONDecodeError) as exc:
        raise MicrostructureStorageError("metadata_json is malformed") from exc
    if not isinstance(payload, dict):
        raise MicrostructureStorageError("metadata_json must be an object")
    values = cast(dict[str, object], payload)
    try:
        metadata = MarketMetadata(
            instrument=VenueInstrument(
                venue=cast(str, row["venue"]),
                venue_symbol=cast(str, row["venue_symbol"]),
                base=AssetId(cast(str, row["base_asset"])),
                quote=AssetId(cast(str, row["quote_asset"])),
            ),
            status=cast(str, values["status"]),
            price_tick=Decimal(cast(str, values["price_tick"])),
            minimum_price=_maybe_decimal(
                values.get("minimum_price"), field="minimum_price"
            ),
            maximum_price=_maybe_decimal(
                values.get("maximum_price"), field="maximum_price"
            ),
            quantity_step=Decimal(cast(str, values["quantity_step"])),
            minimum_quantity=_maybe_decimal(
                values.get("minimum_quantity"), field="minimum_quantity"
            ),
            maximum_quantity=_maybe_decimal(
                values.get("maximum_quantity"), field="maximum_quantity"
            ),
            minimum_notional=_maybe_decimal(
                values.get("minimum_notional"), field="minimum_notional"
            ),
            maximum_notional=_maybe_decimal(
                values.get("maximum_notional"), field="maximum_notional"
            ),
            minimum_notional_applies_to_market=cast(
                bool, values["minimum_notional_applies_to_market"]
            ),
            maximum_notional_applies_to_market=cast(
                bool, values["maximum_notional_applies_to_market"]
            ),
            notional_average_price_minutes=cast(
                int, values["notional_average_price_minutes"]
            ),
            market_quantity_step=_maybe_decimal(
                values.get("market_quantity_step"), field="market_quantity_step"
            ),
            market_minimum_quantity=_maybe_decimal(
                values.get("market_minimum_quantity"),
                field="market_minimum_quantity",
            ),
            market_maximum_quantity=_maybe_decimal(
                values.get("market_maximum_quantity"),
                field="market_maximum_quantity",
            ),
        )
        snapshot = PublicMarketMetadataSnapshot(
            metadata=metadata,
            observed_at=cast(Any, row["observed_at"]),
            source_id=cast(str, row["source_id"]),
            source_fingerprint=cast(str, row["source_fingerprint"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MicrostructureStorageError("invalid metadata snapshot row") from exc
    if snapshot.snapshot_id != row["snapshot_id"]:
        raise MicrostructureStorageError("metadata snapshot_id mismatch")
    return snapshot


def write_public_market_metadata_snapshots(
    path: str | Path,
    snapshots: tuple[PublicMarketMetadataSnapshot, ...],
) -> None:
    copied = tuple(snapshots)
    if not copied:
        raise MicrostructureStorageError(
            "at least one public metadata snapshot is required"
        )
    ordered = tuple(
        sorted(copied, key=lambda item: (item.observed_at, item.snapshot_id))
    )
    ids = tuple(item.snapshot_id for item in ordered)
    if len(set(ids)) != len(ids):
        raise MicrostructureStorageError("duplicate public metadata snapshot_id")
    table = pa.Table.from_pylist(
        [_metadata_row(snapshot) for snapshot in ordered],
        schema=_PUBLIC_METADATA_SCHEMA,
    )
    _atomic_write(Path(path), table)


def read_public_market_metadata_snapshots(
    path: str | Path,
) -> tuple[PublicMarketMetadataSnapshot, ...]:
    source = Path(path)
    try:
        table = pq.read_table(source)
    except (OSError, pa.ArrowException) as exc:
        raise MicrostructureStorageError(
            f"failed to read metadata parquet: {source}"
        ) from exc
    if not table.schema.equals(_PUBLIC_METADATA_SCHEMA):
        raise MicrostructureStorageError("metadata parquet schema mismatch")
    snapshots = tuple(_metadata_from_row(row) for row in table.to_pylist())
    if not snapshots:
        raise MicrostructureStorageError("metadata parquet must contain snapshots")
    ordered = tuple(
        sorted(snapshots, key=lambda item: (item.observed_at, item.snapshot_id))
    )
    if snapshots != ordered:
        raise MicrostructureStorageError(
            "metadata parquet rows must be deterministically ordered"
        )
    return ordered


def append_public_market_metadata_snapshot(
    path: str | Path,
    snapshot: PublicMarketMetadataSnapshot,
) -> None:
    target = Path(path)
    existing = read_public_market_metadata_snapshots(target) if target.is_file() else ()
    for item in existing:
        if item.snapshot_id == snapshot.snapshot_id:
            return
        if (
            item.metadata.instrument == snapshot.metadata.instrument
            and item.observed_at == snapshot.observed_at
        ):
            raise MicrostructureStorageError(
                "conflicting public metadata observation at the same timestamp"
            )
    write_public_market_metadata_snapshots(target, (*existing, snapshot))


__all__ = [
    "MicrostructureStorageError",
    "append_public_book_snapshot",
    "append_public_market_metadata_snapshot",
    "read_public_book_snapshots",
    "read_public_market_metadata_snapshots",
    "write_public_book_snapshots",
    "write_public_market_metadata_snapshots",
]
