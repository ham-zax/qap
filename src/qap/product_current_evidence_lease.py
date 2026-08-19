"""Singleton process lease for the Product current-evidence collector."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from qap.product_current_evidence import (
    CollectorLeaseState,
    CollectorStatus,
    ProductCurrentEvidenceError,
)

_LEASE_TIMEOUT = timedelta(seconds=90)


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _timestamp(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value).astimezone(UTC)


def _process_start_marker(pid: int) -> str | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    closing = raw.rfind(")")
    if closing < 0:
        return None
    fields = raw[closing + 2 :].split()
    if len(fields) <= 19:
        return None
    marker = fields[19].strip()
    return marker or None


class ProductCurrentEvidenceLease:
    """Own PID/start-marker/heartbeat state for one workspace collector."""

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
        return connection

    def acquire(
        self,
        *,
        pid: int | None = None,
        started_at: datetime | None = None,
    ) -> CollectorLeaseState:
        process_id = os.getpid() if pid is None else pid
        marker = _process_start_marker(process_id)
        if marker is None:
            raise ProductCurrentEvidenceError(
                "Collector process identity is unavailable."
            )
        timestamp = (
            datetime.now(UTC)
            if started_at is None
            else _utc(started_at, field="started_at")
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, pid, process_start_marker "
                "FROM current_evidence_collector WHERE singleton = 1"
            ).fetchone()
            if row is not None and str(row[0]) == "running" and row[1] is not None:
                existing_pid = int(row[1])
                if _process_start_marker(existing_pid) == str(row[2]):
                    raise ProductCurrentEvidenceError(
                        "Another current-evidence collector already owns this "
                        "workspace."
                    )
            connection.execute(
                "INSERT INTO current_evidence_collector "
                "(singleton, status, pid, process_start_marker, started_at, "
                "heartbeat_at, failure_reason) VALUES (1, 'running', ?, ?, ?, ?, NULL) "
                "ON CONFLICT(singleton) DO UPDATE SET status='running', "
                "pid=excluded.pid, process_start_marker=excluded.process_start_marker, "
                "started_at=excluded.started_at, heartbeat_at=excluded.heartbeat_at, "
                "failure_reason=NULL",
                (process_id, marker, timestamp.isoformat(), timestamp.isoformat()),
            )
        return self.state(now=timestamp)

    def heartbeat(
        self,
        *,
        pid: int | None = None,
        now: datetime | None = None,
    ) -> None:
        process_id = os.getpid() if pid is None else pid
        marker = _process_start_marker(process_id)
        timestamp = datetime.now(UTC) if now is None else _utc(now, field="now")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT pid, process_start_marker, status "
                "FROM current_evidence_collector WHERE singleton = 1"
            ).fetchone()
            if (
                row is None
                or str(row[2]) != "running"
                or int(row[0]) != process_id
                or str(row[1]) != marker
            ):
                raise ProductCurrentEvidenceError("Collector lease ownership was lost.")
            connection.execute(
                "UPDATE current_evidence_collector SET heartbeat_at = ? "
                "WHERE singleton = 1",
                (timestamp.isoformat(),),
            )

    def release(self, *, pid: int | None = None) -> None:
        process_id = os.getpid() if pid is None else pid
        marker = _process_start_marker(process_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT pid, process_start_marker, status "
                "FROM current_evidence_collector WHERE singleton = 1"
            ).fetchone()
            if row is None or str(row[2]) != "running":
                return
            if int(row[0]) != process_id or str(row[1]) != marker:
                raise ProductCurrentEvidenceError(
                    "Collector lease is owned by another process."
                )
            connection.execute(
                "UPDATE current_evidence_collector SET status='not_running', pid=NULL, "
                "process_start_marker=NULL, heartbeat_at=?, failure_reason=NULL "
                "WHERE singleton=1",
                (datetime.now(UTC).isoformat(),),
            )

    def fail(self, reason: str, *, pid: int | None = None) -> None:
        message = reason.strip()
        if not message:
            raise ValueError("collector failure reason must not be empty")
        process_id = os.getpid() if pid is None else pid
        with self._connect() as connection:
            row = connection.execute(
                "SELECT pid, status FROM current_evidence_collector WHERE singleton = 1"
            ).fetchone()
            if row is None or str(row[1]) != "running" or int(row[0]) != process_id:
                return
            connection.execute(
                "UPDATE current_evidence_collector "
                "SET status='failed', heartbeat_at=?, failure_reason=? "
                "WHERE singleton=1",
                (datetime.now(UTC).isoformat(), message),
            )

    def state(self, *, now: datetime | None = None) -> CollectorLeaseState:
        if not self.path.is_file():
            return CollectorLeaseState("not_running")
        current = datetime.now(UTC) if now is None else _utc(now, field="now")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT status, pid, process_start_marker, started_at, heartbeat_at, "
                "failure_reason FROM current_evidence_collector WHERE singleton = 1"
            ).fetchone()
        if row is None:
            return CollectorLeaseState("not_running")
        status = cast(CollectorStatus, str(row[0]))
        pid = None if row[1] is None else int(row[1])
        marker = None if row[2] is None else str(row[2])
        started = _timestamp(cast(str | None, row[3]))
        heartbeat = _timestamp(cast(str | None, row[4]))
        failure = None if row[5] is None else str(row[5])
        if status == "running":
            alive = (
                pid is not None
                and marker is not None
                and _process_start_marker(pid) == marker
            )
            heartbeat_fresh = (
                heartbeat is not None and current - heartbeat <= _LEASE_TIMEOUT
            )
            if not alive:
                return CollectorLeaseState(
                    "failed",
                    pid,
                    marker,
                    started,
                    heartbeat,
                    "Collector process stopped unexpectedly.",
                )
            if not heartbeat_fresh:
                return CollectorLeaseState(
                    "failed",
                    pid,
                    marker,
                    started,
                    heartbeat,
                    "Collector heartbeat is stale.",
                )
        return CollectorLeaseState(status, pid, marker, started, heartbeat, failure)


__all__ = ["ProductCurrentEvidenceLease"]
