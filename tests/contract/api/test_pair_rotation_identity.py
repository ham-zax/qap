"""Binance Lab identity requires acquired evidence, never familiar coin symbols."""

import json
from datetime import timedelta
from math import exp, sin
from pathlib import Path
from typing import Literal

import httpx
import pytest
from fastapi.testclient import TestClient

from qap.api.app import create_app
from qap.api.settings import ApiSettings
from qap.asset_registry_coingecko import CoinGeckoRegistry
from qap.market import BarInterval, MarketBar, validate_bar_series
from qap.market.adapters.spot_directory import binance_directory_from_payload
from qap.product_market_data import ProductMarketData
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataUpstreamSource,
)
from qap.product_market_data_prepare import product_dataset_id
from qap.product_universe import ProductMarketDirectory, ProductUniverse

from .pair_rotation_support import NOW
from .test_lab_studies import publish_lab_metadata

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "registry"
PAIR = ("binance:BTC", "binance:ETH")
QUERY = {"coin_a": PAIR[0], "coin_b": PAIR[1], "bar": "1h", "days": 30}
Evidence = Literal["missing", "rate_limited", "coins_only", "flagged", "recorded"]


def _universe(root: Path) -> ProductUniverse:
    payload = json.loads((FIXTURES / "binance_case_exchange_info.json").read_text())
    directory = ProductMarketDirectory.from_observations(
        (binance_directory_from_payload(payload, observed_at=NOW),)
    )
    directory = directory.model_copy(
        update={
            "markets": tuple(
                market
                for market in directory.markets
                if market.venue_base_asset in ("BTC", "ETH")
                and market.venue_quote_asset == "USDT"
            )
        }
    )
    owner = ProductUniverse(root / "runs")
    owner.root.mkdir(parents=True)
    owner.directory_path.write_text(directory.model_dump_json())
    return owner


