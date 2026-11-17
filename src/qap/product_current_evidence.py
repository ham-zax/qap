"""Bounded Product operational state for persistent current public evidence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

from qap.market import PublicBookSnapshot, VenueInstrument
from qap.market.microstructure import PublicMarketMetadataSnapshot
from qap.market.public_evidence import PublicEvidenceBundle
from qap.product_market_data_protocol import DEPTH_CADENCE, L1_CADENCE

CollectionKind = Literal["l1", "depth"]
CollectorStatus = Literal["not_running", "running", "failed"]
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_INSTRUMENT_COLUMNS = (
    "collector_instrument_id, venue, venue_symbol, base_asset, quote_asset, "
    "valid_from, valid_to"
)
_PLAN_COLUMNS = (
    "plan_id, source_scan_id, candidate_id, selection_cohort_id, "
    "active_cohort_id, active_freeze_id, execution_instrument_id, "
    "collector_instrument_id, started_at, stopped_at"
)


class ProductCurrentEvidenceError(RuntimeError):
    """Raised when Product collector state or frozen lineage is invalid."""


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _timestamp(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value).astimezone(UTC)


def _cadence(kind: CollectionKind) -> timedelta:
    return L1_CADENCE if kind == "l1" else DEPTH_CADENCE


def scheduled_slot(value: datetime, kind: CollectionKind) -> datetime:
    """Return the exact nominal UTC slot containing ``value``."""

    current = _utc(value, field="slot time")
    step_us = int(_cadence(kind).total_seconds() * 1_000_000)
    elapsed = current - _EPOCH
    elapsed_us = (
        elapsed.days * 86_400_000_000
        + elapsed.seconds * 1_000_000
        + elapsed.microseconds
    )
    return _EPOCH + timedelta(microseconds=(elapsed_us // step_us) * step_us)


@dataclass(frozen=True, slots=True)
class ResolvedCollectorInstrument:
    collector_instrument_id: str
    execution_instrument_id: str
    active_cohort_id: str
    active_freeze_id: str
    historical_run_id: str
    instrument: VenueInstrument


@dataclass(frozen=True, slots=True)
class CollectionPlan:
    plan_id: str
    source_scan_id: str
    candidate_id: str
    selection_cohort_id: str
    active_cohort_id: str
    active_freeze_id: str
    execution_instrument_id: str
    collector_instrument_id: str
    started_at: datetime
    stopped_at: datetime | None


@dataclass(frozen=True, slots=True)
class CollectorLeaseState:
    status: CollectorStatus
    pid: int | None = None
    process_start_marker: str | None = None
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SlotClaim:
    collector_instrument_id: str
    kind: CollectionKind
    scheduled_slot: datetime


@dataclass(frozen=True, slots=True)
class SlotCounts:
    scheduled: int
    captured: int
    missed: int


def resolve_frozen_instrument(
    run_root: Path,
    *,
    active_cohort_id: str,
    active_freeze_id: str,
) -> ResolvedCollectorInstrument:
    """Retired scanner-forward freeze resolution."""
    del run_root, active_cohort_id, active_freeze_id
    raise ProductCurrentEvidenceError("Scanner forward cohorts are retired.")


class ProductCurrentEvidenceStore:
    """Own M7 plans, lease, scheduled slots, and normalized public observations."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.path = self.workspace_root / "product" / "product-state.sqlite3"

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        self._schema(connection)
        return connection

    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS current_evidence_collector (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                status TEXT NOT NULL,
                pid INTEGER,
                process_start_marker TEXT,
                started_at TEXT,
                heartbeat_at TEXT,
                failure_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS current_evidence_instruments (
                collector_instrument_id TEXT PRIMARY KEY,
                venue TEXT NOT NULL,
                venue_symbol TEXT NOT NULL,
                base_asset TEXT NOT NULL,
                quote_asset TEXT NOT NULL,
                valid_from TEXT,
                valid_to TEXT
            );
            CREATE TABLE IF NOT EXISTS current_evidence_plans (
                plan_id TEXT PRIMARY KEY,
                source_scan_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                selection_cohort_id TEXT NOT NULL,
                active_cohort_id TEXT NOT NULL,
                active_freeze_id TEXT NOT NULL,
                execution_instrument_id TEXT NOT NULL,
                collector_instrument_id TEXT NOT NULL
                    REFERENCES current_evidence_instruments(collector_instrument_id),
                started_at TEXT NOT NULL,
                stopped_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS current_evidence_one_active_plan_per_idea
                ON current_evidence_plans(source_scan_id, candidate_id)
                WHERE stopped_at IS NULL;
            CREATE TABLE IF NOT EXISTS current_evidence_slots (
                collector_instrument_id TEXT NOT NULL
                    REFERENCES current_evidence_instruments(collector_instrument_id),
                kind TEXT NOT NULL CHECK (kind IN ('l1', 'depth')),
                scheduled_slot TEXT NOT NULL,
                state TEXT NOT NULL
                    CHECK (state IN ('in_progress', 'captured', 'missed')),
                claimed_at TEXT,
                observed_at TEXT,
                snapshot_id TEXT,
                PRIMARY KEY (collector_instrument_id, kind, scheduled_slot)
            );
            CREATE TABLE IF NOT EXISTS current_evidence_books (
                snapshot_id TEXT PRIMARY KEY,
                collector_instrument_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('l1', 'depth')),
                scheduled_slot TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_fingerprint TEXT NOT NULL,
                bids_json TEXT NOT NULL,
                asks_json TEXT NOT NULL,
                UNIQUE (collector_instrument_id, kind, scheduled_slot),
                FOREIGN KEY (collector_instrument_id, kind, scheduled_slot)
                    REFERENCES current_evidence_slots(
                        collector_instrument_id, kind, scheduled_slot
                    )
            );
            CREATE TABLE IF NOT EXISTS current_evidence_metadata (
                snapshot_id TEXT PRIMARY KEY,
                collector_instrument_id TEXT NOT NULL
                    REFERENCES current_evidence_instruments(collector_instrument_id),
                observed_at TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_fingerprint TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            """
        )

    @staticmethod
    def _instrument_row(target: ResolvedCollectorInstrument) -> tuple[object, ...]:
        instrument = target.instrument
        return (
            target.collector_instrument_id,
            instrument.venue,
            instrument.venue_symbol,
            instrument.base.key,
            instrument.quote.key,
            None
            if instrument.valid_from is None
            else instrument.valid_from.isoformat(),
            None if instrument.valid_to is None else instrument.valid_to.isoformat(),
        )

    @staticmethod
    def _assert_cached_instrument(
        row: tuple[object, ...], target: ResolvedCollectorInstrument
    ) -> None:
        expected = ProductCurrentEvidenceStore._instrument_row(target)
        if tuple(row) != expected:
            raise ProductCurrentEvidenceError(
                "Cached collector instrument disagrees with immutable frozen lineage."
            )

    def _ensure_instrument(
        self, connection: sqlite3.Connection, target: ResolvedCollectorInstrument
    ) -> None:
        row = connection.execute(
            f"SELECT {_INSTRUMENT_COLUMNS} FROM current_evidence_instruments "
            "WHERE collector_instrument_id = ?",
            (target.collector_instrument_id,),
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO current_evidence_instruments "
                f"({_INSTRUMENT_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                self._instrument_row(target),
            )
            return
        self._assert_cached_instrument(cast(tuple[object, ...], row), target)

    @staticmethod
    def _plan(row: tuple[object, ...]) -> CollectionPlan:
        return CollectionPlan(
            plan_id=str(row[0]),
            source_scan_id=str(row[1]),
            candidate_id=str(row[2]),
            selection_cohort_id=str(row[3]),
            active_cohort_id=str(row[4]),
            active_freeze_id=str(row[5]),
            execution_instrument_id=str(row[6]),
            collector_instrument_id=str(row[7]),
            started_at=datetime.fromisoformat(str(row[8])).astimezone(UTC),
            stopped_at=_timestamp(cast(str | None, row[9])),
        )

    def active_plan(
        self, *, source_scan_id: str, candidate_id: str
    ) -> CollectionPlan | None:
        if not self.path.is_file():
            return None
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT {_PLAN_COLUMNS} FROM current_evidence_plans "
                "WHERE source_scan_id = ? AND candidate_id = ? AND stopped_at IS NULL",
                (source_scan_id, candidate_id),
            ).fetchone()
        return None if row is None else self._plan(cast(tuple[object, ...], row))

    def start_plan(
        self,
        *,
        source_scan_id: str,
        candidate_id: str,
        selection_cohort_id: str,
        target: ResolvedCollectorInstrument,
        started_at: datetime | None = None,
    ) -> CollectionPlan:
        timestamp = (
            datetime.now(UTC)
            if started_at is None
            else _utc(started_at, field="started_at")
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._ensure_instrument(connection, target)
            existing = connection.execute(
                f"SELECT {_PLAN_COLUMNS} FROM current_evidence_plans "
                "WHERE source_scan_id = ? AND candidate_id = ? AND stopped_at IS NULL",
                (source_scan_id, candidate_id),
            ).fetchone()
            if existing is not None:
                plan = self._plan(cast(tuple[object, ...], existing))
                if (
                    plan.selection_cohort_id != selection_cohort_id
                    or plan.active_cohort_id != target.active_cohort_id
                    or plan.active_freeze_id != target.active_freeze_id
                    or plan.execution_instrument_id != target.execution_instrument_id
                    or plan.collector_instrument_id != target.collector_instrument_id
                ):
                    raise ProductCurrentEvidenceError(
                        "Current-evidence collection is already active for another "
                        "frozen membership. Stop it before starting the new membership."
                    )
                return plan
            plan_id = str(uuid4())
            connection.execute(
                "INSERT INTO current_evidence_plans "
                f"({_PLAN_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    plan_id,
                    source_scan_id,
                    candidate_id,
                    selection_cohort_id,
                    target.active_cohort_id,
                    target.active_freeze_id,
                    target.execution_instrument_id,
                    target.collector_instrument_id,
                    timestamp.isoformat(),
                ),
            )
        plan = self.active_plan(
            source_scan_id=source_scan_id, candidate_id=candidate_id
        )
        if plan is None:
            raise ProductCurrentEvidenceError("Collection plan was not persisted.")
        return plan

    def stop_plan(
        self,
        *,
        source_scan_id: str,
        candidate_id: str,
        stopped_at: datetime | None = None,
    ) -> CollectionPlan | None:
        timestamp = (
            datetime.now(UTC)
            if stopped_at is None
            else _utc(stopped_at, field="stopped_at")
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                f"SELECT {_PLAN_COLUMNS} FROM current_evidence_plans "
                "WHERE source_scan_id = ? AND candidate_id = ? AND stopped_at IS NULL",
                (source_scan_id, candidate_id),
            ).fetchone()
            if row is None:
                return None
            plan = self._plan(cast(tuple[object, ...], row))
            if timestamp < plan.started_at:
                raise ValueError("stopped_at must not precede collection start")
            connection.execute(
                "UPDATE current_evidence_plans SET stopped_at = ? WHERE plan_id = ?",
                (timestamp.isoformat(), plan.plan_id),
            )
        return CollectionPlan(
            plan.plan_id,
            plan.source_scan_id,
            plan.candidate_id,
            plan.selection_cohort_id,
            plan.active_cohort_id,
            plan.active_freeze_id,
            plan.execution_instrument_id,
            plan.collector_instrument_id,
            plan.started_at,
            timestamp,
        )

    def _plan_rows(self, *, active_only: bool) -> tuple[CollectionPlan, ...]:
        if not self.path.is_file():
            return ()
        where = " WHERE stopped_at IS NULL" if active_only else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT {_PLAN_COLUMNS} FROM current_evidence_plans{where} "
                "ORDER BY started_at, plan_id"
            ).fetchall()
        return tuple(self._plan(cast(tuple[object, ...], row)) for row in rows)

    def active_targets(self) -> tuple[ResolvedCollectorInstrument, ...]:
        targets: dict[str, ResolvedCollectorInstrument] = {}
        for plan in self._plan_rows(active_only=True):
            target = resolve_frozen_instrument(
                self.workspace_root,
                active_cohort_id=plan.active_cohort_id,
                active_freeze_id=plan.active_freeze_id,
            )
            if (
                target.execution_instrument_id != plan.execution_instrument_id
                or target.collector_instrument_id != plan.collector_instrument_id
            ):
                raise ProductCurrentEvidenceError(
                    "Collection plan instrument disagrees with immutable frozen "
                    "lineage."
                )
            targets[target.collector_instrument_id] = target
        if targets:
            with self._connect() as connection:
                for target in targets.values():
                    row = connection.execute(
                        f"SELECT {_INSTRUMENT_COLUMNS} "
                        "FROM current_evidence_instruments "
                        "WHERE collector_instrument_id = ?",
                        (target.collector_instrument_id,),
                    ).fetchone()
                    if row is None:
                        raise ProductCurrentEvidenceError(
                            "Collector instrument cache is missing."
                        )
                    self._assert_cached_instrument(
                        cast(tuple[object, ...], row), target
                    )
        return tuple(
            sorted(targets.values(), key=lambda item: item.collector_instrument_id)
        )

    def all_instrument_ids(self) -> tuple[str, ...]:
        if not self.path.is_file():
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT collector_instrument_id FROM current_evidence_instruments "
                "ORDER BY collector_instrument_id"
            ).fetchall()
        return tuple(str(row[0]) for row in rows)

    def reconcile_and_claim(
        self,
        *,
        instrument_id: str,
        kind: CollectionKind,
        now: datetime | None = None,
    ) -> SlotClaim | None:
        from qap.product_current_evidence_schedule import ProductCurrentEvidenceSchedule

        return ProductCurrentEvidenceSchedule(self.workspace_root).reconcile_and_claim(
            instrument_id=instrument_id,
            kind=kind,
            now=now,
        )

    def admit_book(self, claim: SlotClaim, snapshot: PublicBookSnapshot) -> bool:
        from qap.product_current_evidence_observations import (
            ProductCurrentEvidenceObservations,
        )

        return ProductCurrentEvidenceObservations(self.workspace_root).admit_book(
            claim, snapshot
        )

    def admit_metadata(
        self,
        *,
        instrument_id: str,
        snapshot: PublicMarketMetadataSnapshot,
    ) -> bool:
        from qap.product_current_evidence_observations import (
            ProductCurrentEvidenceObservations,
        )

        return ProductCurrentEvidenceObservations(self.workspace_root).admit_metadata(
            instrument_id=instrument_id,
            snapshot=snapshot,
        )

    def metadata_needed(self, instrument_id: str) -> bool:
        from qap.product_current_evidence_observations import (
            ProductCurrentEvidenceObservations,
        )

        return ProductCurrentEvidenceObservations(self.workspace_root).metadata_needed(
            instrument_id
        )

    def evidence(self, target: ResolvedCollectorInstrument) -> PublicEvidenceBundle:
        from qap.product_current_evidence_observations import (
            ProductCurrentEvidenceObservations,
        )

        return ProductCurrentEvidenceObservations(self.workspace_root).evidence(target)

    def slot_counts(self, instrument_id: str, kind: CollectionKind) -> SlotCounts:
        from qap.product_current_evidence_schedule import ProductCurrentEvidenceSchedule

        return ProductCurrentEvidenceSchedule(self.workspace_root).slot_counts(
            instrument_id,
            kind,
        )

    def latest_observation(self, instrument_id: str) -> datetime | None:
        from qap.product_current_evidence_observations import (
            ProductCurrentEvidenceObservations,
        )

        return ProductCurrentEvidenceObservations(
            self.workspace_root
        ).latest_observation(instrument_id)

    def acquire_lease(
        self,
        *,
        pid: int | None = None,
        started_at: datetime | None = None,
    ) -> CollectorLeaseState:
        from qap.product_current_evidence_lease import ProductCurrentEvidenceLease

        with self._connect():
            pass
        return ProductCurrentEvidenceLease(self.workspace_root).acquire(
            pid=pid,
            started_at=started_at,
        )

    def heartbeat(self, *, pid: int | None = None, now: datetime | None = None) -> None:
        from qap.product_current_evidence_lease import ProductCurrentEvidenceLease

        ProductCurrentEvidenceLease(self.workspace_root).heartbeat(pid=pid, now=now)

    def release_lease(self, *, pid: int | None = None) -> None:
        from qap.product_current_evidence_lease import ProductCurrentEvidenceLease

        ProductCurrentEvidenceLease(self.workspace_root).release(pid=pid)

    def fail_lease(self, reason: str, *, pid: int | None = None) -> None:
        from qap.product_current_evidence_lease import ProductCurrentEvidenceLease

        ProductCurrentEvidenceLease(self.workspace_root).fail(reason, pid=pid)

    def lease_state(self, *, now: datetime | None = None) -> CollectorLeaseState:
        from qap.product_current_evidence_lease import ProductCurrentEvidenceLease

        if not self.path.is_file():
            return CollectorLeaseState("not_running")
        return ProductCurrentEvidenceLease(self.workspace_root).state(now=now)


__all__ = [
    "CollectionKind",
    "CollectionPlan",
    "CollectorLeaseState",
    "ProductCurrentEvidenceError",
    "ProductCurrentEvidenceStore",
    "ResolvedCollectorInstrument",
    "SlotClaim",
    "SlotCounts",
    "resolve_frozen_instrument",
    "scheduled_slot",
]
