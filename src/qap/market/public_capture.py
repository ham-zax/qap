"""Bounded one-shot public Spot evidence capture for approved scanner venues."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import quote

from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.market.adapters.gate_public import GatePublicAdapter
from qap.market.microstructure import (
    PublicBookSnapshot,
    PublicMarketMetadataSnapshot,
    public_market_metadata_snapshot_from_metadata,
)
from qap.market.microstructure_storage import (
    append_public_book_snapshot,
    append_public_market_metadata_snapshot,
)
from qap.portfolio import AssetId


class CaptureKind(StrEnum):
    L1 = "l1"
    DEPTH = "depth"
    METADATA = "metadata"


def capture_file(
    capture_root: str | Path,
    *,
    venue: str,
    venue_symbol: str,
    kind: CaptureKind,
) -> Path:
    """Return the deterministic append-only file for one public evidence stream."""

    return (
        Path(capture_root).resolve()
        / quote(venue.strip().lower(), safe="")
        / quote(venue_symbol.strip(), safe="")
        / f"{kind.value}.parquet"
    )


def capture_public_spot(
    *,
    venue: str,
    venue_symbol: str,
    base: AssetId,
    quote_asset: AssetId,
    capture_root: str | Path,
    kind: CaptureKind,
    observed_at: datetime | None = None,
    depth_limit: int = 20,
) -> Path:
    """Capture and persist one public observation; never access account APIs."""

    timestamp = datetime.now(UTC) if observed_at is None else observed_at
    normalized_venue = venue.strip().lower()
    observation: PublicBookSnapshot | None = None
    metadata_observation: PublicMarketMetadataSnapshot | None = None
    if normalized_venue == "binance":
        with BinancePublicAdapter() as adapter:
            metadata = adapter.fetch_market_metadata(
                venue_symbol=venue_symbol,
                base=base,
                quote=quote_asset,
                venue_base_asset=base.key,
                venue_quote_asset=quote_asset.key,
                require_trading=False,
            )
            if kind is CaptureKind.L1:
                observation = adapter.fetch_l1_book(
                    instrument=metadata.instrument,
                    observed_at=timestamp,
                )
            elif kind is CaptureKind.DEPTH:
                observation = adapter.fetch_shallow_depth(
                    instrument=metadata.instrument,
                    limit=depth_limit,
                    observed_at=timestamp,
                )
            else:
                metadata_observation = public_market_metadata_snapshot_from_metadata(
                    metadata=metadata,
                    observed_at=timestamp,
                    source_id="binance:normalized-public-metadata",
                )
    elif normalized_venue == "gate":
        with GatePublicAdapter() as adapter:
            metadata = adapter.fetch_market_metadata(
                venue_symbol=venue_symbol,
                base=base,
                quote=quote_asset,
                venue_base_asset=base.key,
                venue_quote_asset=quote_asset.key,
            )
            if kind is CaptureKind.L1:
                observation = adapter.fetch_l1_book(
                    instrument=metadata.instrument,
                    observed_at=timestamp,
                )
            elif kind is CaptureKind.DEPTH:
                observation = adapter.fetch_shallow_depth(
                    instrument=metadata.instrument,
                    limit=depth_limit,
                    observed_at=timestamp,
                )
            else:
                metadata_observation = public_market_metadata_snapshot_from_metadata(
                    metadata=metadata,
                    observed_at=timestamp,
                    source_id="gate:normalized-public-metadata",
                )
    else:
        raise ValueError("prospective capture venue must be binance or gate")

    target = capture_file(
        capture_root,
        venue=normalized_venue,
        venue_symbol=venue_symbol,
        kind=kind,
    )
    if kind is CaptureKind.METADATA:
        assert metadata_observation is not None
        append_public_market_metadata_snapshot(target, metadata_observation)
    else:
        assert observation is not None
        append_public_book_snapshot(target, observation)
    return target


__all__ = ["CaptureKind", "capture_file", "capture_public_spot"]
