# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from qap.market import VenueInstrument
from qap.market.microstructure import BookLevel, PublicBookSnapshot
from qap.market.microstructure_storage import (
    MicrostructureStorageError,
    read_public_book_snapshots,
    write_public_book_snapshots,
)
from qap.portfolio import AssetId

BTC = AssetId("BTC")
ETH = AssetId("ETH")
INSTRUMENT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCETH",
    base=BTC,
    quote=ETH,
)
NOW = datetime(2026, 8, 18, tzinfo=UTC)


def _snapshot(*, observed_at: datetime = NOW) -> PublicBookSnapshot:
    return PublicBookSnapshot(
        instrument=INSTRUMENT,
        observed_at=observed_at,
        source_id="binance-public-depth",
        source_fingerprint="a" * 64,
        bids=(
            BookLevel(price=2.00, quantity=3.0),
            BookLevel(price=1.99, quantity=5.0),
        ),
        asks=(
            BookLevel(price=2.01, quantity=4.0),
            BookLevel(price=2.02, quantity=6.0),
        ),
    )


def test_public_book_snapshot_is_immutable_ordered_and_fingerprinted() -> None:
    snapshot = _snapshot()

    assert snapshot.best_bid == 2.00
    assert snapshot.best_ask == 2.01
    assert snapshot.mid_price == pytest.approx(2.005)
    assert len(snapshot.snapshot_id) == 64
    assert _snapshot().snapshot_id == snapshot.snapshot_id
    assert (
        _snapshot(observed_at=NOW + timedelta(seconds=1)).snapshot_id
        != snapshot.snapshot_id
    )

    with pytest.raises(AttributeError):
        snapshot.bids = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    ("bids", "asks", "message"),
    [
        (
            (BookLevel(price=2.00, quantity=1.0), BookLevel(price=2.01, quantity=1.0)),
            (BookLevel(price=2.02, quantity=1.0),),
            "bids must be strictly descending",
        ),
        (
            (BookLevel(price=2.00, quantity=1.0),),
            (BookLevel(price=2.02, quantity=1.0), BookLevel(price=2.01, quantity=1.0)),
            "asks must be strictly ascending",
        ),
        (
            (BookLevel(price=2.01, quantity=1.0),),
            (BookLevel(price=2.01, quantity=1.0),),
            "best bid must be below best ask",
        ),
    ],
)
def test_public_book_snapshot_rejects_invalid_ordering(
    bids: tuple[BookLevel, ...],
    asks: tuple[BookLevel, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        PublicBookSnapshot(
            instrument=INSTRUMENT,
            observed_at=NOW,
            source_id="binance-public-depth",
            source_fingerprint="a" * 64,
            bids=bids,
            asks=asks,
        )


@pytest.mark.parametrize(
    ("price", "quantity"),
    [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0), (float("inf"), 1.0)],
)
def test_book_level_requires_positive_finite_values(
    price: float, quantity: float
) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        BookLevel(price=price, quantity=quantity)


def test_public_book_snapshot_requires_utc_and_exact_source_fingerprint() -> None:
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        _snapshot(observed_at=datetime(2026, 8, 18))
    with pytest.raises(ValueError, match="SHA-256"):
        PublicBookSnapshot(
            instrument=INSTRUMENT,
            observed_at=NOW,
            source_id="binance-public-depth",
            source_fingerprint="not-a-hash",
            bids=(BookLevel(price=2.00, quantity=1.0),),
            asks=(BookLevel(price=2.01, quantity=1.0),),
        )


def test_microstructure_parquet_round_trip_preserves_exact_snapshot_ids(
    tmp_path: Path,
) -> None:
    snapshots = (
        _snapshot(),
        _snapshot(observed_at=NOW + timedelta(seconds=1)),
    )
    path = tmp_path / "books.parquet"

    write_public_book_snapshots(path, snapshots)
    loaded = read_public_book_snapshots(path)

    assert loaded == snapshots
    assert tuple(item.snapshot_id for item in loaded) == tuple(
        item.snapshot_id for item in snapshots
    )


def test_microstructure_reader_rejects_snapshot_id_tamper(tmp_path: Path) -> None:
    path = tmp_path / "books.parquet"
    write_public_book_snapshots(path, (_snapshot(),))
    table = pq.read_table(path)
    columns = {
        name: table[name] for name in table.schema.names if name != "snapshot_id"
    }
    columns["snapshot_id"] = pa.array(["f" * 64], type=pa.string())
    pq.write_table(pa.table(columns, schema=table.schema), path)

    with pytest.raises(MicrostructureStorageError, match="snapshot_id"):
        read_public_book_snapshots(path)
