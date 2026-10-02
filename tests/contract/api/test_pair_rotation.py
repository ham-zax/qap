"""The Pair Rotation API opens immutable data without identity/admission screens."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from qap.api import ApiSettings, create_app
from qap.api.operation_worker import run
from qap.api.operations import OperationManager, OperationStatus
from qap.asset_registry import RegistryRefreshResult
from qap.product_market_data import ProductMarketData
from qap.product_market_data_binance import BinanceHistoricalAcquisitionError
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    ProductMarketDataProjection,
)
from qap.product_pair_rotation_data import PairRotationData, ProgressCallback
from qap.product_universe import ProductResearchScope, ProductUniverse

from .pair_rotation_support import NOW, OfflineBinance, publish_directory


class WorkerProcess:
    pid = os.getpid()


def api_settings(client: TestClient) -> ApiSettings:
    return cast(ApiSettings, cast(FastAPI, client.app).state.settings)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def spawn(*args: object, **kwargs: object) -> WorkerProcess:
        return WorkerProcess()

    def registry_unavailable(self: object) -> RegistryRefreshResult:
        return RegistryRefreshResult(status="unavailable", failure="network_error")

    monkeypatch.setattr("qap.api.operations.subprocess.Popen", spawn)
    monkeypatch.setattr(
        "qap.product_universe.CoinGeckoRegistry.refresh",
        registry_unavailable,
    )
    return TestClient(
        create_app(
            ApiSettings(
                run_root=tmp_path / "runs",
                market_data_root=tmp_path / "data",
            )
        )
    )


@pytest.mark.parametrize("query", ["Wormhole", "W", "W/USDT", "W_USDT", "WUSDT"])
def test_search_aliases_and_eligibility(client: TestClient, query: str) -> None:
    owner = ProductUniverse(api_settings(client).run_root)
    publish_directory(owner)
    response = client.get("/api/pair-rotation/coins", params={"q": query})
    assert response.status_code == 200
    assert response.json()["coins"][0]["listing_id"] == "binance:W"
    rows = client.get("/api/pair-rotation/coins").json()["coins"]
    assert {row["listing_id"] for row in rows} == {"binance:BTC", "binance:W"}
    assert not owner.read_state().approved_asset_ids
    assert not owner.state_path.exists()


def test_empty_workspace_opens_year_of_data_with_durable_progress(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = api_settings(client)
    fake = OfflineBinance()
    # Keep the recorded cutoff independent of the test execution date.
    prepare = PairRotationData.prepare

    def prepare_at_recorded_time(
        self: PairRotationData,
        scope: ProductResearchScope,
        *,
        lookback_days: int = 365,
        progress: ProgressCallback | None = None,
    ) -> ProductMarketDataProjection:
        return prepare(
            self, scope, now=NOW, lookback_days=lookback_days, progress=progress
        )

    monkeypatch.setattr(PairRotationData, "prepare", prepare_at_recorded_time)
    monkeypatch.setattr(ProductUniverse, "refresh_directory", publish_directory)
    monkeypatch.setattr(
        "qap.product_pair_rotation_data.BinanceHistoricalAcquirer", lambda: fake
    )
    command = {"coin_a": "binance:W", "coin_b": "binance:BTC"}
    assert (
        client.get("/api/pair-rotation/coins").json()["directory_status"]
        == "not_refreshed"
    )
    opened = client.post("/api/pair-rotation/open", json=command)
    assert opened.status_code == 202
    operation_id = opened.json()["operation_id"]
    before = client.get(f"/api/operations/{operation_id}").json()
    assert before["progress"] == {"stage": "queued", "completed": 0, "total": 8}
    assert (
        client.post("/api/pair-rotation/open", json=command).json()["operation_id"]
        == operation_id
    )
    assert run(settings.run_root, operation_id) == 0
    result = client.get(f"/api/operations/{operation_id}").json()
    assert result["status"] == "completed"
    assert result["progress"] == {"stage": "data ready", "completed": 8, "total": 8}
    assert not result["result"]["identity_confirmed"]
    assert result["result"]["registry_status"] == "unavailable"
    assert len(result["result"]["datasets"]) == 8
    assert {row["interval"] for row in result["result"]["datasets"]} == {
        "15m",
        "1h",
        "4h",
        "1d",
    }
    assert len(fake.windows) == 2
    assert all((end - start).days >= 365 for start, end in fake.windows)
    assert ProductUniverse(settings.run_root).read_state().approved_asset_ids == ()
    # A reloaded API projects the same persisted result; reopening reuses current data.
    reloaded = TestClient(create_app(settings))
    assert reloaded.get(f"/api/operations/{operation_id}").json() == result
    second_id = reloaded.post("/api/pair-rotation/open", json=command).json()[
        "operation_id"
    ]
    assert run(settings.run_root, second_id) == 0
    assert len(fake.windows) == 2


def test_failed_download_is_typed_and_retryable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = api_settings(client)
    publish_directory(ProductUniverse(settings.run_root))

    class FailingBinance(OfflineBinance):
        def acquire_generation_input(
            self, **kwargs: object
        ) -> MarketDataGenerationInput:
            raise BinanceHistoricalAcquisitionError("offline outage")

    monkeypatch.setattr(
        "qap.product_pair_rotation_data.BinanceHistoricalAcquirer", FailingBinance
    )
    command = {"coin_a": "binance:W", "coin_b": "binance:BTC"}
    operation_id = client.post("/api/pair-rotation/open", json=command).json()[
        "operation_id"
    ]
    assert run(settings.run_root, operation_id) == 1
    state = client.get(f"/api/operations/{operation_id}").json()
    assert state["status"] == "failed"
    assert state["failure"]["code"] == "pair_rotation_data_unavailable"
    assert "offline outage" in state["failure"]["message"]
    assert (
        ProductMarketData(settings.run_root, settings.market_data_root)
        .projection()
        .maintenance.status
        == "failed"
    )
    retry = client.post("/api/pair-rotation/open", json=command)
    assert retry.status_code == 202 and retry.json()["operation_id"] != operation_id
    manager = cast(OperationManager, cast(FastAPI, client.app).state.operation_manager)
    manager.store.finish(
        retry.json()["operation_id"], status=OperationStatus.INTERRUPTED
    )


@pytest.mark.parametrize(
    "command",
    [
        {"coin_a": "binance:W", "coin_b": "binance:w"},
        {"coin_a": "gate:W", "coin_b": "binance:BTC"},
        {"coin_a": "binance:W", "coin_b": "binance:BTC", "lookback_days": 30},
    ],
)
def test_invalid_pair_request_is_rejected(
    client: TestClient, command: dict[str, str | int]
) -> None:
    assert client.post("/api/pair-rotation/open", json=command).status_code == 422


def test_sample_workspace_cannot_download(tmp_path: Path) -> None:
    publish_directory(ProductUniverse(tmp_path))
    state_path = tmp_path / "product/research-universe.json"
    sample = TestClient(
        create_app(ApiSettings(run_root=tmp_path, workspace_mode="sample"))
    )
    for endpoint, command in (
        ("bootstrap", {}),
        ("open", {"coin_a": "binance:W", "coin_b": "binance:BTC"}),
    ):
        response = sample.post(f"/api/pair-rotation/{endpoint}", json=command)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "pair_rotation_read_only"
    assert sample.get("/api/pair-rotation/coins").status_code == 200
    assert not state_path.exists()


def test_concurrent_api_instances_reuse_one_running_intent(client: TestClient) -> None:
    settings = api_settings(client)
    other = TestClient(create_app(settings))
    command = {"coin_a": "binance:W", "coin_b": "binance:BTC"}

    def open_pair(current: TestClient) -> str:
        response = current.post("/api/pair-rotation/open", json=command)
        assert response.status_code == 202
        return str(response.json()["operation_id"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = tuple(pool.map(open_pair, (client, other)))
    assert len(set(ids)) == 1
    assert len(client.get("/api/operations").json()["items"]) == 1
    blocked = other.post(
        "/api/pair-rotation/open",
        json={
            "coin_a": "binance:BTC",
            "coin_b": "binance:W",
        },
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "operation_busy"
    manager = cast(OperationManager, cast(FastAPI, client.app).state.operation_manager)
    manager.store.update_progress(ids[0], "download", 1, 8)
    marker = manager.store.read_state(ids[0]).process_start_marker
    assert marker is not None
    # Progress and worker attachment must preserve each other's persisted fields.
    manager.store.attach_worker(ids[0], pid=os.getpid(), marker=marker)
    projected = other.get(f"/api/operations/{ids[0]}").json()
    assert projected["progress"] == {"stage": "download", "completed": 1, "total": 8}
    manager.store.finish(ids[0], status=OperationStatus.COMPLETED, result={})
    manager.store.update_progress(ids[0], "late", 8, 8)
    assert manager.store.read_state(ids[0]).progress == projected["progress"]
