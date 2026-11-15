"""Unit tests for stat-keyed market-data projection and generation caches."""

from __future__ import annotations

from pathlib import Path

from qap.product_market_data_cache import (
    GenerationCache,
    ProjectionRowCache,
    stat_key,
)
from qap.product_market_data_models import CurrentMarketDataGeneration


def _row(dataset_id: str, fp: str = "sha256:aaa") -> CurrentMarketDataGeneration:
    return CurrentMarketDataGeneration(
        dataset_id=dataset_id,
        relative_path=f"generations/{dataset_id}.parquet",
        venue="binance",
        venue_symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        interval="15m",
        semantic_fingerprint=fp,
        coverage_start=None,
        coverage_end_exclusive=None,
        provenance_status="complete",
        provenance_relative_path=None,
        issue=None,
    )


def test_projection_row_cache_hits_and_invalidates_on_stat_change(
    tmp_path: Path,
) -> None:
    cache = ProjectionRowCache()
    data_file = tmp_path / "btc.parquet"
    prov_file = tmp_path / "btc.provenance.json"
    data_file.write_bytes(b"v1")
    prov_file.write_text("{}", encoding="utf-8")

    key1 = (
        tmp_path,
        "binance:BTCUSDT:15m",
        "btc.parquet",
        "sha256:aaa",
        stat_key(data_file),
        stat_key(prov_file),
    )
    row1 = _row("binance:BTCUSDT:15m")
    cache.put(tmp_path, "binance:BTCUSDT:15m", key1, row1)
    assert cache.get(tmp_path, "binance:BTCUSDT:15m", key1) is row1

    data_file.write_bytes(b"v2-longer")
    key2 = (
        tmp_path,
        "binance:BTCUSDT:15m",
        "btc.parquet",
        "sha256:aaa",
        stat_key(data_file),
        stat_key(prov_file),
    )
    assert cache.get(tmp_path, "binance:BTCUSDT:15m", key2) is None


def test_generation_cache_evicts_oldest_when_full(tmp_path: Path) -> None:
    cache = GenerationCache(maxsize=2)
    k1 = (tmp_path, "d1", "fp1", None, None)
    k2 = (tmp_path, "d2", "fp2", None, None)
    k3 = (tmp_path, "d3", "fp3", None, None)
    v1 = ("p1", "s1")
    v2 = ("p2", "s2")
    v3 = ("p3", "s3")
    cache.put(k1, v1)  # type: ignore[arg-type]
    cache.put(k2, v2)  # type: ignore[arg-type]
    assert cache.get(k1) is v1  # k1 becomes most-recently-used
    cache.put(k3, v3)  # type: ignore[arg-type]
    assert cache.get(k2) is None
    assert cache.get(k1) is v1
    assert cache.get(k3) is v3
