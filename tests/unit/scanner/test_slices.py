import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId
from qap.scanner.catalog import (
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    catalog_semantic_identity,
    load_scanner_catalog,
    resolve_catalog_source,
)
from qap.scanner.models import ScanDefinition, ScanInputIdentity
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity
from qap.scanner.slices import evaluate_series

BTC = AssetId("BTC")
USDT = AssetId("USDT")
INSTRUMENT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCUSDT",
    base=BTC,
    quote=USDT,
)
INTERVAL = BarInterval("1h")
START = datetime(2026, 1, 1, tzinfo=UTC)


def _series(count: int, *, price_offset: float = 0.0) -> ValidatedBarSeries:
    bars: list[MarketBar] = []
    for index in range(count):
        price = 100.0 + price_offset + float(index)
        bars.append(
            MarketBar(
                instrument=INSTRUMENT,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=price,
                high=price + 1.0,
                low=price - 1.0,
                close=price + 0.5,
                volume=10.0 + float(index),
            )
        )
    return validate_bar_series(bars)


def test_evaluated_slice_excludes_incomplete_future_rows_and_has_exact_identity() -> (
    None
):
    cutoff = START + timedelta(hours=6)
    original = _series(6)
    appended = _series(7)

    original_eval = evaluate_series(
        original,
        dataset_id="btc-1h-original",
        eligible_information_end=cutoff,
        lookback=timedelta(hours=4),
    )
    appended_eval = evaluate_series(
        appended,
        dataset_id="btc-1h-appended",
        eligible_information_end=cutoff,
        lookback=timedelta(hours=4),
    )

    assert original_eval.source_artifact_fingerprint != (
        appended_eval.source_artifact_fingerprint
    )
    assert original_eval.selection_slice_fingerprint == (
        appended_eval.selection_slice_fingerprint
    )
    assert tuple(bar.candle_open_time for bar in appended_eval.bars) == tuple(
        START + timedelta(hours=hour) for hour in range(2, 6)
    )
    assert all(bar.bar_end_exclusive <= cutoff for bar in appended_eval.bars)
    assert appended_eval.bar_coverage == 1.0
    assert appended_eval.longest_missing_run == 0


def test_selection_fingerprint_changes_when_a_selected_row_changes() -> None:
    cutoff = START + timedelta(hours=6)
    baseline = evaluate_series(
        _series(6),
        dataset_id="baseline",
        eligible_information_end=cutoff,
        lookback=timedelta(hours=4),
    )
    changed = evaluate_series(
        _series(6, price_offset=1.0),
        dataset_id="changed",
        eligible_information_end=cutoff,
        lookback=timedelta(hours=4),
    )

    assert baseline.selection_slice_fingerprint != changed.selection_slice_fingerprint


def test_coverage_counts_missing_boundary_bars_without_interpolation() -> None:
    cutoff = START + timedelta(hours=6)
    short_source = validate_bar_series(_series(6).bars[3:])

    evaluated = evaluate_series(
        short_source,
        dataset_id="short-source",
        eligible_information_end=cutoff,
        lookback=timedelta(hours=4),
    )

    assert len(evaluated.bars) == 3
    assert evaluated.bar_coverage == 0.75
    assert evaluated.longest_missing_run == 1


def test_catalog_resolves_only_safe_admitted_parquet_with_matching_identity(
    tmp_path: Path,
) -> None:
    market_path = tmp_path / "market" / "BTCUSDT_1h.parquet"
    lifecycle_path = tmp_path / "lifecycle.jsonl"
    lifecycle_path.write_text("", encoding="utf-8")
    series = _series(6)
    fingerprint = write_parquet_bar_series(market_path, series)
    catalog_data = {
        "schema_version": "qap.scanner.catalog.v1",
        "lifecycle_evidence_relative_path": "lifecycle.jsonl",
        "sources": [
            {
                "dataset_id": "binance-btcusdt-1h",
                "relative_path": "market/BTCUSDT_1h.parquet",
                "venue": "binance",
                "venue_symbol": "BTCUSDT",
                "base_asset": "BTC",
                "quote_asset": "USDT",
                "interval": "1h",
                "expected_semantic_fingerprint": fingerprint,
                "lifecycle_evidence_ids": ["listing-btcusdt"],
                "direct_pair_dataset_ids": [],
            }
        ],
    }
    (tmp_path / "catalog.json").write_text(
        json.dumps(catalog_data),
        encoding="utf-8",
    )

    catalog = load_scanner_catalog(tmp_path)
    resolved = resolve_catalog_source(
        catalog,
        dataset_id="binance-btcusdt-1h",
        data_root=tmp_path,
    )

    assert resolved.spec.dataset_id == "binance-btcusdt-1h"
    assert resolved.series == series
    assert resolved.source_artifact_fingerprint == fingerprint


