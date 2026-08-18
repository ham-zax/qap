# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pyarrow.parquet as pq

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
from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import run_scan_with_qap

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
AS_OF = datetime(2024, 3, 1, tzinfo=UTC)
HISTORY = timedelta(days=46)


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


def _lifecycle_event(asset: AssetId) -> InstrumentLifecycleEvent:
    return InstrumentLifecycleEvent(
        canonical_asset_id=asset,
        asset_identity_version=f"{asset.key.lower()}-v1",
        venue="binance",
        venue_symbol=f"{asset.key}USDT",
        quote_asset=USDT,
        event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
        effective_at=AS_OF - HISTORY,
        observed_at=AS_OF - HISTORY,
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


def _write_fixture(data_root: Path, *, include_direct: bool) -> None:
    data_root.mkdir(parents=True)
    events = (_lifecycle_event(BTC), _lifecycle_event(ETH))
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
                    "lifecycle_evidence_ids": [event_id_by_asset[asset]],
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
