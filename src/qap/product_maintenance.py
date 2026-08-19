"""Bounded SQLite state for Product market-data maintenance."""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

MaintenanceKind = Literal["prepare_market_data", "refresh_market_data"]
MaintenanceStatus = Literal["idle", "running", "failed"]


class ProductMaintenanceError(RuntimeError):
    """Raised when persisted Product maintenance state is invalid."""


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


class MarketDataMaintenanceState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    status: MaintenanceStatus = "idle"
    kind: MaintenanceKind | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failure_reason: str | None = None

    @field_validator("started_at", "finished_at")
    @classmethod
    def validate_optional_timestamp(
        cls,
        value: datetime | None,
        info: object,
    ) -> datetime | None:
        if value is None:
            return None
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("failure_reason")
    @classmethod
    def validate_failure_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("failure_reason must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.status == "idle":
            if (
                self.kind is not None
                or self.started_at is not None
                or self.finished_at is not None
                or self.failure_reason is not None
            ):
                raise ValueError("idle maintenance state must not describe active work")
            return self
        if self.kind is None or self.started_at is None:
            raise ValueError("non-idle maintenance state requires kind and started_at")
        if self.status == "running" and (
            self.finished_at is not None or self.failure_reason is not None
        ):
            raise ValueError("running maintenance state cannot be finished or failed")
        if self.status == "failed" and (
            self.finished_at is None or self.failure_reason is None
        ):
            raise ValueError("failed maintenance state requires finish time and reason")
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("maintenance finish time cannot precede start time")
        return self


class MarketDataMaintenanceStore:
    """Single-row Product maintenance state; not a generic operation queue."""

    def __init__(self, workspace_root: Path) -> None:
        self.path = (
            workspace_root.expanduser().resolve() / "product" / "product-state.sqlite3"
        )
        self._lock = Lock()

    def _connection(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_data_maintenance (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                status TEXT NOT NULL,
                kind TEXT,
                started_at TEXT,
                finished_at TEXT,
                failure_reason TEXT
            )
            """
        )
        return connection

    def read(self) -> MarketDataMaintenanceState:
        if not self.path.is_file():
            return MarketDataMaintenanceState()
        with sqlite3.connect(self.path) as connection:
            table = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'market_data_maintenance'"
            ).fetchone()
            if table is None:
                return MarketDataMaintenanceState()
            row = connection.execute(
                "SELECT status, kind, started_at, finished_at, failure_reason "
                "FROM market_data_maintenance WHERE singleton = 1"
            ).fetchone()
        if row is None:
            return MarketDataMaintenanceState()
        status, kind, started_at, finished_at, failure_reason = cast(
            tuple[str, str | None, str | None, str | None, str | None],
            row,
        )
        try:
            return MarketDataMaintenanceState(
                status=cast(MaintenanceStatus, status),
                kind=cast(MaintenanceKind | None, kind),
                started_at=(
                    None if started_at is None else datetime.fromisoformat(started_at)
                ),
                finished_at=(
                    None if finished_at is None else datetime.fromisoformat(finished_at)
                ),
                failure_reason=failure_reason,
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise ProductMaintenanceError(
                "Market-data maintenance state is invalid."
            ) from exc

    def _write(self, state: MarketDataMaintenanceState) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO market_data_maintenance
                    (singleton, status, kind, started_at, finished_at, failure_reason)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    status = excluded.status,
                    kind = excluded.kind,
                    started_at = excluded.started_at,
                    finished_at = excluded.finished_at,
                    failure_reason = excluded.failure_reason
                """,
                (
                    state.status,
                    state.kind,
                    None if state.started_at is None else state.started_at.isoformat(),
                    None
                    if state.finished_at is None
                    else state.finished_at.isoformat(),
                    state.failure_reason,
                ),
            )

    def start(
        self,
        kind: MaintenanceKind,
        *,
        started_at: datetime | None = None,
    ) -> MarketDataMaintenanceState:
        timestamp = (
            datetime.now(UTC)
            if started_at is None
            else _utc(
                started_at,
                field="started_at",
            )
        )
        with self._lock:
            if self.read().status == "running":
                raise ProductMaintenanceError(
                    "Market-data maintenance is already running."
                )
            state = MarketDataMaintenanceState(
                status="running",
                kind=kind,
                started_at=timestamp,
            )
            self._write(state)
            return state

    def finish(self) -> MarketDataMaintenanceState:
        with self._lock:
            if self.read().status != "running":
                raise ProductMaintenanceError("No market-data maintenance is running.")
            state = MarketDataMaintenanceState()
            self._write(state)
            return state

    def fail(
        self,
        reason: str,
        *,
        finished_at: datetime | None = None,
    ) -> MarketDataMaintenanceState:
        failure_reason = reason.strip()
        if not failure_reason:
            raise ValueError("failure_reason must not be empty")
        timestamp = (
            datetime.now(UTC)
            if finished_at is None
            else _utc(
                finished_at,
                field="finished_at",
            )
        )
        with self._lock:
            current = self.read()
            if (
                current.status != "running"
                or current.kind is None
                or current.started_at is None
            ):
                raise ProductMaintenanceError("No market-data maintenance is running.")
            state = MarketDataMaintenanceState(
                status="failed",
                kind=current.kind,
                started_at=current.started_at,
                finished_at=timestamp,
                failure_reason=failure_reason,
            )
            self._write(state)
            return state


__all__ = [
    "MaintenanceKind",
    "MarketDataMaintenanceState",
    "MarketDataMaintenanceStore",
    "ProductMaintenanceError",
]
