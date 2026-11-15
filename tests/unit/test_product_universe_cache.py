"""Tests for stat-versioned JSON state caching in ProductUniverse."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from qap.product_universe import ProductUniverse
from qap.product_universe_cache import VersionedFileCache
from qap.product_universe_models import AssetIdentityMapping, ProductUniverseState

NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


def _write_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-other")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def test_read_state_returns_cached_instance_until_file_changes(tmp_path: Path) -> None:
    universe = ProductUniverse(tmp_path)
    universe.state_path.parent.mkdir(parents=True, exist_ok=True)
    universe.state_path.write_text(
        ProductUniverseState().model_dump_json(), encoding="utf-8"
    )
    first = universe.read_state()
    second = universe.read_state()
    assert first is second


def test_read_state_invalidates_after_public_write(tmp_path: Path) -> None:
    universe = ProductUniverse(tmp_path)
    mapping = AssetIdentityMapping(
        venue="binance",
        venue_asset_code="BTC",
        canonical_asset_id="BTC",
        asset_identity_version="v1",
        confirmed_at=NOW,
    )
    initial = ProductUniverseState(identity_mappings=(mapping,))
    _write_atomic(universe.state_path, initial.model_dump_json())
    assert universe.read_state().approved_asset_ids == ()

    universe.set_asset_admission(
        canonical_asset_id="BTC", approved=True, updated_at=NOW
    )
    updated = universe.read_state()
    assert updated.approved_asset_ids == ("BTC",)


def test_read_state_invalidates_after_external_atomic_replace(
    tmp_path: Path,
) -> None:
    universe = ProductUniverse(tmp_path)
    _write_atomic(universe.state_path, ProductUniverseState().model_dump_json())
    assert universe.read_state().approved_asset_ids == ()

    updated = ProductUniverseState(approved_asset_ids=("ETH",))
    _write_atomic(universe.state_path, updated.model_dump_json())
    assert universe.read_state().approved_asset_ids == ("ETH",)


def test_versioned_file_cache_parses_only_when_file_version_changes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "sample.json"
    _write_atomic(target, '{"v": 1}')
    cache = VersionedFileCache()
    calls = 0

    def parse(text: str) -> str:
        nonlocal calls
        calls += 1
        return text

    assert cache.get(target, parse) == '{"v": 1}'
    assert cache.get(target, parse) == '{"v": 1}'
    assert calls == 1

    _write_atomic(target, '{"v": 2}')
    assert cache.get(target, parse) == '{"v": 2}'
    assert calls == 2
