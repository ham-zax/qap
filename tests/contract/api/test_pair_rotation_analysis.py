"""Analysis reads sealed data without preparing or changing identity state."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qap.api.app import create_app
from qap.api.settings import ApiSettings
from qap.product_market_data import ProductMarketData
from qap.product_pair_rotation_data import PairRotationData
from qap.product_universe import ProductUniverse

from .pair_rotation_support import NOW, OfflineBinance, publish_directory


@pytest.fixture
def prepared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[TestClient, Path]:
    settings = ApiSettings(
        run_root=tmp_path / "runs", market_data_root=tmp_path / "data"
    )
    owner = ProductUniverse(settings.run_root)
    publish_directory(owner)
    fake = OfflineBinance()
    monkeypatch.setattr(
        "qap.product_pair_rotation_data.BinanceHistoricalAcquirer", lambda: fake
    )
    scope = owner.research_scope(("binance:W", "binance:BTC"))
    data = ProductMarketData(settings.run_root, settings.market_data_root)
    PairRotationData(owner, data).prepare(scope, now=NOW)
    return TestClient(create_app(settings)), tmp_path


def test_analysis_matches_exact_data_and_does_not_write(
    prepared: tuple[TestClient, Path],
) -> None:
    client, root = prepared
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    response = client.get(
        "/api/pair-rotation/analysis",
        params={
            "coin_a": "binance:W",
            "coin_b": "binance:BTC",
            "bar": "1h",
            "days": 30,
            "band_lookback": 20,
            "anchor": "binance:BTC",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_version"] == "qap.api.pair-rotation-analysis.v1"
    assert body["bars_used"] == 30 * 24
    assert body["identity_confirmed"] is False
    assert body["series"]["ratio"] == [1.0] * 720
    assert body["series"]["mean"][:19] == [None] * 19
    assert body["series"]["std"][19:] == [0.0] * (720 - 19)
    assert body["measurements"]["correlation"] is None
    assert body["measurements"]["cointegration"] is None
    # Flat sealed prices leave every dependence measurement undefined, never zero.
    for name in ("kalman", "granger", "copula", "rolling_dependence"):
        assert body["measurements"][name] is None
    assert body["anchor"]["id"] == "binance:BTC"
    assert body["series"]["anchor_close"] == [10.0] * 720
    assert len(body["datasets"]) == 2
    assert all(len(row["semantic_fingerprint"]) == 64 for row in body["datasets"])
    assert "call" not in body and "proof" not in body and "demo" not in body
    after = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert before == after


@pytest.mark.parametrize("bar,expected", [("15m", 2880), ("4h", 180), ("1d", 30)])
def test_interval_and_missing_anchor_are_explicit(
    prepared: tuple[TestClient, Path], bar: str, expected: int
) -> None:
    client, _ = prepared
    response = client.get(
        "/api/pair-rotation/analysis",
        params={
            "coin_a": "binance:W",
            "coin_b": "binance:BTC",
            "bar": bar,
            "days": 30,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["bars_used"] == expected
    assert body["anchor"] is None
    assert body["series"]["anchor_close"] is None
    assert body["anchor_ranking"] == []
    assert len(body["series"]["time"]) == len(body["series"]["ratio"])


def test_missing_data_and_bad_queries_are_typed(tmp_path: Path) -> None:
    settings = ApiSettings(
        run_root=tmp_path / "runs", market_data_root=tmp_path / "data"
    )
    publish_directory(ProductUniverse(settings.run_root))
    client = TestClient(create_app(settings))
    query = {"coin_a": "binance:W", "coin_b": "binance:BTC"}
    response = client.get("/api/pair-rotation/analysis", params=query)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pair_rotation_analysis_unavailable"
    for invalid in (
        {"bar": "2h"},
        {"days": 7},
        {"band_lookback": 1},
        {"coin_b": "binance:W"},
    ):
        assert (
            client.get(
                "/api/pair-rotation/analysis", params=query | invalid
            ).status_code
            == 422
        )


def test_tampered_generation_never_becomes_analysis(
    prepared: tuple[TestClient, Path],
) -> None:
    client, root = prepared
    for path in (root / "data").rglob("*.parquet"):
        path.write_bytes(b"invalid parquet")
    response = client.get(
        "/api/pair-rotation/analysis",
        params={
            "coin_a": "binance:W",
            "coin_b": "binance:BTC",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pair_rotation_analysis_unavailable"


def test_explicit_missing_or_stale_anchor_returns_409(
    prepared: tuple[TestClient, Path],
) -> None:
    client, _ = prepared
    response = client.get(
        "/api/pair-rotation/analysis",
        params={
            "coin_a": "binance:W",
            "coin_b": "binance:BTC",
            "bar": "1h",
            "days": 30,
            "anchor": "binance:SOL",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pair_rotation_analysis_unavailable"
