# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Strict Parquet persistence for public microstructure evidence."""

import os
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from qap.market.instruments import VenueInstrument
from qap.market.microstructure import BookLevel, PublicBookSnapshot
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


__all__ = [
    "MicrostructureStorageError",
    "read_public_book_snapshots",
    "write_public_book_snapshots",
]