def _registry_transport(evidence: Evidence, requests: list[str]) -> httpx.MockTransport:
    responses = json.loads((FIXTURES / "coingecko_case_responses.json").read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        assert evidence != "missing", "Missing evidence must not trigger a GET fetch"
        key = request.url.raw_path.decode().removeprefix("/api/v3/")
        requests.append(key)
        if evidence == "rate_limited":
            return httpx.Response(429)
        if evidence == "coins_only" and "tickers" in key:
            return httpx.Response(200, json={"tickers": []})
        if evidence == "flagged" and key.startswith("exchanges/binance/"):
            for row in responses[key]["tickers"]:
                if row["base"] == "BTC":
                    row["is_stale"] = True
        return httpx.Response(200, json=responses[key])

    return httpx.MockTransport(handler)


def _configure_registry(
    monkeypatch: pytest.MonkeyPatch, evidence: Evidence
) -> list[str]:
    requests: list[str] = []
    transport = _registry_transport(evidence, requests)

    def registry(cache_path: Path) -> CoinGeckoRegistry:
        return CoinGeckoRegistry(
            cache_path,
            demo_key="",
            transport=transport,
            pacing_seconds=0,
            retries=0,
            now=lambda: NOW,
        )

    monkeypatch.setattr("qap.product_universe.CoinGeckoRegistry", registry)
    return requests


def _prepare_client(owner: ProductUniverse, root: Path) -> TestClient:
    """Synthetic prices isolate identity from market movement and acquisition."""
    scope = owner.research_scope(PAIR)
    data = ProductMarketData(owner.workspace_root, root)
    interval = BarInterval("1h")
    end = NOW.replace(minute=0, second=0, microsecond=0)
    for leg, instrument in enumerate(scope.instruments):
        bars: list[MarketBar] = []
        for index in range(720):
            movement = (
                0.04 * sin(index * 0.3) if leg == 0 else 0.003 * sin(index * 0.17)
            )
            price = exp(index * 0.0001 + movement)
            bars.append(
                MarketBar(
                    instrument=instrument.instrument,
                    interval=interval,
                    candle_open_time=end - timedelta(hours=720 - index),
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1_000_000.0,
                )
            )
        data.publish_generation(
            scope,
            MarketDataGenerationInput(
                dataset_id=product_dataset_id(instrument, interval),
                resolved_instrument=instrument,
                series=validate_bar_series(tuple(bars)),
                acquisition_implementation="offline-identity-contract",
                upstream_sources=(
                    MarketDataUpstreamSource(
                        provider="binance",
                        source_family="offline-contract",
                        source_id=instrument.instrument.venue_symbol,
                        retrieved_at=NOW,
                        source_fingerprint="1" * 64,
                    ),
                ),
            ),
        )
    publish_lab_metadata(root, scope.instruments)
    return TestClient(
        create_app(ApiSettings(run_root=owner.workspace_root, market_data_root=root))
    )


@pytest.mark.parametrize(
    "evidence,confirmed",
    [
        ("missing", False),
        ("rate_limited", False),
        ("coins_only", False),
        ("flagged", False),
        ("recorded", True),
    ],
)
def test_binance_analysis_and_study_require_accepted_venue_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    evidence: Evidence,
    confirmed: bool,
) -> None:
    owner = _universe(tmp_path)
    requests = _configure_registry(monkeypatch, evidence)
    if evidence != "missing":
        refresh = owner.refresh_identity_evidence()
        if evidence == "rate_limited":
            assert refresh.status == "unavailable"
            assert refresh.failure == "rate_limited"
            assert not (owner.root / "asset-registry.json").exists()
        else:
            assert refresh.status == "refreshed"
            assert refresh.snapshot is not None and refresh.snapshot.sources
    scope = owner.research_scope(PAIR)
    assert scope.economic_identity_confirmed is confirmed
    assert scope.approved_assets == ()
    if confirmed:
        assert tuple(item.instrument.base.key for item in scope.instruments) == (
            "BTC",
            "ETH",
        )
        bindings = {
            item.venue_asset_code: item for item in owner.read_state().identity_mappings
        }
        for code, coin_id in (("BTC", "bitcoin"), ("ETH", "ethereum")):
            assert bindings[code].registry_coin_id == coin_id
            assert bindings[code].accepted_by == "policy"
            assert bindings[code].evidence_fingerprint
            assert bindings[code].asset_identity_version.startswith("registry-v1-")

    client = _prepare_client(owner, tmp_path)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    acquisitions = list(requests)
    response = client.get("/api/pair-rotation/analysis", params=QUERY)
    assert response.status_code == 200, response.text
    assert response.json()["identity_confirmed"] is confirmed
    after = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after

    study = client.post(
        "/api/pair-rotation/studies",
        json=QUERY | {"settings": {"lookback": 40, "auto_tune": False, "entry": 1.0}},
    )
    assert study.status_code == 200, study.text
    result = study.json()["result"]
    assert len(result["folds"]) == 8
    assert result["trades"]
    if confirmed:
        assert result["call"]["status"] not in (
            "identity_unresolved",
            "execution_data_missing",
            "insufficient_history",
        )
    else:
        assert result["call"]["status"] == "identity_unresolved"
    assert requests == acquisitions
    assert owner.read_state().approved_asset_ids == ()


def test_registry_acceptance_requires_new_data_without_relabeling_old_prices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _universe(tmp_path)
    client = _prepare_client(owner, tmp_path)
    prices = {path: path.read_bytes() for path in tmp_path.rglob("*.parquet")}
    assert prices
    before = client.get("/api/pair-rotation/analysis", params=QUERY)
    assert before.status_code == 200, before.text
    assert before.json()["identity_confirmed"] is False

    _configure_registry(monkeypatch, "recorded")
    assert owner.refresh_identity_evidence().status == "refreshed"
    response = client.get("/api/pair-rotation/analysis", params=QUERY)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pair_rotation_analysis_unavailable"
    assert {path: path.read_bytes() for path in prices} == prices

    client = _prepare_client(owner, tmp_path)
    response = client.get("/api/pair-rotation/analysis", params=QUERY)
    assert response.status_code == 200, response.text
    assert response.json()["identity_confirmed"] is True
    assert {path: path.read_bytes() for path in prices} == prices
