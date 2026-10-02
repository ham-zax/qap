"""The API must expose the observed venue code behind an operator asset mapping."""

from datetime import UTC, datetime
from pathlib import Path

from qap.api.product_schemas import ResearchUniverseVenueDto
from qap.product_universe import (
    DirectoryMarket,
    DirectorySource,
    ProductMarketDirectory,
    ProductUniverse,
)


def test_recorded_asset_keeps_observed_venue_code_visible(tmp_path: Path) -> None:
    now = datetime(2026, 9, 25, tzinfo=UTC)
    universe = ProductUniverse(tmp_path)
    directory = ProductMarketDirectory(
        sources=(
            DirectorySource(
                venue="binance",
                observed_at=now,
                source_id="binance-directory",
                source_fingerprint="0" * 64,
            ),
            DirectorySource(
                venue="gate",
                observed_at=now,
                source_id="gate-directory",
                source_fingerprint="1" * 64,
            ),
        ),
        markets=(
            DirectoryMarket(
                venue="binance",
                venue_symbol="WUSDT",
                venue_base_asset="W",
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
            ),
        ),
    )
    universe.directory_path.parent.mkdir(parents=True, exist_ok=True)
    universe.directory_path.write_text(directory.model_dump_json(), encoding="utf-8")
    universe.set_identity_mapping(
        venue="binance",
        venue_asset_code="USDT",
        canonical_asset_id="USDT",
        asset_identity_version="operator-usdt-1",
    )
    universe.set_identity_mapping(
        venue="binance",
        venue_asset_code="W",
        canonical_asset_id="W",
        asset_identity_version="operator-wormhole-1",
    )

    assets = universe.projection().assets
    asset = next(item for item in assets if item.asset.key == "W")
    venue = asset.venues[0]
    dto = ResearchUniverseVenueDto(
        venue="binance",
        venue_symbol=venue.venue_symbol,
        venue_asset_code=venue.venue_asset_code,
        status=venue.status,
        trading=venue.trading,
    )
    assert dto.venue_symbol == "WUSDT"
    assert dto.venue_asset_code == "W"
