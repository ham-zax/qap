# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from qap.market import (
    BarInterval,
    InstrumentLifecycleEvent,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    MarketBar,
    VenueInstrument,
    fingerprint_bar_series,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId
from qap.scanner.models import ScannerPinSpec
from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import run_scan_with_qap

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
AS_OF = datetime(2024, 3, 1, tzinfo=UTC)
HISTORY = timedelta(days=46)
RESERVED_FINAL_OOS_FINGERPRINT = (
    "b3069c70fb61f1e7fb6a8b1d338194817ba8896dfd2618b96091c8c46686f2a5"
)


def _price(asset: AssetId, elapsed_hours: float) -> float:
    if asset == BTC:
        return 100.0 * math.exp(
            0.00015 * elapsed_hours + 0.035 * math.sin(elapsed_hours / 8.0)
        )
    return 50.0 * math.exp(
        0.00011 * elapsed_hours
        + 0.028 * math.sin(elapsed_hours / 8.0 + 0.9)
        + 0.009 * math.sin(elapsed_hours / 2.5)
    )


def _series(
    *,
    instrument: VenueInstrument,
    interval: BarInterval,
):
    start = AS_OF - HISTORY
    count = HISTORY // interval.duration
    bars = []
    for index in range(count):
        candle_open = start + index * interval.duration
        elapsed_hours = (candle_open - start).total_seconds() / 3600.0
        if instrument.base == BTC and instrument.quote == ETH:
            close = _price(BTC, elapsed_hours) / _price(ETH, elapsed_hours)
        else:
            close = _price(instrument.base, elapsed_hours)
        bars.append(
            MarketBar(
                instrument=instrument,
                interval=interval,
                candle_open_time=candle_open,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000.0,
            )
        )
    return validate_bar_series(tuple(bars))


def _lifecycle_event(
    asset: AssetId,
    *,
    effective_at: datetime | None = None,
) -> InstrumentLifecycleEvent:
    lifecycle_start = AS_OF - HISTORY if effective_at is None else effective_at
    return InstrumentLifecycleEvent(
        canonical_asset_id=asset,
        asset_identity_version=f"{asset.key.lower()}-v1",
        venue="binance",
        venue_symbol=f"{asset.key}USDT",
        quote_asset=USDT,
        event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
        effective_at=lifecycle_start,
        observed_at=lifecycle_start,
        source_type=LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
        source_id=f"fixture-{asset.key.lower()}-listing",
        confidence=LifecycleConfidence.CONFIRMED,
    )


def _event_payload(event: InstrumentLifecycleEvent) -> dict[str, object]:
    return {
        "schema_version": "qap.market.lifecycle-event.v1",
        "canonical_asset_id": event.canonical_asset_id.key,
        "asset_identity_version": event.asset_identity_version,
        "venue": event.venue,
        "venue_symbol": event.venue_symbol,
        "quote_asset": event.quote_asset.key,
        "event_type": event.event_type.value,
        "effective_at": event.effective_at.isoformat(),
        "observed_at": event.observed_at.isoformat(),
        "source_type": event.source_type.value,
        "source_id": event.source_id,
        "confidence": event.confidence.value,
        "continuity": None,
    }


