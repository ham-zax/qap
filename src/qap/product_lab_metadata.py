"""Capture/read public venue constraints with existing immutable observations."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from qap.file_lock import FileLock
from qap.market import VenueInstrument
from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.market.microstructure import (
    PublicMarketMetadataSnapshot,
    public_market_metadata_snapshot_from_metadata,
    public_payload_fingerprint,
)
from qap.market.microstructure_storage import (
    append_public_market_metadata_snapshot,
    read_public_market_metadata_snapshots,
)
from qap.product_universe import ProductUniverse, ResolvedProductInstrument


def _path(data_root: Path, instrument: VenueInstrument) -> Path:
    identity = public_payload_fingerprint(
        {
            "venue": instrument.venue,
            "symbol": instrument.venue_symbol,
            "base": instrument.base.key,
            "quote": instrument.quote.key,
        }
    )
    return data_root / "product-market-data" / "lab-metadata" / f"{identity}.parquet"


def read_lab_metadata(
    data_root: Path, instruments: tuple[VenueInstrument, ...]
) -> tuple[PublicMarketMetadataSnapshot, ...]:
    snapshots: list[PublicMarketMetadataSnapshot] = []
    for instrument in instruments:
        path = _path(data_root, instrument)
        if path.is_file():
            records = read_public_market_metadata_snapshots(path)
            snapshots.append(max(records, key=lambda record: record.observed_at))
    return tuple(snapshots)


def capture_lab_metadata(
    universe: ProductUniverse,
    data_root: Path,
    instruments: tuple[ResolvedProductInstrument, ...],
) -> None:
    directory = universe.read_directory()
    if directory is None:
        raise ValueError("Venue metadata needs an observed market directory.")
    now = datetime.now(UTC)
    with FileLock(data_root / "product-market-data" / "lab-metadata" / ".lock"):
        with BinancePublicAdapter() as adapter:
            for instrument in instruments:
                path = _path(data_root, instrument.instrument)
                if path.is_file():
                    latest = read_public_market_metadata_snapshots(path)[-1]
                    if latest.observed_at >= now - timedelta(days=1):
                        continue
                market = next(
                    row
                    for row in directory.markets
                    if row.venue == "binance"
                    and row.venue_symbol == instrument.instrument.venue_symbol
                )
                metadata = adapter.fetch_market_metadata(
                    venue_symbol=market.venue_symbol,
                    base=instrument.instrument.base,
                    quote=instrument.instrument.quote,
                    venue_base_asset=market.venue_base_asset,
                    venue_quote_asset=market.venue_quote_asset,
                )
                snapshot = public_market_metadata_snapshot_from_metadata(
                    metadata=metadata,
                    observed_at=now,
                    source_id=f"binance-exchangeInfo:{market.venue_symbol}",
                )
                append_public_market_metadata_snapshot(path, snapshot)