def test_catalog_rejects_path_escape_and_fingerprint_mismatch(tmp_path: Path) -> None:
    lifecycle_path = tmp_path / "lifecycle.jsonl"
    lifecycle_path.write_text("", encoding="utf-8")
    series = _series(3)
    market_path = tmp_path / "market.parquet"
    fingerprint = write_parquet_bar_series(market_path, series)

    def write_catalog(relative_path: str, expected: str) -> None:
        (tmp_path / "catalog.json").write_text(
            json.dumps(
                {
                    "schema_version": "qap.scanner.catalog.v1",
                    "lifecycle_evidence_relative_path": "lifecycle.jsonl",
                    "sources": [
                        {
                            "dataset_id": "btc",
                            "relative_path": relative_path,
                            "venue": "binance",
                            "venue_symbol": "BTCUSDT",
                            "base_asset": "BTC",
                            "quote_asset": "USDT",
                            "interval": "1h",
                            "expected_semantic_fingerprint": expected,
                            "lifecycle_evidence_ids": [],
                            "direct_pair_dataset_ids": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    write_catalog("../outside.parquet", fingerprint)
    with pytest.raises(ScannerCatalogError, match="safe relative POSIX path"):
        load_scanner_catalog(tmp_path)

    write_catalog("market.parquet", "f" * 64)
    catalog = load_scanner_catalog(tmp_path)
    with pytest.raises(ScannerCatalogError, match="fingerprint mismatch"):
        resolve_catalog_source(catalog, dataset_id="btc", data_root=tmp_path)


def test_catalog_semantic_identity_binds_sources_but_excludes_paths_and_order() -> None:
    first = ScannerSourceSpec(
        dataset_id="btc-usdt",
        relative_path="market/a.parquet",
        venue="binance",
        venue_symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        interval="1h",
        expected_semantic_fingerprint="a" * 64,
        lifecycle_evidence_ids=("btc-listing",),
        direct_pair_dataset_ids=("btc-eth",),
    )
    second = ScannerSourceSpec(
        dataset_id="btc-eth",
        relative_path="market/b.parquet",
        venue="binance",
        venue_symbol="BTCETH",
        base_asset="BTC",
        quote_asset="ETH",
        interval="1h",
        expected_semantic_fingerprint="b" * 64,
    )
    baseline = ScannerCatalog(
        schema_version="qap.scanner.catalog.v1",
        lifecycle_evidence_relative_path="lifecycle/a.jsonl",
        sources=(first, second),
    )
    moved = ScannerCatalog(
        schema_version="qap.scanner.catalog.v1",
        lifecycle_evidence_relative_path="elsewhere/lifecycle.jsonl",
        sources=(
            second.model_copy(update={"relative_path": "moved/direct.parquet"}),
            first.model_copy(update={"relative_path": "moved/evidence.parquet"}),
        ),
    )
    changed = baseline.model_copy(
        update={
            "sources": (
                first,
                second.model_copy(update={"expected_semantic_fingerprint": "f" * 64}),
            )
        }
    )

    assert catalog_semantic_identity(baseline) == catalog_semantic_identity(moved)
    assert catalog_semantic_identity(baseline) != catalog_semantic_identity(changed)


def test_scan_id_binds_slice_and_catalog_but_not_creation_time() -> None:
    evaluated = evaluate_series(
        _series(4),
        dataset_id="btc",
        eligible_information_end=START + timedelta(hours=4),
        lookback=timedelta(hours=4),
    )
    input_identity = ScanInputIdentity(
        dataset_id="btc",
        source_artifact_fingerprint=evaluated.source_artifact_fingerprint,
        selection_slice_fingerprint=evaluated.selection_slice_fingerprint,
    )
    definition = ScanDefinition(
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        catalog_identity="c" * 64,
        as_of=START + timedelta(hours=4),
        eligible_information_end=START + timedelta(hours=4),
        venues=("binance",),
        horizons=(ScannerHorizon.SHORT,),
        input_slices=(input_identity,),
        manual_inputs=(),
        created_at=START + timedelta(days=1),
    )
    later = definition.model_copy(update={"created_at": START + timedelta(days=2)})
    changed_catalog = definition.model_copy(update={"catalog_identity": "d" * 64})
    changed_slice = definition.model_copy(
        update={
            "input_slices": (
                input_identity.model_copy(
                    update={"selection_slice_fingerprint": "f" * 64}
                ),
            )
        }
    )

    assert definition.scan_id == later.scan_id
    assert definition.scan_id != changed_catalog.scan_id
    assert definition.scan_id != changed_slice.scan_id
