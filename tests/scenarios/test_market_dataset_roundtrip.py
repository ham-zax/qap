# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

from pathlib import Path
from typing import cast

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from qap.market import (
    BarInterval,
    MarketDataStorageError,
    VenueInstrument,
    align_bar_series,
    fingerprint_bar_series,
    load_csv_bar_series,
    read_parquet_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId

FIXTURES = Path(__file__).parents[1] / "fixtures" / "market"


def _instrument(base: str) -> VenueInstrument:
    return VenueInstrument(
        venue="binance",
        venue_symbol=f"{base}USDT",
        base=AssetId(base),
        quote=AssetId("USDT"),
    )


def test_csv_to_parquet_roundtrip_is_semantic_and_path_independent(
    tmp_path: Path,
) -> None:
    source = load_csv_bar_series(
        FIXTURES / "BTCUSDT_1h.csv",
        instrument=_instrument("BTC"),
        interval=BarInterval("1h"),
    )
    expected_fingerprint = fingerprint_bar_series(source)

    first_path = tmp_path / "first" / "btc.parquet"
    second_path = tmp_path / "second" / "renamed.parquet"
    first_written = write_parquet_bar_series(first_path, source)
    second_written = write_parquet_bar_series(second_path, source)

    first = read_parquet_bar_series(first_path)
    second = read_parquet_bar_series(second_path)

    assert len(source) == 12
    assert first == source
    assert second == source
    assert first_written == expected_fingerprint
    assert second_written == expected_fingerprint
    assert fingerprint_bar_series(first) == expected_fingerprint
    assert fingerprint_bar_series(second) == expected_fingerprint


def test_two_fixture_datasets_align_without_imputation() -> None:
    interval = BarInterval("1h")
    btc = load_csv_bar_series(
        FIXTURES / "BTCUSDT_1h.csv",
        instrument=_instrument("BTC"),
        interval=interval,
    )
    eth = load_csv_bar_series(
        FIXTURES / "ETHUSDT_1h.csv",
        instrument=_instrument("ETH"),
        interval=interval,
    )

    aligned = align_bar_series([btc, eth])

    assert len(aligned.timestamps) == 12
    assert aligned.for_instrument(btc.instrument).bars == btc.bars
    assert aligned.for_instrument(eth.instrument).bars == eth.bars


def test_parquet_writer_refuses_to_replace_an_existing_artifact(
    tmp_path: Path,
) -> None:
    source = load_csv_bar_series(
        FIXTURES / "BTCUSDT_1h.csv",
        instrument=_instrument("BTC"),
        interval=BarInterval("1h"),
    )
    destination = tmp_path / "immutable.parquet"
    write_parquet_bar_series(destination, source)

    with pytest.raises(MarketDataStorageError, match="already exists"):
        write_parquet_bar_series(destination, source)


def test_parquet_reader_rejects_semantic_tampering(
    tmp_path: Path,
) -> None:
    source = load_csv_bar_series(
        FIXTURES / "BTCUSDT_1h.csv",
        instrument=_instrument("BTC"),
        interval=BarInterval("1h"),
    )
    destination = tmp_path / "tampered.parquet"
    write_parquet_bar_series(destination, source)

    original = pq.read_table(destination)
    columns = cast(dict[str, list[object]], original.to_pydict())
    closes = columns["close"]
    closes[0] = cast(float, closes[0]) + 1.0
    tampered = pa.Table.from_pydict(columns, schema=original.schema)
    pq.write_table(tampered, destination)

    with pytest.raises(MarketDataStorageError, match="fingerprint"):
        read_parquet_bar_series(destination)
