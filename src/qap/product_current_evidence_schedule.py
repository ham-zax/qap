"""Scheduled-slot persistence for Product current public evidence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from qap.product_current_evidence import (
    CollectionKind,
    ProductCurrentEvidenceError,
    SlotClaim,
    SlotCounts,
    scheduled_slot,
)
from qap.product_market_data_protocol import DEPTH_CADENCE, L1_CADENCE


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _cadence(kind: CollectionKind) -> timedelta:
    return L1_CADENCE if kind == "l1" else DEPTH_CADENCE


class ProductCurrentEvidenceSchedule:
    """Reconcile elapsed slots and claim the exact current UTC slot."""

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
    def _has_plan_overlap(
        connection: sqlite3.Connection,
        instrument_id: str,
        slot_start: datetime,
        slot_end: datetime,
    ) -> bool:
        return (
            connection.execute(
                "SELECT 1 FROM current_evidence_plans "
                "WHERE collector_instrument_id = ? "
                "AND started_at < ? "
                "AND (stopped_at IS NULL OR stopped_at > ?) LIMIT 1",
                (instrument_id, slot_end.isoformat(), slot_start.isoformat()),
            ).fetchone()
            is not None
        )

    @staticmethod
    def _has_active_plan(
        connection: sqlite3.Connection,
        instrument_id: str,
        slot_end: datetime,
    ) -> bool:
        return (
            connection.execute(
                "SELECT 1 FROM current_evidence_plans "
                "WHERE collector_instrument_id = ? "
                "AND stopped_at IS NULL AND started_at < ? LIMIT 1",
                (instrument_id, slot_end.isoformat()),
            ).fetchone()
            is not None
        )

    def reconcile_and_claim(
        self,
        *,
        instrument_id: str,
        kind: CollectionKind,
        now: datetime | None = None,
    ) -> SlotClaim | None:
        current = datetime.now(UTC) if now is None else _utc(now, field="now")
        cadence = _cadence(kind)
        current_slot = scheduled_slot(current, kind)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE current_evidence_slots "
                "SET state = 'missed', claimed_at = NULL "
                "WHERE collector_instrument_id = ? AND kind = ? "
                "AND state = 'in_progress' AND scheduled_slot < ?",
                (instrument_id, kind, current_slot.isoformat()),
            )
            earliest = connection.execute(
                "SELECT MIN(started_at) FROM current_evidence_plans "
                "WHERE collector_instrument_id = ?",
                (instrument_id,),
            ).fetchone()
            if earliest is None or earliest[0] is None:
                return None
            latest = connection.execute(
                "SELECT MAX(scheduled_slot) FROM current_evidence_slots "
                "WHERE collector_instrument_id = ? AND kind = ?",
                (instrument_id, kind),
            ).fetchone()
            if latest is None or latest[0] is None:
                cursor = scheduled_slot(
                    datetime.fromisoformat(str(earliest[0])),
                    kind,
                )
            else:
                cursor = (
                    datetime.fromisoformat(str(latest[0])).astimezone(UTC) + cadence
                )
            while cursor < current_slot:
                slot_end = cursor + cadence
                if self._has_plan_overlap(
                    connection,
                    instrument_id,
                    cursor,
                    slot_end,
                ):
                    connection.execute(
                        "INSERT OR IGNORE INTO current_evidence_slots "
                        "(collector_instrument_id, kind, scheduled_slot, state) "
                        "VALUES (?, ?, ?, 'missed')",
                        (instrument_id, kind, cursor.isoformat()),
                    )
                cursor = slot_end
            slot_end = current_slot + cadence
            if not self._has_active_plan(connection, instrument_id, slot_end):
                return None
            existing = connection.execute(
                "SELECT state FROM current_evidence_slots "
                "WHERE collector_instrument_id = ? AND kind = ? "
                "AND scheduled_slot = ?",
                (instrument_id, kind, current_slot.isoformat()),
            ).fetchone()
            if existing is not None and str(existing[0]) in {"captured", "missed"}:
                return None
            if existing is None:
                connection.execute(
                    "INSERT INTO current_evidence_slots "
                    "(collector_instrument_id, kind, scheduled_slot, state, "
                    "claimed_at) VALUES (?, ?, ?, 'in_progress', ?)",
                    (
                        instrument_id,
                        kind,
                        current_slot.isoformat(),
                        current.isoformat(),
                    ),
                )
            else:
                connection.execute(
                    "UPDATE current_evidence_slots SET claimed_at = ? "
                    "WHERE collector_instrument_id = ? AND kind = ? "
                    "AND scheduled_slot = ? AND state = 'in_progress'",
                    (
                        current.isoformat(),
                        instrument_id,
                        kind,
                        current_slot.isoformat(),
                    ),
                )
        return SlotClaim(instrument_id, kind, current_slot)

    def slot_counts(self, instrument_id: str, kind: CollectionKind) -> SlotCounts:
        if not self.path.is_file():
            return SlotCounts(0, 0, 0)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT state, COUNT(*) FROM current_evidence_slots "
                "WHERE collector_instrument_id = ? AND kind = ? GROUP BY state",
                (instrument_id, kind),
            ).fetchall()
        counts = {str(state): int(count) for state, count in rows}
        return SlotCounts(
            scheduled=sum(counts.values()),
            captured=counts.get("captured", 0),
            missed=counts.get("missed", 0),
        )


__all__ = ["ProductCurrentEvidenceSchedule"]
