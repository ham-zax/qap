# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""No-network vertical evidence for scanner prospective Slice 2."""

import json
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest
import test_scanner_slice1 as slice1_fixture

from qap.market import (
    BookLevel,
    MarketBar,
    MarketMetadata,
    PublicBookSnapshot,
    VenueInstrument,
    fingerprint_bar_series,
    read_parquet_bar_series,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.market.microstructure_storage import (
    write_public_book_snapshots,
    write_public_market_metadata_snapshots,
)
from qap.market.public_capture import CaptureKind, capture_file
from qap.portfolio import AssetId
from qap.scanner.catalog import load_scanner_catalog
from qap.scanner.prospective import ForwardOutcomeStatus, enroll_forward_cohort
from qap.scanner.prospective_artifacts import start_forward_cohort
from qap.scanner.prospective_integrity import read_manifest, read_outcome
from qap.scanner.prospective_run import cohort_scoreboard
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.qualification_artifacts import read_qualification
from qap.scanner_entry import (
    advance_forward_with_qap,
    freeze_scan_with_qap,
    qualify_forward_with_qap,
    run_scan_with_qap,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
AS_OF = slice1_fixture.AS_OF
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _fixture_price(asset: AssetId, elapsed_hours: float) -> float:
    if asset == BTC:
        return 100.0 + elapsed_hours * 0.03 + math.sin(elapsed_hours / 11.0) * 2.0
    return 50.0 + elapsed_hours * 0.012 + math.cos(elapsed_hours / 13.0) * 1.2


def _manual_survivor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path]:
    monkeypatch.setattr(slice1_fixture, "_price", _fixture_price)
    data_root = tmp_path / "data"
    discovery_root = tmp_path / "discovery"
    run_root = tmp_path / "runs"
    slice1_fixture._write_fixture(data_root, include_direct=True)
    discovery = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=discovery_root,
        pins=(),
    )
    scouts = pq.read_table(
        discovery.artifact_directory / "scout_trials.parquet"
    ).to_pylist()
    target = next(
        row
        for row in scouts
        if row["trial_status"] == "valid"
        and row["model_family"] == "log_ratio_mean_reversion"
        and row["template_id"] == "fast"
        and row["resolution"] == "1h"
    )
    scan = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
        pins=(),
        manual_replay_candidate_ids=(target["candidate_id"],),
    )
    promotions = pq.read_table(
        scan.artifact_directory / "promotions.parquet"
    ).to_pylist()
    selected = next(
        row for row in promotions if row["candidate_id"] == target["candidate_id"]
    )
    assert selected["manual_selected"] is True
    assert selected["economic_gate_status"] == "deep_replay_survivor"
    cohort_root = freeze_scan_with_qap(
        run_root=run_root,
        data_root=data_root,
        prospective_root=run_root,
        scan_id=scan.scan_id,
        horizon=ScannerHorizon.SHORT,
        freeze_at=AS_OF,
    )
    return data_root, run_root, cohort_root


def _append_forward_data(data_root: Path, *, hours: int = 8):
    document = json.loads((data_root / "catalog.json").read_text(encoding="utf-8"))
    sources = {item["dataset_id"]: item for item in document["sources"]}
    for source in document["sources"]:
        path = data_root / source["relative_path"]
        existing = read_parquet_bar_series(path)
        bars = list(existing.bars)
        for offset in range(hours):
            elapsed = len(existing.bars) + offset
            instrument = existing.instrument
            close = (
                _fixture_price(BTC, elapsed) / _fixture_price(ETH, elapsed)
                if instrument.base == BTC and instrument.quote == ETH
                else _fixture_price(instrument.base, elapsed)
            )
            bars.append(
                MarketBar(
                    instrument=instrument,
                    interval=existing.interval,
                    candle_open_time=AS_OF + offset * existing.interval.duration,
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=1000.0,
                )
            )
        updated = validate_bar_series(tuple(bars))
        forward_relative = f"market/{source['dataset_id']}-forward.parquet"
        write_parquet_bar_series(data_root / forward_relative, updated)
        sources[source["dataset_id"]]["relative_path"] = forward_relative
        sources[source["dataset_id"]]["expected_semantic_fingerprint"] = (
            fingerprint_bar_series(updated)
        )
    (data_root / "catalog.json").write_text(
        json.dumps(document, sort_keys=True), encoding="utf-8"
    )
    return load_scanner_catalog(data_root)


def _metadata(instrument: VenueInstrument) -> MarketMetadata:
    return MarketMetadata(
        instrument=instrument,
        status="TRADING",
        price_tick=Decimal("0.0001"),
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


def _write_metadata_only(capture_root: Path, *, as_of: datetime, price: float) -> None:
    instrument = VenueInstrument(
        venue="binance", venue_symbol="BTCETH", base=BTC, quote=ETH
    )
    snapshot = public_market_metadata_snapshot_from_metadata(
        metadata=_metadata(instrument),
        observed_at=as_of,
        source_id="scenario:metadata",
    )
    write_public_market_metadata_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.METADATA,
        ),
        (snapshot,),
    )