def _write_fixture(
    data_root: Path,
    *,
    include_direct: bool,
    unknown_eth_lifecycle: bool = False,
    lifecycle_start: datetime | None = None,
) -> None:
    data_root.mkdir(parents=True)
    events = (
        _lifecycle_event(BTC, effective_at=lifecycle_start),
        _lifecycle_event(ETH, effective_at=lifecycle_start),
    )
    (data_root / "lifecycle.jsonl").write_text(
        "".join(
            json.dumps(_event_payload(event), sort_keys=True) + "\n" for event in events
        ),
        encoding="utf-8",
    )
    event_id_by_asset = {event.canonical_asset_id: event.event_id for event in events}

    sources: list[dict[str, object]] = []
    market_root = data_root / "market"
    market_root.mkdir()
    for interval in (BarInterval("1h"),):
        for asset in (BTC, ETH):
            instrument = VenueInstrument(
                venue="binance",
                venue_symbol=f"{asset.key}USDT",
                base=asset,
                quote=USDT,
            )
            series = _series(instrument=instrument, interval=interval)
            dataset_id = f"{asset.key.lower()}-usdt-{interval.label}"
            relative = f"market/{dataset_id}.parquet"
            write_parquet_bar_series(data_root / relative, series)
            sources.append(
                {
                    "dataset_id": dataset_id,
                    "relative_path": relative,
                    "venue": "binance",
                    "venue_symbol": instrument.venue_symbol,
                    "base_asset": asset.key,
                    "quote_asset": "USDT",
                    "interval": interval.label,
                    "expected_semantic_fingerprint": fingerprint_bar_series(series),
                    "lifecycle_evidence_ids": (
                        []
                        if unknown_eth_lifecycle and asset == ETH
                        else [event_id_by_asset[asset]]
                    ),
                    "direct_pair_dataset_ids": (
                        [f"btc-eth-{interval.label}"] if include_direct else []
                    ),
                }
            )
        if include_direct:
            direct = VenueInstrument(
                venue="binance",
                venue_symbol="BTCETH",
                base=BTC,
                quote=ETH,
            )
            series = _series(instrument=direct, interval=interval)
            dataset_id = f"btc-eth-{interval.label}"
            relative = f"market/{dataset_id}.parquet"
            write_parquet_bar_series(data_root / relative, series)
            sources.append(
                {
                    "dataset_id": dataset_id,
                    "relative_path": relative,
                    "venue": "binance",
                    "venue_symbol": "BTCETH",
                    "base_asset": "BTC",
                    "quote_asset": "ETH",
                    "interval": interval.label,
                    "expected_semantic_fingerprint": fingerprint_bar_series(series),
                    "lifecycle_evidence_ids": [],
                    "direct_pair_dataset_ids": [],
                }
            )

    (data_root / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": "qap.scanner.catalog.v1",
                "lifecycle_evidence_relative_path": "lifecycle.jsonl",
                "sources": sources,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_scanner_short_horizon_direct_market_reaches_authoritative_replay(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(data_root, include_direct=True)

    result = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
        pins=(),
    )

    assert result.artifact_directory.is_dir()
    assert result.scan_id == result.artifact_directory.name
    neighbors = pq.read_table(
        result.artifact_directory / "neighbors.parquet"
    ).to_pylist()
    graph_metadata = pq.read_table(
        result.artifact_directory / "graph_metadata.parquet"
    ).to_pylist()
    eligible = pq.read_table(
        result.artifact_directory / "eligible_assets.parquet"
    ).to_pylist()
    scouts = pq.read_table(
        result.artifact_directory / "scout_trials.parquet"
    ).to_pylist()
    promotions = pq.read_table(
        result.artifact_directory / "promotions.parquet"
    ).to_pylist()
    attempts = pq.read_table(
        result.artifact_directory / "replay_attempts.parquet"
    ).to_pylist()
    assert {(row["venue"], row["pair_id"]) for row in neighbors} == {
        ("binance", "BTC/ETH")
    }
    assert len(graph_metadata) == 1
    graph_row = graph_metadata[0]
    assert graph_row["eligible_asset_count"] == 2
    assert graph_row["total_valid_pair_comparisons"] == 1
    assert graph_row["neighbors_per_asset"] == 8
    assert len(graph_row["distance_digest"]) == 64
    assert set(graph_row["input_selection_slice_fingerprints"]) == {
        row["selection_slice_fingerprint"]
        for row in eligible
        if row["automatic_eligible"]
    }
    assert len(scouts) == 18
    assert sum(row["trial_status"] == "invalid" for row in scouts) == 9
    assert {
        row["failure_reason"] for row in scouts if row["trial_status"] == "invalid"
    } == {"model_source_unavailable"}
    assert sum(bool(row["automatic_selected"]) for row in promotions) <= 10
    assert attempts
    assert all(row["attempt_status"] == "completed" for row in attempts)
    assert all(row["deep_replay_run_id"] for row in attempts)
    assert all(
        row["economic_gate_status"] in {"deep_replay_survivor", "deep_replay_rejected"}
        for row in promotions
        if row["selected_for_replay"]
    )


def test_model_warmup_before_lifecycle_eligibility_is_not_promotable(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(
        data_root,
        include_direct=True,
        lifecycle_start=AS_OF - timedelta(days=30),
    )

    result = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
        pins=(),
    )

    scouts = pq.read_table(
        result.artifact_directory / "scout_trials.parquet"
    ).to_pylist()
    assert len(scouts) == 18
    assert {row["trial_status"] for row in scouts} == {"invalid"}
    assert {row["failure_reason"] for row in scouts} == {
        "model_source_unavailable",
        "model_lifecycle_ineligible",
    }
    promotions = pq.read_table(
        result.artifact_directory / "promotions.parquet"
    ).to_pylist()
    assert promotions == []


def test_forensic_pin_can_research_unknown_asset_without_automatic_promotion(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(
        data_root,
        include_direct=False,
        unknown_eth_lifecycle=True,
    )
    pin = ScannerPinSpec(
        venue="binance",
        asset_a="BTC",
        asset_b="ETH",
        horizons=(ScannerHorizon.SHORT,),
        forensic=True,
    )

    result = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
        pins=(pin,),
    )

    eligible = pq.read_table(
        result.artifact_directory / "eligible_assets.parquet"
    ).to_pylist()
    eth = next(row for row in eligible if row["asset_id"] == "ETH")
    assert eth["eligibility_state"] == "historical_eligibility_unknown"
    assert eth["automatic_eligible"] is False
    assert eth["forensic_research_allowed"] is True
    neighbors = pq.read_table(
        result.artifact_directory / "neighbors.parquet"
    ).to_pylist()
    assert len(neighbors) == 1
    assert neighbors[0]["manual_pinned"] is True
    assert neighbors[0]["automatic_neighbor_selected"] is False
    promotions = pq.read_table(
        result.artifact_directory / "promotions.parquet"
    ).to_pylist()
    assert promotions == []


def test_scanner_unsupported_cross_stays_in_durable_attempt_denominator(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(data_root, include_direct=False)

    result = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
        pins=(),
    )

    scouts = pq.read_table(
        result.artifact_directory / "scout_trials.parquet"
    ).to_pylist()
    promotions = pq.read_table(
        result.artifact_directory / "promotions.parquet"
    ).to_pylist()
    attempts = pq.read_table(
        result.artifact_directory / "replay_attempts.parquet"
    ).to_pylist()
    selected_ids = {
        row["candidate_id"] for row in promotions if row["selected_for_replay"]
    }
    assert selected_ids
    assert {row["candidate_id"] for row in attempts} == selected_ids
    assert {row["attempt_status"] for row in attempts} == {"setup_failed"}
    assert {row["failure_reason"] for row in attempts} == {"unsupported_direct_market"}
    assert any(
        row["trial_status"] == "valid"
        and row["scout_relative_wealth_proxy"] is not None
        for row in scouts
    )


def test_explicit_manual_replay_is_outside_automatic_budget(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_fixture(data_root, include_direct=True)
    baseline = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=tmp_path / "baseline-runs",
        pins=(),
    )
    baseline_promotions = pq.read_table(
        baseline.artifact_directory / "promotions.parquet"
    ).to_pylist()
    manual_candidate_id = next(
        row["candidate_id"]
        for row in baseline_promotions
        if not row["selected_for_replay"]
    )

    manual = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=tmp_path / "manual-runs",
        pins=(),
        manual_replay_candidate_ids=(manual_candidate_id,),
    )
    manual_promotions = pq.read_table(
        manual.artifact_directory / "promotions.parquet"
    ).to_pylist()
    selected = next(
        row for row in manual_promotions if row["candidate_id"] == manual_candidate_id
    )
    attempts = pq.read_table(
        manual.artifact_directory / "replay_attempts.parquet"
    ).to_pylist()

    assert manual.scan_id != baseline.scan_id
    assert selected["automatic_selected"] is False
    assert selected["manual_selected"] is True
    assert selected["selected_for_replay"] is True
    assert manual_candidate_id in {row["candidate_id"] for row in attempts}


def test_scanner_rejects_reserved_final_oos_before_source_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(data_root, include_direct=True)
    catalog_path = data_root / "catalog.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["sources"][0]["expected_semantic_fingerprint"] = (
        RESERVED_FINAL_OOS_FINGERPRINT
    )
    catalog_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    import qap.scanner.catalog as scanner_catalog

    def fail_if_reader_runs(_path: Path) -> object:
        raise AssertionError("reserved final-OOS source reader was invoked")

    monkeypatch.setattr(scanner_catalog, "read_parquet_bar_series", fail_if_reader_runs)

    with pytest.raises(ValueError, match="reserved final-OOS"):
        run_scan_with_qap(
            as_of=AS_OF,
            horizons=(ScannerHorizon.SHORT,),
            data_root=data_root,
            run_root=run_root,
            pins=(),
        )
