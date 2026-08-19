import os
from pathlib import Path

from fastapi.testclient import TestClient

from qap.api import ApiSettings, create_app
from qap.api.operations import (
    OperationKind,
    OperationStatus,
    OperationWorkerSettings,
    process_start_marker,
)


def test_scanner_workbench_empty_reads_expose_frozen_protocol(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    client = TestClient(app)

    protocol = client.get("/api/scanner/protocol")
    scans = client.get("/api/scans")
    cohorts = client.get("/api/forward/cohorts")
    baskets = client.get("/api/baskets")
    operations = client.get("/api/operations")

    assert protocol.status_code == 200
    assert protocol.json()["protocol_id"] == "scanner-v1-s1"
    assert protocol.json()["venues"] == ["binance", "gate"]
    assert scans.status_code == 200 and scans.json()["items"] == []
    assert cohorts.status_code == 200 and cohorts.json()["items"] == []
    assert baskets.status_code == 200 and baskets.json()["items"] == []
    assert operations.status_code == 200 and operations.json()["items"] == []


def test_mutation_is_serial_while_reads_remain_available(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    app = create_app(
        ApiSettings(
            run_root=run_root,
            market_data_root=tmp_path / "data",
            repository_root=Path.cwd(),
        )
    )
    manager = app.state.operation_manager
    marker = process_start_marker(os.getpid())
    assert marker is not None
    request = manager.store.reserve(
        kind=OperationKind.RUN_SCAN,
        request_summary={"probe": "active"},
        settings=OperationWorkerSettings(
            run_root=str(run_root),
            data_root=str(tmp_path / "data"),
            capture_root=str(run_root / "public-capture"),
            repository_root=str(Path.cwd()),
        ),
    )
    manager.store.attach_worker(request.operation_id, pid=os.getpid(), marker=marker)

    client = TestClient(app)
    assert client.get("/api/scans").status_code == 200
    blocked = client.post(
        "/api/scans",
        json={"as_of": "2026-08-19T00:00:00Z", "horizons": ["short"]},
    )

    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "operation_busy"
    assert blocked.json()["error"]["context"]["operation_id"] == request.operation_id


def test_orphaned_running_operation_becomes_interrupted(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    app = create_app(ApiSettings(run_root=run_root))
    manager = app.state.operation_manager
    request = manager.store.reserve(
        kind=OperationKind.RUN_SCAN,
        request_summary={"probe": "orphan"},
        settings=OperationWorkerSettings(
            run_root=str(run_root),
            data_root=None,
            capture_root=str(run_root / "public-capture"),
            repository_root=None,
        ),
    )

    manager.store.reconcile_running()
    state = manager.store.read_state(request.operation_id)

    assert state.status is OperationStatus.INTERRUPTED
    assert state.failure_code == "worker_interrupted"
