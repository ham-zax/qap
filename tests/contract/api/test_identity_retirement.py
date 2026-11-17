"""Known corruption is retired only from a verified, dependency-free preview."""

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from qap.market import BarInterval, VenueInstrument
from qap.portfolio import AssetId
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_catalog import load_scanner_catalog
from qap.product_market_data_models import (
    MarketDataDerivation,
    MarketDataParentGeneration,
)
from qap.product_universe import ProductResearchScope, ResolvedProductInstrument

from .pair_rotation_support import NOW, OfflineBinance


def data_with_corruption(tmp_path: Path) -> ProductMarketData:
    owner = ProductMarketData(tmp_path / "runs", tmp_path / "data")
    instruments = tuple(
        ResolvedProductInstrument(
            instrument=VenueInstrument(
                venue="binance",
                venue_symbol=symbol,
                base=AssetId(base),
                quote=AssetId("USDT"),
            ),
            base_asset_identity_version="old",
            quote_asset_identity_version="old",
            directory_observed_at=NOW,
            source_id="fixture",
            source_fingerprint="1" * 64,
        )
        for base, symbol in (("BTC", "WUSDT"), ("ETH", "ETHUSDT"))
    )
    scope = ProductResearchScope(
        directory_id="1" * 64,
        directory_observed_at=NOW,
        approved_assets=(AssetId("BTC"), AssetId("ETH")),
        instruments=instruments,
    )
    fake = OfflineBinance()
    for index, item in enumerate(instruments):
        owner.publish_generation(
            scope,
            fake.acquire_generation_input(
                scope=scope,
                instrument=item,
                dataset_id=f"fixture-{index}",
                interval=BarInterval("15m"),
                start=NOW.replace(hour=0, minute=0),
                end_exclusive=NOW.replace(hour=0, minute=0) + timedelta(days=1),
            ),
        )
    return owner


def test_retirement_revokes_bad_catalog_and_deletes_only_verified_files(
    tmp_path: Path,
) -> None:
    owner = data_with_corruption(tmp_path)
    assert owner.market_data_root is not None
    before = load_scanner_catalog(owner.market_data_root)
    clean = before.source("fixture-1")
    clean_bytes = (owner.market_data_root / clean.relative_path).read_bytes()
    plan = owner.identity_retirement_preview()
    assert len(plan.generations) == 1 and len(plan.file_hashes) == 2
    assert plan.dependencies == () and plan.generations[0].base_asset == "BTC"
    owner.retire_identity_data(plan)
    catalog = load_scanner_catalog(owner.market_data_root)
    assert tuple(item.dataset_id for item in catalog.sources) == ("fixture-1",)
    assert (owner.market_data_root / clean.relative_path).read_bytes() == clean_bytes
    assert all(
        not (owner.market_data_root / path).exists() for path, _ in plan.file_hashes
    )
    audit = (
        owner.workspace_root / f"product/identity-retirements/{plan.fingerprint}.json"
    )
    assert json.loads(audit.read_text())["generations"][0]["base_asset"] == "BTC"
    assert owner.identity_retirement_preview().generations == ()
    assert owner.projection().maintenance.status == "idle"


def test_saved_research_dependency_prevents_deletion(tmp_path: Path) -> None:
    owner = data_with_corruption(tmp_path)
    assert owner.market_data_root is not None
    first = owner.identity_retirement_preview()
    saved = owner.workspace_root / "experiments/saved/manifest.json"
    saved.parent.mkdir(parents=True)
    saved.write_text(json.dumps({"source": first.generations[0].semantic_fingerprint}))
    plan = owner.identity_retirement_preview()
    assert plan.dependencies == ("experiments/saved/manifest.json",)
    before = (owner.market_data_root / "catalog.json").read_bytes()
    with pytest.raises(ProductMarketDataError, match="Saved research depends"):
        owner.retire_identity_data(plan)
    assert (owner.market_data_root / "catalog.json").read_bytes() == before
    assert all(
        (owner.market_data_root / path).is_file() for path, _ in plan.file_hashes
    )


def test_stale_preview_is_rejected_before_any_catalog_mutation(tmp_path: Path) -> None:
    owner = data_with_corruption(tmp_path)
    assert owner.market_data_root is not None
    plan = owner.identity_retirement_preview()
    catalog_path = owner.market_data_root / "catalog.json"
    catalog_path.write_bytes(catalog_path.read_bytes() + b"\n")
    with pytest.raises(ProductMarketDataError, match="preview is stale"):
        owner.retire_identity_data(plan)
    assert all(
        (owner.market_data_root / path).is_file() for path, _ in plan.file_hashes
    )


def test_descendant_is_retired_even_with_a_different_listing_identity(
    tmp_path: Path,
) -> None:
    owner = data_with_corruption(tmp_path)
    assert owner.market_data_root is not None
    parent = owner.identity_retirement_preview().generations[0]
    item = ResolvedProductInstrument(
        instrument=VenueInstrument(
            venue="binance",
            venue_symbol="SOLUSDT",
            base=AssetId("SOL"),
            quote=AssetId("USDT"),
        ),
        base_asset_identity_version="old",
        quote_asset_identity_version="old",
        directory_observed_at=NOW,
        source_id="fixture",
        source_fingerprint="1" * 64,
    )
    scope = ProductResearchScope(
        directory_id="1" * 64,
        directory_observed_at=NOW,
        approved_assets=(AssetId("SOL"),),
        instruments=(item,),
    )
    derived = OfflineBinance().acquire_generation_input(
        scope=scope,
        instrument=item,
        dataset_id="descendant",
        interval=BarInterval("15m"),
        start=NOW.replace(hour=0, minute=0),
        end_exclusive=NOW.replace(hour=0, minute=0) + timedelta(days=1),
    )
    owner.publish_generation(
        scope,
        replace(
            derived,
            derivation=MarketDataDerivation(
                derivation_id="fixture-derived",
                parents=(
                    MarketDataParentGeneration(
                        dataset_id=parent.dataset_id,
                        relative_path=parent.relative_path,
                        semantic_fingerprint=parent.semantic_fingerprint,
                    ),
                ),
            ),
        ),
    )
    plan = owner.identity_retirement_preview()
    assert {item.dataset_id for item in plan.generations} == {"fixture-0", "descendant"}
    owner.retire_identity_data(plan)
    assert tuple(
        item.dataset_id for item in load_scanner_catalog(owner.market_data_root).sources
    ) == ("fixture-1",)


def test_generation_symlink_cannot_escape_retirement_root(tmp_path: Path) -> None:
    owner = data_with_corruption(tmp_path)
    assert owner.market_data_root is not None
    plan = owner.identity_retirement_preview()
    target = owner.market_data_root / plan.generations[0].relative_path
    outside = tmp_path / "outside.parquet"
    target.rename(outside)
    target.symlink_to(outside)
    with pytest.raises(ProductMarketDataError, match="inventory failed"):
        owner.identity_retirement_preview()
    assert outside.is_file()
