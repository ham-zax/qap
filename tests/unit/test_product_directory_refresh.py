"""Per-venue refresh preserves authoritative observations through outages."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.market.adapters.gate_public import GatePublicAdapter, GatePublicDataError
from qap.market.directory import CurrentSpotDirectoryObservation, CurrentSpotMarket
from qap.market.microstructure import public_payload_fingerprint
from qap.product_universe import (
    ProductMarketDirectory,
    ProductUniverse,
    ProductUniverseError,
)

OLD = datetime(2026, 9, 25, tzinfo=UTC)
NEW = datetime(2026, 9, 30, tzinfo=UTC)


def _observation(
    venue: str, observed_at: datetime = NEW, base: str = "ETH"
) -> CurrentSpotDirectoryObservation:
    return CurrentSpotDirectoryObservation(
        venue=venue,
        observed_at=observed_at,
        source_id=f"{venue}-{base}-{observed_at.isoformat()}",
        source_fingerprint=("1" if observed_at == NEW else "0") * 64,
        markets=(
            CurrentSpotMarket(
                venue=venue,
                venue_symbol=f"{base}USDT" if venue == "binance" else f"{base}_USDT",
                venue_base_asset=base,
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
            ),
        ),
    )


def _seed(universe: ProductUniverse) -> ProductMarketDirectory:
    directory = ProductMarketDirectory.from_observations(
        (_observation("binance", OLD, "BTC"), _observation("gate", OLD, "BTC"))
    )
    universe.directory_path.parent.mkdir(parents=True, exist_ok=True)
    universe.directory_path.write_text(directory.model_dump_json(), encoding="utf-8")
    return directory


def _adapters(monkeypatch: pytest.MonkeyPatch, failed: set[str]) -> None:
    def binance(_self: BinancePublicAdapter) -> CurrentSpotDirectoryObservation:
        if "binance" in failed:
            raise BinancePublicDataError("Binance directory unavailable")
        return _observation("binance")

    def gate(_self: GatePublicAdapter) -> CurrentSpotDirectoryObservation:
        if "gate" in failed:
            raise GatePublicDataError("Gate directory unavailable")
        return _observation("gate")

    monkeypatch.setattr(BinancePublicAdapter, "fetch_spot_directory", binance)
    monkeypatch.setattr(GatePublicAdapter, "fetch_spot_directory", gate)


@pytest.mark.parametrize("failed", ["binance", "gate"])
@pytest.mark.parametrize("saved", [False, True])
def test_one_outage_keeps_successful_venue_usable_and_failed_source_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: str, saved: bool
) -> None:
    universe = ProductUniverse(tmp_path)
    original = _seed(universe) if saved else None
    _adapters(monkeypatch, {failed})

    attempted_before = datetime.now(UTC)
    directory = universe.refresh_directory()
    attempted_after = datetime.now(UTC)

    successful = "gate" if failed == "binance" else "binance"
    results = {result.venue: result for result in directory.refresh_results}
    assert results[successful].status == "refreshed"
    assert results[successful].error is None
    assert results[failed].status == ("stale" if saved else "unavailable")
    assert results[failed].error
    assert all(result.attempted_at.tzinfo == UTC for result in results.values())
    assert all(
        attempted_before <= result.attempted_at <= attempted_after
        for result in results.values()
    )
    sources = {source.venue: source for source in directory.sources}
    assert sources[successful].observed_at == NEW
    assert {
        market.venue_base_asset
        for market in directory.markets
        if market.venue == successful
    } == {"ETH"}
    if original is not None:
        assert sources[failed] == next(
            source for source in original.sources if source.venue == failed
        )
        assert tuple(
            market for market in directory.markets if market.venue == failed
        ) == tuple(market for market in original.markets if market.venue == failed)
    else:
        assert failed not in sources
        assert all(market.venue != failed for market in directory.markets)
    assert universe.read_directory() == directory


def test_success_is_persisted_before_second_venue_is_attempted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe = ProductUniverse(tmp_path)
    original = _seed(universe)
    _adapters(monkeypatch, set())

    def gate(_self: GatePublicAdapter) -> CurrentSpotDirectoryObservation:
        checkpoint = ProductUniverse(tmp_path).read_directory()
        assert checkpoint is not None
        assert (
            next(
                source for source in checkpoint.sources if source.venue == "binance"
            ).observed_at
            == NEW
        )
        assert next(
            source for source in checkpoint.sources if source.venue == "gate"
        ) == next(source for source in original.sources if source.venue == "gate")
        raise GatePublicDataError("Gate directory unavailable")

    monkeypatch.setattr(GatePublicAdapter, "fetch_spot_directory", gate)
    directory = universe.refresh_directory()
    assert {result.venue: result.status for result in directory.refresh_results} == {
        "binance": "refreshed",
        "gate": "stale",
    }


def test_all_failed_refresh_preserves_saved_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe = ProductUniverse(tmp_path)
    original = _seed(universe)
    _adapters(monkeypatch, {"binance", "gate"})

    directory = universe.refresh_directory()

    assert directory.sources == original.sources
    assert directory.markets == original.markets
    assert directory.observed_at == OLD
    assert {result.status for result in directory.refresh_results} == {"stale"}
    assert universe.read_directory() == directory


def test_successful_empty_venue_replaces_old_markets_while_failed_venue_is_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe = ProductUniverse(tmp_path)
    original = _seed(universe)
    _adapters(monkeypatch, {"gate"})

    def binance(_self: BinancePublicAdapter) -> CurrentSpotDirectoryObservation:
        return CurrentSpotDirectoryObservation(
            venue="binance",
            observed_at=NEW,
            source_id="binance-empty-directory",
            source_fingerprint="2" * 64,
            markets=(),
        )

    monkeypatch.setattr(BinancePublicAdapter, "fetch_spot_directory", binance)

    directory = universe.refresh_directory()

    assert directory.markets == tuple(
        market for market in original.markets if market.venue == "gate"
    )
    assert (
        next(
            source for source in directory.sources if source.venue == "binance"
        ).source_id
        == "binance-empty-directory"
    )
    assert universe.read_directory() == directory


def test_all_failed_refresh_without_saved_observation_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe = ProductUniverse(tmp_path)
    _adapters(monkeypatch, {"binance", "gate"})

    with pytest.raises(ProductUniverseError):
        universe.refresh_directory()

    assert universe.read_directory() is None


def test_invalid_saved_directory_cannot_be_overwritten_by_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe = ProductUniverse(tmp_path)
    universe.directory_path.parent.mkdir(parents=True)
    invalid = '{"schema_version":"unsupported","sources":[],"markets":[]}'
    universe.directory_path.write_text(invalid, encoding="utf-8")
    _adapters(monkeypatch, set())

    with pytest.raises(ProductUniverseError, match="invalid"):
        universe.refresh_directory()

    assert universe.directory_path.read_text(encoding="utf-8") == invalid


def test_v1_directory_remains_readable_with_unchanged_provenance_id(
    tmp_path: Path,
) -> None:
    universe = ProductUniverse(tmp_path)
    payload = {
        "schema_version": "qap.product.market-directory.v1",
        "sources": [
            {
                "venue": venue,
                "observed_at": "2026-09-25T00:00:00Z",
                "source_id": f"{venue}-original",
                "source_fingerprint": "0" * 64,
            }
            for venue in ("binance", "gate")
        ],
        "markets": [
            {
                "venue": "binance",
                "venue_symbol": "BTCUSDT",
                "venue_base_asset": "BTC",
                "venue_quote_asset": "USDT",
                "status": "TRADING",
                "trading": True,
            }
        ],
    }
    universe.directory_path.parent.mkdir(parents=True)
    original = json.dumps(payload)
    universe.directory_path.write_text(original, encoding="utf-8")

    directory = universe.read_directory()

    assert directory is not None
    assert directory.schema_version == "qap.product.market-directory.v1"
    assert directory.refresh_results == ()
    assert directory.directory_id == public_payload_fingerprint(payload)
    assert (
        ProductMarketDirectory.model_validate_json(
            directory.model_dump_json()
        ).directory_id
        == directory.directory_id
    )
    assert universe.directory_path.read_text(encoding="utf-8") == original