def _write_full_capture(capture_root: Path, *, as_of: datetime, mid: float) -> None:
    instrument = VenueInstrument(
        venue="binance", venue_symbol="BTCETH", base=BTC, quote=ETH
    )
    start = as_of - timedelta(days=14)
    bid = mid * (1.0 - 0.0001)
    ask = mid * (1.0 + 0.0001)

    def snapshot(observed_at: datetime, fingerprint: str) -> PublicBookSnapshot:
        return PublicBookSnapshot(
            instrument=instrument,
            observed_at=observed_at,
            source_id="scenario:book",
            source_fingerprint=fingerprint,
            bids=(BookLevel(price=bid, quantity=1_000_000.0),),
            asks=(BookLevel(price=ask, quantity=1_000_000.0),),
        )

    l1 = tuple(
        snapshot(start + index * timedelta(minutes=1), "1" * 64)
        for index in range(14 * 24 * 60)
    )
    depth = tuple(
        snapshot(start + index * timedelta(minutes=5), "2" * 64)
        for index in range(14 * 24 * 12)
    )
    write_public_book_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.L1,
        ),
        l1,
    )
    write_public_book_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.DEPTH,
        ),
        depth,
    )
    _write_metadata_only(capture_root, as_of=as_of, price=mid)


def test_slice2_vertical_freeze_advance_qualify_and_scoreboard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root, run_root, cohort_root = _manual_survivor(tmp_path, monkeypatch)
    catalog = _append_forward_data(data_root)
    checkpoints = advance_forward_with_qap(
        cohort_root=cohort_root,
        catalog=catalog,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        through=AS_OF + timedelta(hours=8),
        run_timestamp=datetime(2026, 8, 18, 2, 0, tzinfo=UTC),
    )
    assert len(checkpoints) == 1
    outcome = read_outcome(checkpoints[0])
    assert outcome.status is ForwardOutcomeStatus.PARTIAL
    assert outcome.qap_run_id is not None
    checkpoint_id = read_manifest(checkpoints[0])["checkpoint_id"]
    assert isinstance(checkpoint_id, str)

    missing_capture = tmp_path / "capture-missing"
    _write_metadata_only(missing_capture, as_of=outcome.through, price=2.0)
    missing = qualify_forward_with_qap(
        cohort_root=cohort_root,
        checkpoint_id=checkpoint_id,
        requested_capital=Decimal("10"),
        catalog=catalog,
        data_root=data_root,
        capture_root=missing_capture,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
    )
    missing_record = read_qualification(missing)
    assert missing_record["state"] == "research_only"
    assert missing_record["reason"] == "microstructure_coverage_insufficient"

    direct = catalog.source("btc-eth-1h")
    series = read_parquet_bar_series(data_root / direct.relative_path)
    current = next(
        bar for bar in series.bars if bar.bar_end_exclusive == outcome.through
    )
    full_capture = tmp_path / "capture-full"
    _write_full_capture(full_capture, as_of=outcome.through, mid=current.close)
    qualified = qualify_forward_with_qap(
        cohort_root=cohort_root,
        checkpoint_id=checkpoint_id,
        requested_capital=Decimal("10"),
        catalog=catalog,
        data_root=data_root,
        capture_root=full_capture,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        run_timestamp=datetime(2026, 8, 18, 3, 0, tzinfo=UTC),
    )
    record = read_qualification(qualified)
    assert record["request"]["capture_contract_satisfied"] is True
    assert record["state"] == "tradable_now"
    assert record["reason"] == "all_current_evidence_satisfied"
    assert record["request"]["requested_capital_qap_run_id"] is not None

    scoreboard = cohort_scoreboard(cohort_root)
    assert scoreboard["manual_selected_count"] == 1
    assert scoreboard["new_freeze_count"] == 1
    assert scoreboard["outcome_state_counts"] == {"partial": 1}
    assert scoreboard["qualification_count"] == 2


def test_slice2_zero_member_cohort_and_prospective_failure_remain_visible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty = enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=AS_OF,
        selected_freezes=(),
    )
    empty_root = start_forward_cohort(tmp_path / "empty-runs", empty)
    assert cohort_scoreboard(empty_root)["new_freeze_count"] == 0

    data_root, run_root, cohort_root = _manual_survivor(
        tmp_path / "failure", monkeypatch
    )
    catalog = _append_forward_data(data_root)
    partial = advance_forward_with_qap(
        cohort_root=cohort_root,
        catalog=catalog,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        through=AS_OF + timedelta(hours=8),
        run_timestamp=datetime(2026, 8, 18, 2, 0, tzinfo=UTC),
    )
    assert len(partial) == 1
    assert read_outcome(partial[0]).status is ForwardOutcomeStatus.PARTIAL

    failed = advance_forward_with_qap(
        cohort_root=cohort_root,
        catalog=catalog,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        through=AS_OF + timedelta(hours=10),
        run_timestamp=datetime(2026, 8, 18, 3, 0, tzinfo=UTC),
    )
    assert len(failed) == 1
    invalid = read_outcome(failed[0])
    assert invalid.status is ForwardOutcomeStatus.INVALID
    assert invalid.failure_reason is not None
    assert invalid.failure_reason.startswith("ExperimentSetupError:")
    assert cohort_scoreboard(cohort_root)["outcome_state_counts"] == {
        "invalid": 1,
        "partial": 1,
    }


def test_slice2_unfillable_book_remains_fail_closed() -> None:
    from qap.scanner.liquidity import BookSide, BookWalkStatus, walk_quote_notional

    instrument = VenueInstrument(
        venue="binance", venue_symbol="BTCETH", base=BTC, quote=ETH
    )
    book = PublicBookSnapshot(
        instrument=instrument,
        observed_at=AS_OF,
        source_id="scenario:shallow",
        source_fingerprint="3" * 64,
        bids=(BookLevel(price=1.99, quantity=1.0),),
        asks=(BookLevel(price=2.01, quantity=1.0),),
    )
    result = walk_quote_notional(
        book,
        side=BookSide.BUY_BASE,
        quote_notional=Decimal("1000"),
    )
    assert result.status is BookWalkStatus.UNFILLABLE
