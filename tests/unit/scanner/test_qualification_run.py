# pyright: reportPrivateUsage=false
"""Direct qualification regressions for current venue/capture semantics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qap.market import BookLevel, MarketMetadata, PublicBookSnapshot, VenueInstrument
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.market.microstructure_storage import (
    write_public_book_snapshots,
    write_public_market_metadata_snapshots,
)
from qap.market.public_capture import CaptureKind, capture_file
from qap.portfolio import AssetId
from qap.scanner.qualification_run import _capture_state, _two_way

AS_OF = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)
INSTRUMENT = VenueInstrument(
    venue="gate",
    venue_symbol="BTC_ETH",
    base=AssetId("BTC"),
    quote=AssetId("ETH"),
)


def _metadata() -> MarketMetadata:
    return MarketMetadata(
        instrument=INSTRUMENT,
        status="tradable",
        price_tick=Decimal("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=Decimal("0.001"),
        minimum_quantity=None,
        maximum_quantity=None,
        minimum_notional=None,
        maximum_notional=None,
        minimum_notional_applies_to_market=False,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=0,
        market_quantity_step=Decimal("0.001"),
        market_minimum_quantity=None,
        market_maximum_quantity=None,
    )


def _book(observed_at: datetime, fingerprint: str) -> PublicBookSnapshot:
    return PublicBookSnapshot(
        instrument=INSTRUMENT,
        observed_at=observed_at,
        source_id="test:book",
        source_fingerprint=fingerprint,
        bids=(BookLevel(price=99.99, quantity=10.0),),
        asks=(BookLevel(price=100.01, quantity=10.0),),
    )


def test_gate_tradable_status_survives_normalization_for_two_way_gate() -> None:
    metadata = _metadata()

    assert metadata.status == "TRADABLE"
    assert _two_way(metadata) is True


def test_capture_state_excludes_observations_after_qualification_as_of(
    tmp_path: Path,
) -> None:
    capture_root = tmp_path / "capture"
    before = _book(AS_OF - timedelta(minutes=5), "1" * 64)
    after = _book(AS_OF + timedelta(minutes=5), "2" * 64)
    for kind in (CaptureKind.L1, CaptureKind.DEPTH):
        write_public_book_snapshots(
            capture_file(
                capture_root,
                venue="gate",
                venue_symbol="BTC_ETH",
                kind=kind,
            ),
            (before, after),
        )
    metadata = public_market_metadata_snapshot_from_metadata(
        metadata=_metadata(),
        observed_at=AS_OF,
        source_id="test:metadata",
    )
    write_public_market_metadata_snapshots(
        capture_file(
            capture_root,
            venue="gate",
            venue_symbol="BTC_ETH",
            kind=CaptureKind.METADATA,
        ),
        (metadata,),
    )

    l1, depth, selected_metadata, satisfied = _capture_state(
        capture_root=capture_root,
        venue="gate",
        venue_symbol="BTC_ETH",
        as_of=AS_OF,
    )

    assert satisfied is False
    assert selected_metadata is not None
    assert tuple(item.snapshot_id for item in l1) == (before.snapshot_id,)
    assert tuple(item.snapshot_id for item in depth) == (before.snapshot_id,)
    assert after.snapshot_id not in {item.snapshot_id for item in (*l1, *depth)}
