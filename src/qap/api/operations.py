"""Minimal durable lifecycle for local browser-triggered research operations."""

import os
import subprocess
import sys
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from qap.api.errors import ApiBoundaryError
from qap.api.scanner_schemas import OperationDto, OperationListDto, OperationRefDto
from qap.api.schemas import ErrorDetailDto
from qap.api.settings import ApiSettings
from qap.process_identity import process_start_marker

_REQUEST_FILE = "request.json"
_STATUS_FILE = "status.json"
_WORKER_LOG = "worker.log"


class OperationKind(StrEnum):
    RUN_SCAN = "run_scan"
    RUN_RESEARCH_RECIPE = "run_research_recipe"
    GENERATE_ASSET_MOMENTUM = "generate_asset_momentum"
    FREEZE_FORWARD_COHORT = "freeze_forward_cohort"
    ADVANCE_FORWARD_COHORT = "advance_forward_cohort"
    CAPTURE_PUBLIC_EVIDENCE = "capture_public_evidence"
    QUALIFY_CANDIDATE = "qualify_candidate"
    RUN_BASKET = "run_basket"


class OperationStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OperationWorkerSettings(_FrozenModel):
    run_root: str
    data_root: str | None
    capture_root: str
    repository_root: str | None


class OperationRequestRecord(_FrozenModel):
    schema_version: str = "qap.api.operation-request.v1"
    operation_id: str
    kind: OperationKind
    requested_at: datetime
    request_summary: dict[str, JsonValue]
    settings: OperationWorkerSettings


