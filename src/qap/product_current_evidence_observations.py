"""Normalized SQLite observation I/O for Product current-evidence collection."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from qap.market import BookLevel, MarketMetadata, PublicBookSnapshot, VenueInstrument
from qap.market.microstructure import PublicMarketMetadataSnapshot
from qap.market.public_evidence import PublicEvidenceBundle
from qap.portfolio import AssetId
from qap.product_current_evidence import (
    ProductCurrentEvidenceError,
    ResolvedCollectorInstrument,
    SlotClaim,
)
from qap.product_market_data_protocol import DEPTH_CADENCE, L1_CADENCE


def _cadence(kind: str):
    return L1_CADENCE if kind == "l1" else DEPTH_CADENCE


def _timestamp(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value).astimezone(UTC)


class ProductCurrentEvidenceObservations:
    """Persist normalized collector observations and complete claimed slots."""

    def __init__(self, workspace_root: Path) -> None:
        self.path = (
            workspace_root.expanduser().resolve() / "product" / "product-state.sqlite3"
        )

    def _connect(self) -> sqlite3.Connection:
        if not self.path.is_file():
            raise ProductCurrentEvidenceError(
                "Current-evidence Product state is unavailable."
            )
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _levels_json(levels: tuple[BookLevel, ...]) -> str:
        return json.dumps(
            [[item.price.hex(), item.quantity.hex()] for item in levels],
            separators=(",", ":"),
        )

    @staticmethod
    def _levels(raw: str) -> tuple[BookLevel, ...]:
        values = cast(list[list[str]], json.loads(raw))
        return tuple(
            BookLevel(price=float.fromhex(price), quantity=float.fromhex(quantity))
            for price, quantity in values
        )

    def _instrument(self, instrument_id: str) -> VenueInstrument:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT venue, venue_symbol, base_asset, quote_asset, "
                "valid_from, valid_to FROM current_evidence_instruments "
                "WHERE collector_instrument_id = ?",
                (instrument_id,),
            ).fetchone()
        if row is None:
            raise ProductCurrentEvidenceError("Collector instrument cache is missing.")
        return VenueInstrument(
            venue=str(row[0]),
            venue_symbol=str(row[1]),
            base=AssetId(str(row[2])),
            quote=AssetId(str(row[3])),
            valid_from=_timestamp(cast(str | None, row[4])),
            valid_to=_timestamp(cast(str | None, row[5])),
        )

    def admit_book(self, claim: SlotClaim, snapshot: PublicBookSnapshot) -> bool:
        """Admit at most one exact in-slot public-book observation."""

        if snapshot.instrument != self._instrument(claim.collector_instrument_id):
            raise ProductCurrentEvidenceError(
                "Captured book instrument does not match slot identity."
            )
        slot_end = claim.scheduled_slot + _cadence(claim.kind)
        if not claim.scheduled_slot <= snapshot.observed_at < slot_end:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE current_evidence_slots "
                    "SET state = 'missed', claimed_at = NULL "
                    "WHERE collector_instrument_id = ? AND kind = ? "
                    "AND scheduled_slot = ? AND state = 'in_progress'",
                    (
                        claim.collector_instrument_id,
                        claim.kind,
                        claim.scheduled_slot.isoformat(),
                    ),
                )
            return False
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT state FROM current_evidence_slots "
                "WHERE collector_instrument_id = ? AND kind = ? "
                "AND scheduled_slot = ?",
                (
                    claim.collector_instrument_id,
                    claim.kind,
                    claim.scheduled_slot.isoformat(),
                ),
            ).fetchone()
            if row is None:
                raise ProductCurrentEvidenceError(
                    "Collector slot disappeared before admission."
                )
            if str(row[0]) in {"captured", "missed"}:
                return False
            connection.execute(
                "INSERT INTO current_evidence_books "
                "(snapshot_id, collector_instrument_id, kind, scheduled_slot, "
                "observed_at, source_id, source_fingerprint, bids_json, asks_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    snapshot.snapshot_id,
                    claim.collector_instrument_id,
                    claim.kind,
                    claim.scheduled_slot.isoformat(),
                    snapshot.observed_at.isoformat(),
                    snapshot.source_id,
                    snapshot.source_fingerprint,
                    self._levels_json(snapshot.bids),
                    self._levels_json(snapshot.asks),
                ),
            )
            connection.execute(
                "UPDATE current_evidence_slots "
                "SET state = 'captured', observed_at = ?, snapshot_id = ?, "
                "claimed_at = NULL WHERE collector_instrument_id = ? AND kind = ? "
                "AND scheduled_slot = ?",
                (
                    snapshot.observed_at.isoformat(),
                    snapshot.snapshot_id,
                    claim.collector_instrument_id,
                    claim.kind,
                    claim.scheduled_slot.isoformat(),
                ),
            )
        return True

    @staticmethod
    def _decimal(value: Decimal | None) -> str | None:
        return None if value is None else str(value)

    @classmethod
    def _metadata_json(cls, metadata: MarketMetadata) -> str:
        return json.dumps(
            {
                "status": metadata.status,
                "price_tick": str(metadata.price_tick),
                "minimum_price": cls._decimal(metadata.minimum_price),
                "maximum_price": cls._decimal(metadata.maximum_price),
                "quantity_step": str(metadata.quantity_step),
                "minimum_quantity": cls._decimal(metadata.minimum_quantity),
                "maximum_quantity": cls._decimal(metadata.maximum_quantity),
                "minimum_notional": cls._decimal(metadata.minimum_notional),
                "maximum_notional": cls._decimal(metadata.maximum_notional),
                "minimum_notional_applies_to_market": (
                    metadata.minimum_notional_applies_to_market
                ),
                "maximum_notional_applies_to_market": (
                    metadata.maximum_notional_applies_to_market
                ),
                "notional_average_price_minutes": (
                    metadata.notional_average_price_minutes
                ),
                "market_quantity_step": cls._decimal(metadata.market_quantity_step),
                "market_minimum_quantity": cls._decimal(
                    metadata.market_minimum_quantity
                ),
                "market_maximum_quantity": cls._decimal(
                    metadata.market_maximum_quantity
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _optional_decimal(value: object) -> Decimal | None:
        return None if value is None else Decimal(str(value))

    @classmethod
    def _metadata(cls, instrument: VenueInstrument, raw: str) -> MarketMetadata:
        payload = cast(dict[str, object], json.loads(raw))
        return MarketMetadata(
            instrument=instrument,
            status=str(payload["status"]),
            price_tick=Decimal(str(payload["price_tick"])),
            minimum_price=cls._optional_decimal(payload["minimum_price"]),
            maximum_price=cls._optional_decimal(payload["maximum_price"]),
            quantity_step=Decimal(str(payload["quantity_step"])),
            minimum_quantity=cls._optional_decimal(payload["minimum_quantity"]),
            maximum_quantity=cls._optional_decimal(payload["maximum_quantity"]),
            minimum_notional=cls._optional_decimal(payload["minimum_notional"]),
            maximum_notional=cls._optional_decimal(payload["maximum_notional"]),
            minimum_notional_applies_to_market=cast(
                bool, payload["minimum_notional_applies_to_market"]
            ),
            maximum_notional_applies_to_market=cast(
                bool, payload["maximum_notional_applies_to_market"]
            ),
            notional_average_price_minutes=int(
                str(payload["notional_average_price_minutes"])
            ),
            market_quantity_step=cls._optional_decimal(payload["market_quantity_step"]),
            market_minimum_quantity=cls._optional_decimal(
                payload["market_minimum_quantity"]
            ),
            market_maximum_quantity=cls._optional_decimal(
                payload["market_maximum_quantity"]
            ),
        )

    def admit_metadata(
        self,
        *,
        instrument_id: str,
        snapshot: PublicMarketMetadataSnapshot,
    ) -> bool:
        """Persist one explicit metadata event for a frozen instrument."""

        if snapshot.metadata.instrument != self._instrument(instrument_id):
            raise ProductCurrentEvidenceError(
                "Captured metadata instrument does not match frozen identity."
            )
        with self._connect() as connection:
            before = connection.total_changes
            connection.execute(
                "INSERT OR IGNORE INTO current_evidence_metadata "
                "(snapshot_id, collector_instrument_id, observed_at, source_id, "
                "source_fingerprint, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    snapshot.snapshot_id,
                    instrument_id,
                    snapshot.observed_at.isoformat(),
                    snapshot.source_id,
                    snapshot.source_fingerprint,
                    self._metadata_json(snapshot.metadata),
                ),
            )
            return connection.total_changes > before

    def metadata_needed(self, instrument_id: str) -> bool:
        """Require one metadata observation after each active-plan start event."""

        with self._connect() as connection:
            required = connection.execute(
                "SELECT MAX(started_at) FROM current_evidence_plans "
                "WHERE collector_instrument_id = ? AND stopped_at IS NULL",
                (instrument_id,),
            ).fetchone()
            if required is None or required[0] is None:
                return False
            latest = connection.execute(
                "SELECT MAX(observed_at) FROM current_evidence_metadata "
                "WHERE collector_instrument_id = ?",
                (instrument_id,),
            ).fetchone()
        if latest is None or latest[0] is None:
            return True
        return datetime.fromisoformat(str(latest[0])) < datetime.fromisoformat(
            str(required[0])
        )

    def evidence(self, target: ResolvedCollectorInstrument) -> PublicEvidenceBundle:
        """Reconstruct normalized evidence without changing scientific authority."""

        if self._instrument(target.collector_instrument_id) != target.instrument:
            raise ProductCurrentEvidenceError(
                "Collector evidence instrument cache mismatch."
            )
        with self._connect() as connection:
            books = connection.execute(
                "SELECT snapshot_id, kind, observed_at, source_id, "
                "source_fingerprint, bids_json, asks_json "
                "FROM current_evidence_books WHERE collector_instrument_id = ? "
                "ORDER BY observed_at, snapshot_id",
                (target.collector_instrument_id,),
            ).fetchall()
            metadata_rows = connection.execute(
                "SELECT snapshot_id, observed_at, source_id, source_fingerprint, "
                "metadata_json "
                "FROM current_evidence_metadata WHERE collector_instrument_id = ? "
                "ORDER BY observed_at, snapshot_id",
                (target.collector_instrument_id,),
            ).fetchall()
        l1: list[PublicBookSnapshot] = []
        depth: list[PublicBookSnapshot] = []
        for row in books:
            snapshot = PublicBookSnapshot(
                instrument=target.instrument,
                observed_at=datetime.fromisoformat(str(row[2])).astimezone(UTC),
                source_id=str(row[3]),
                source_fingerprint=str(row[4]),
                bids=self._levels(str(row[5])),
                asks=self._levels(str(row[6])),
            )
            if snapshot.snapshot_id != str(row[0]):
                raise ProductCurrentEvidenceError(
                    "Stored public-book observation identity mismatch."
                )
            (l1 if str(row[1]) == "l1" else depth).append(snapshot)
        metadata: list[PublicMarketMetadataSnapshot] = []
        for row in metadata_rows:
            snapshot = PublicMarketMetadataSnapshot(
                metadata=self._metadata(target.instrument, str(row[4])),
                observed_at=datetime.fromisoformat(str(row[1])).astimezone(UTC),
                source_id=str(row[2]),
                source_fingerprint=str(row[3]),
            )
            if snapshot.snapshot_id != str(row[0]):
                raise ProductCurrentEvidenceError(
                    "Stored metadata observation identity mismatch."
                )
            metadata.append(snapshot)
        return PublicEvidenceBundle(tuple(l1), tuple(depth), tuple(metadata))

    def latest_observation(self, instrument_id: str) -> datetime | None:
        if not self.path.is_file():
            return None
        with self._connect() as connection:
            book = connection.execute(
                "SELECT MAX(observed_at) FROM current_evidence_books "
                "WHERE collector_instrument_id = ?",
                (instrument_id,),
            ).fetchone()
            metadata = connection.execute(
                "SELECT MAX(observed_at) FROM current_evidence_metadata "
                "WHERE collector_instrument_id = ?",
                (instrument_id,),
            ).fetchone()
        values = [
            datetime.fromisoformat(str(value)).astimezone(UTC)
            for row in (book, metadata)
            if row is not None
            for value in row
            if value is not None
        ]
        return max(values) if values else None


__all__ = ["ProductCurrentEvidenceObservations"]
