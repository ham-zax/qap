"""Research Universe exposes per-venue refresh outcomes without losing lineage."""

# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qap.api import ApiSettings, create_app
from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.market.adapters.gate_public import GatePublicAdapter, GatePublicDataError
from qap.market.directory import CurrentSpotDirectoryObservation, CurrentSpotMarket
from qap.product_universe import ProductMarketDirectory, ProductUniverse

OLD = datetime(2026, 9, 25, tzinfo=UTC)
NEW = datetime(2026, 9, 30, tzinfo=UTC)
ENDPOINT = "/api/research-universe/directory-refresh"


def _observation(venue: str, observed_at: datetime) -> CurrentSpotDirectoryObservation:
    return CurrentSpotDirectoryObservation(
        venue=venue,
        observed_at=observed_at,
        source_id=f"{venue}-{observed_at.isoformat()}",
        source_fingerprint=("0" if observed_at == OLD else "1") * 64,
        markets=(
            CurrentSpotMarket(
                venue=venue,
                venue_symbol="BTCUSDT" if venue == "binance" else "BTC_USDT",
                venue_base_asset="BTC",
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
            ),
        ),
    )


def _client(tmp_path: Path, *, saved: bool) -> TestClient:
    run_root = tmp_path / "runs"
    if saved:
        universe = ProductUniverse(run_root)
        directory = ProductMarketDirectory.from_observations(
            (_observation("binance", OLD), _observation("gate", OLD))
        )
        universe.directory_path.parent.mkdir(parents=True)
        universe.directory_path.write_text(
            directory.model_dump_json(), encoding="utf-8"
        )
    return TestClient(create_app(ApiSettings(run_root=run_root)))


def _adapters(monkeypatch: pytest.MonkeyPatch, failed: set[str]) -> None:
    def binance(_self: BinancePublicAdapter) -> CurrentSpotDirectoryObservation:
        if "binance" in failed:
            raise BinancePublicDataError("Binance directory unavailable")
        return _observation("binance", NEW)

    def gate(_self: GatePublicAdapter) -> CurrentSpotDirectoryObservation:
        if "gate" in failed:
            raise GatePublicDataError("Gate directory unavailable")
        return _observation("gate", NEW)

    monkeypatch.setattr(BinancePublicAdapter, "fetch_spot_directory", binance)
    monkeypatch.setattr(GatePublicAdapter, "fetch_spot_directory", gate)


@pytest.mark.parametrize("failed", ["binance", "gate"])
@pytest.mark.parametrize("saved", [False, True])
def test_partial_refresh_returns_observation_and_failed_venue_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: str, saved: bool
) -> None:
    _adapters(monkeypatch, {failed})
    with _client(tmp_path, saved=saved) as client:
        before = client.get("/api/research-universe").json()

        response = client.post(ENDPOINT)

        assert response.status_code == 200
        body = response.json()
        outcomes = {item["venue"]: item for item in body["directory_refreshes"]}
        successful = "gate" if failed == "binance" else "binance"
        assert outcomes[successful]["status"] == "refreshed"
        assert outcomes[successful]["error"] is None
        assert outcomes[failed]["status"] == ("stale" if saved else "unavailable")
        assert outcomes[failed]["error"]
        assert all(item["attempted_at"].endswith("Z") for item in outcomes.values())
        sources = {item["venue"]: item for item in body["sources"]}
        assert sources[successful]["observed_at"] == "2026-09-30T00:00:00Z"
        if saved:
            assert sources[failed] == next(
                item for item in before["sources"] if item["venue"] == failed
            )
        else:
            assert failed not in sources
        assert body["directory_status"] == "observed"
        assert client.get("/api/research-universe").json() == body


@pytest.mark.parametrize("saved", [False, True])
def test_total_outage_returns_stale_saved_directory_or_502(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, saved: bool
) -> None:
    _adapters(monkeypatch, {"binance", "gate"})
    with _client(tmp_path, saved=saved) as client:
        before = client.get("/api/research-universe").json()

        response = client.post(ENDPOINT)

        assert response.status_code == (200 if saved else 502)
        if saved:
            body = response.json()
            assert body["sources"] == before["sources"]
            assert body["directory_observed_at"] == before["directory_observed_at"]
            assert {item["status"] for item in body["directory_refreshes"]} == {"stale"}
            assert client.get("/api/research-universe").json() == body
        else:
            assert (
                client.get("/api/research-universe").json()["directory_status"]
                == "not_refreshed"
            )