class OperationStateRecord(_FrozenModel):
    schema_version: str = "qap.api.operation-status.v1"
    operation_id: str
    kind: OperationKind
    status: OperationStatus
    requested_at: datetime
    started_at: datetime
    finished_at: datetime | None = None
    result: dict[str, JsonValue] | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    worker_pid: int | None = None
    process_start_marker: str | None = None


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _json_bytes(model: BaseModel) -> bytes:
    return (model.model_dump_json() + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class OperationStore:
    """Durable request/status records under one operational namespace."""

    def __init__(self, run_root: Path) -> None:
        self.root = run_root.resolve() / "web-operations"

    def _directory(self, operation_id: str) -> Path:
        normalized = operation_id.strip().lower()
        try:
            if str(UUID(normalized)) != normalized:
                raise ValueError
        except ValueError as exc:
            raise _operation_not_found(operation_id) from exc
        directory = self.root / normalized
        if not directory.is_dir():
            raise _operation_not_found(normalized)
        return directory

    @staticmethod
    def _read_state_path(path: Path) -> OperationStateRecord:
        try:
            return OperationStateRecord.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            raise ApiBoundaryError(
                code="operation_state_invalid",
                message="Operation state is invalid.",
                status_code=409,
                context={},
            ) from exc

    def read_request(self, operation_id: str) -> OperationRequestRecord:
        path = self._directory(operation_id) / _REQUEST_FILE
        try:
            return OperationRequestRecord.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            raise ApiBoundaryError(
                code="operation_request_invalid",
                message="Operation request is invalid.",
                status_code=409,
                context={"operation_id": operation_id},
            ) from exc

    def read_state(self, operation_id: str) -> OperationStateRecord:
        directory = self._directory(operation_id)
        return self._read_state_path(directory / _STATUS_FILE)

    def reserve(
        self,
        *,
        kind: OperationKind,
        request_summary: dict[str, JsonValue],
        settings: OperationWorkerSettings,
    ) -> OperationRequestRecord:
        self.root.mkdir(parents=True, exist_ok=True)
        operation_id = str(uuid4())
        directory = self.root / operation_id
        directory.mkdir()
        requested_at = _utc_now()
        request = OperationRequestRecord(
            operation_id=operation_id,
            kind=kind,
            requested_at=requested_at,
            request_summary=request_summary,
            settings=settings,
        )
        state = OperationStateRecord(
            operation_id=operation_id,
            kind=kind,
            status=OperationStatus.RUNNING,
            requested_at=requested_at,
            started_at=requested_at,
        )
        try:
            _atomic_write(directory / _REQUEST_FILE, _json_bytes(request))
            _atomic_write(directory / _STATUS_FILE, _json_bytes(state))
        except OSError:
            for path in directory.iterdir():
                path.unlink(missing_ok=True)
            directory.rmdir()
            raise
        return request

    def update_state(self, state: OperationStateRecord) -> None:
        directory = self._directory(state.operation_id)
        _atomic_write(directory / _STATUS_FILE, _json_bytes(state))

    def attach_worker(self, operation_id: str, *, pid: int, marker: str) -> None:
        current = self.read_state(operation_id)
        if current.status is not OperationStatus.RUNNING:
            return
        self.update_state(
            current.model_copy(
                update={"worker_pid": pid, "process_start_marker": marker}
            )
        )

    def finish(
        self,
        operation_id: str,
        *,
        status: OperationStatus,
        result: dict[str, JsonValue] | None = None,
        failure_code: str | None = None,
        failure_message: str | None = None,
    ) -> None:
        if status is OperationStatus.RUNNING:
            raise ValueError("terminal operation update requires terminal status")
        current = self.read_state(operation_id)
        if current.status is not OperationStatus.RUNNING:
            return
        self.update_state(
            current.model_copy(
                update={
                    "status": status,
                    "finished_at": _utc_now(),
                    "result": result,
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                }
            )
        )

    def _directories(self) -> tuple[Path, ...]:
        if not self.root.is_dir():
            return ()
        return tuple(
            path
            for path in sorted(self.root.iterdir())
            if path.is_dir() and not path.name.startswith(".")
        )

    def reconcile_running(self) -> None:
        for directory in self._directories():
            try:
                state = self._read_state_path(directory / _STATUS_FILE)
            except ApiBoundaryError:
                continue
            if state.status is not OperationStatus.RUNNING:
                continue
            marker = (
                None
                if state.worker_pid is None
                else process_start_marker(state.worker_pid)
            )
            if (
                state.worker_pid is not None
                and state.process_start_marker is not None
                and marker == state.process_start_marker
            ):
                continue
            self.finish(
                state.operation_id,
                status=OperationStatus.INTERRUPTED,
                failure_code="worker_interrupted",
                failure_message="Operation worker is no longer running.",
            )

    def list_states(self) -> tuple[OperationStateRecord, ...]:
        states: list[OperationStateRecord] = []
        for directory in self._directories():
            try:
                states.append(self._read_state_path(directory / _STATUS_FILE))
            except ApiBoundaryError:
                continue
        states.sort(
            key=lambda item: (item.requested_at, item.operation_id),
            reverse=True,
        )
        return tuple(states)

    def active(self) -> OperationStateRecord | None:
        return next(
            (
                state
                for state in self.list_states()
                if state.status is OperationStatus.RUNNING
            ),
            None,
        )

    def log_path(self, operation_id: str) -> Path:
        return self._directory(operation_id) / _WORKER_LOG


class OperationManager:
    """Serialize mutation launches and project durable operation state."""

    def __init__(self, settings: ApiSettings) -> None:
        self.settings = settings
        self.store = OperationStore(settings.run_root)
        self._launch_lock = Lock()
        with self._launch_lock:
            self.store.reconcile_running()

    def _worker_settings(self, kind: OperationKind) -> OperationWorkerSettings:
        data_required = kind is not OperationKind.CAPTURE_PUBLIC_EVIDENCE
        if data_required and self.settings.market_data_root is None:
            raise ApiBoundaryError(
                code="operation_unavailable",
                message="Market data root is not configured.",
                status_code=409,
                context={"operation": kind.value},
            )
        repository_required = kind in {
            OperationKind.RUN_SCAN,
            OperationKind.RUN_RESEARCH_RECIPE,
            OperationKind.ADVANCE_FORWARD_COHORT,
            OperationKind.QUALIFY_CANDIDATE,
            OperationKind.RUN_BASKET,
        }
        if repository_required and self.settings.repository_root is None:
            raise ApiBoundaryError(
                code="operation_unavailable",
                message="Repository root is not configured.",
                status_code=409,
                context={"operation": kind.value},
            )
        capture_root = self.settings.capture_root or (
            self.settings.run_root / "public-capture"
        )
        return OperationWorkerSettings(
            run_root=str(self.settings.run_root),
            data_root=(
                None
                if self.settings.market_data_root is None
                else str(self.settings.market_data_root)
            ),
            capture_root=str(capture_root),
            repository_root=(
                None
                if self.settings.repository_root is None
                else str(self.settings.repository_root)
            ),
        )

    def submit(
        self,
        kind: OperationKind,
        request_summary: dict[str, JsonValue],
    ) -> OperationRefDto:
        with self._launch_lock:
            self.store.reconcile_running()
            active = self.store.active()
            if active is not None:
                raise ApiBoundaryError(
                    code="operation_busy",
                    message="Another research operation is already running.",
                    status_code=409,
                    context={"operation_id": active.operation_id},
                )
            request = self.store.reserve(
                kind=kind,
                request_summary=request_summary,
                settings=self._worker_settings(kind),
            )
            log_path = self.store.log_path(request.operation_id)
            try:
                with log_path.open("ab") as log:
                    process = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "qap.api.operation_worker",
                            str(self.settings.run_root),
                            request.operation_id,
                        ],
                        cwd=(
                            None
                            if self.settings.repository_root is None
                            else self.settings.repository_root
                        ),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                marker = process_start_marker(process.pid)
                if marker is None:
                    process.terminate()
                    raise RuntimeError("worker process identity is unavailable")
                self.store.attach_worker(
                    request.operation_id,
                    pid=process.pid,
                    marker=marker,
                )
            except (OSError, RuntimeError) as exc:
                self.store.finish(
                    request.operation_id,
                    status=OperationStatus.FAILED,
                    failure_code="worker_spawn_failed",
                    failure_message="Operation worker could not be started.",
                )
                raise ApiBoundaryError(
                    code="operation_start_failed",
                    message="Operation worker could not be started.",
                    status_code=500,
                    context={"operation_id": request.operation_id},
                ) from exc
            return OperationRefDto(operation_id=request.operation_id)

    @staticmethod
    def _dto(
        request: OperationRequestRecord,
        state: OperationStateRecord,
    ) -> OperationDto:
        failure = None
        if state.failure_code is not None:
            failure = ErrorDetailDto(
                code=state.failure_code,
                message=state.failure_message or "Operation failed.",
                context={},
            )
        return OperationDto(
            operation_id=state.operation_id,
            kind=state.kind.value,
            status=state.status.value,
            requested_at=state.requested_at,
            started_at=state.started_at,
            finished_at=state.finished_at,
            request_summary=request.request_summary,
            result=state.result,
            failure=failure,
        )

    def get(self, operation_id: str) -> OperationDto:
        with self._launch_lock:
            self.store.reconcile_running()
            state = self.store.read_state(operation_id)
            request = self.store.read_request(operation_id)
        return self._dto(request, state)

    def list(self) -> OperationListDto:
        with self._launch_lock:
            self.store.reconcile_running()
            states = self.store.list_states()
            items = tuple(
                self._dto(self.store.read_request(state.operation_id), state)
                for state in states
            )
        return OperationListDto(items=items)


def _operation_not_found(operation_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="operation_not_found",
        message="Operation was not found.",
        status_code=404,
        context={"operation_id": operation_id},
    )


__all__ = [
    "OperationKind",
    "OperationManager",
    "OperationRequestRecord",
    "OperationStateRecord",
    "OperationStatus",
    "OperationStore",
    "process_start_marker",
]
