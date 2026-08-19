# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

from qap.experiment.artifacts import read_run_artifacts
from qap.experiment.basket_manifest import pair_blind_window_returns
from qap.experiment.data import load_experiment_data
from qap.experiment.manifest import DataRole
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
from qap.relationship.models import cross_sectional_relative_observation
from qap.scanner.artifacts import read_completed_scan
from qap.scanner.asset_momentum_artifacts import read_asset_momentum_generation
from qap.scanner.basket_artifacts import (
    BasketEconomicGateStatus,
    BasketReplayStatus,
    read_basket_generation,
)
from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import (
    generate_asset_momentum,
    run_basket_with_qap,
    run_scan_with_qap,
)

AS_OF = datetime(2026, 7, 1, tzinfo=UTC)
HISTORY = timedelta(days=46)
INTERVAL = BarInterval("1h")
USDT = AssetId("USDT")
ASSETS = (AssetId("AAA"), AssetId("BBB"), AssetId("CCC"))


def _price(asset: AssetId, elapsed_hours: float) -> float:
    if asset == ASSETS[0]:
        return 100.0 * math.exp(
            0.00010 * elapsed_hours + 0.028 * math.sin(elapsed_hours / 8.0)
        )
    if asset == ASSETS[1]:
        return 80.0 * math.exp(
            0.00009 * elapsed_hours
            + 0.024 * math.sin(elapsed_hours / 8.0 + 0.8)
            + 0.007 * math.sin(elapsed_hours / 2.7)
        )
    return 60.0 * math.exp(
        0.00008 * elapsed_hours
        + 0.020 * math.sin(elapsed_hours / 11.0 + 1.3)
        + 0.006 * math.sin(elapsed_hours / 3.1)
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


def _write_fixture(data_root: Path) -> None:
    data_root.mkdir(parents=True)
    start = AS_OF - HISTORY
    events = tuple(
        InstrumentLifecycleEvent(
            canonical_asset_id=asset,
            asset_identity_version=f"{asset.key.lower()}-v1",
            venue="binance",
            venue_symbol=f"{asset.key}USDT",
            quote_asset=USDT,
            event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
            effective_at=start,
            observed_at=start,
            source_type=LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
            source_id=f"fixture-{asset.key.lower()}-listing",
            confidence=LifecycleConfidence.CONFIRMED,
        )
        for asset in ASSETS
    )
    (data_root / "lifecycle.jsonl").write_text(
        "".join(
            json.dumps(_event_payload(event), sort_keys=True) + "\n" for event in events
        ),
        encoding="utf-8",
    )
    event_ids = {event.canonical_asset_id: event.event_id for event in events}

    market_root = data_root / "market"
    market_root.mkdir()
    sources: list[dict[str, object]] = []
    count = HISTORY // INTERVAL.duration
    for asset in ASSETS:
        instrument = VenueInstrument(
            venue="binance",
            venue_symbol=f"{asset.key}USDT",
            base=asset,
            quote=USDT,
        )
        bars = []
        for index in range(count):
            candle_open = start + index * INTERVAL.duration
            elapsed_hours = (candle_open - start).total_seconds() / 3600.0
            close = _price(asset, elapsed_hours)
            bars.append(
                MarketBar(
                    instrument=instrument,
                    interval=INTERVAL,
                    candle_open_time=candle_open,
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=1000.0,
                )
            )
        series = validate_bar_series(tuple(bars))
        dataset_id = f"{asset.key.lower()}-usdt-1h"
        relative_path = f"market/{dataset_id}.parquet"
        write_parquet_bar_series(data_root / relative_path, series)
        sources.append(
            {
                "dataset_id": dataset_id,
                "relative_path": relative_path,
                "venue": "binance",
                "venue_symbol": instrument.venue_symbol,
                "base_asset": asset.key,
                "quote_asset": USDT.key,
                "interval": INTERVAL.label,
                "expected_semantic_fingerprint": fingerprint_bar_series(series),
                "lifecycle_evidence_ids": [event_ids[asset]],
                "direct_pair_dataset_ids": (
                    ["aaa-bbb-1h"] if asset in {ASSETS[0], ASSETS[1]} else []
                ),
            }
        )
    direct_instrument = VenueInstrument(
        venue="binance",
        venue_symbol="AAABBB",
        base=ASSETS[0],
        quote=ASSETS[1],
    )
    direct_bars = []
    for index in range(count):
        candle_open = start + index * INTERVAL.duration
        elapsed_hours = (candle_open - start).total_seconds() / 3600.0
        close = _price(ASSETS[0], elapsed_hours) / _price(ASSETS[1], elapsed_hours)
        direct_bars.append(
            MarketBar(
                instrument=direct_instrument,
                interval=INTERVAL,
                candle_open_time=candle_open,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000.0,
            )
        )
    direct_series = validate_bar_series(tuple(direct_bars))
    direct_relative_path = "market/aaa-bbb-1h.parquet"
    write_parquet_bar_series(data_root / direct_relative_path, direct_series)
    sources.append(
        {
            "dataset_id": "aaa-bbb-1h",
            "relative_path": direct_relative_path,
            "venue": "binance",
            "venue_symbol": direct_instrument.venue_symbol,
            "base_asset": ASSETS[0].key,
            "quote_asset": ASSETS[1].key,
            "interval": INTERVAL.label,
            "expected_semantic_fingerprint": fingerprint_bar_series(direct_series),
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


def test_slice3_completed_scan_momentum_and_manual_basket_reach_ordinary_qap(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    run_root = tmp_path / "runs"
    _write_fixture(data_root)

    scan = run_scan_with_qap(
        as_of=AS_OF,
        horizons=(ScannerHorizon.SHORT,),
        data_root=data_root,
        run_root=run_root,
    )
    _definition, tables = read_completed_scan(scan.artifact_directory)
    attempts = {
        str(row["candidate_id"]): row for row in tables["replay_attempts.parquet"]
    }
    direct_candidate = next(
        row
        for row in tables["scout_trials.parquet"]
        if row["trial_status"] == "valid"
        and row["resolution"] == "1h"
        and row["template_id"] == "fast"
        and row["model_family"] == "log_ratio_mean_reversion"
        and attempts.get(str(row["candidate_id"]), {}).get("attempt_status")
        == "completed"
    )
    candidate = next(
        row
        for row in tables["scout_trials.parquet"]
        if row["trial_status"] == "valid"
        and row["resolution"] == "1h"
        and row["template_id"] == "fast"
        and row["model_family"] == "log_ratio_mean_reversion"
        and row["pair_id"] != "AAA/BBB"
    )
    negative_candidate = min(
        (
            row
            for row in tables["scout_trials.parquet"]
            if row["trial_status"] == "valid"
            and row["resolution"] == "1h"
            and row["template_id"] == "fast"
            and row["scout_relative_wealth_proxy"] is not None
            and row["scout_relative_wealth_proxy"] < 0
        ),
        key=lambda row: row["scout_relative_wealth_proxy"],
    )

    momentum_directory = generate_asset_momentum(
        scan_id=scan.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        data_root=data_root,
        run_root=run_root,
    )
    momentum, snapshot = read_asset_momentum_generation(momentum_directory)
    assert momentum.source_scan_id == scan.scan_id
    assert momentum.resolution == "1h"
    assert momentum.formation_seconds == int(timedelta(days=2).total_seconds())
    assert len(momentum.observations) == len(snapshot.records) == 3

    basket_directory = run_basket_with_qap(
        scan_id=scan.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        decision_resolution="1h",
        economic_assets=tuple(asset.key for asset in ASSETS),
        candidate_ids=(str(candidate["candidate_id"]),),
        momentum_scan_id=momentum.momentum_scan_id,
        data_root=data_root,
        run_root=run_root,
        repository_root=Path(__file__).resolve().parents[2],
        run_timestamp=AS_OF + timedelta(days=1),
    )
    basket, attempt, _manifest = read_basket_generation(basket_directory)
    assert basket.source_momentum_scan_id == momentum.momentum_scan_id
    assert basket.selected_edges[0].pair_id != "AAA/BBB"
    assert basket.selected_edges[0].scout_status == "valid"
    assert attempt.status is BasketReplayStatus.COMPLETED
    assert attempt.qap_run_id is not None
    assert attempt.economic_gate_status is BasketEconomicGateStatus.DEVELOPMENT_SURVIVOR

    qap = read_run_artifacts(run_root / attempt.qap_run_id)
    evaluation_start = qap.manifest.effective_evaluation_window().start
    loaded = load_experiment_data(qap.manifest, data_root=data_root)
    window_returns = pair_blind_window_returns(
        qap.manifest.policy.config,
        qap.manifest.interval,
    )
    momentum_observation = cross_sectional_relative_observation(
        loaded.aligned,
        basket=tuple(qap.manifest.asset(key) for key in qap.manifest.basket),
        window_returns=window_returns,
        as_of=evaluation_start,
    )
    assert momentum_observation.coverage_returns == window_returns == 48
    first_reasons: dict[str, str] = {}
    for event in qap.events:
        if (
            event["event_type"] != "policy_decision"
            or event["event_time"] != evaluation_start.isoformat()
            or event["role"] not in {"strategy", "control:relative-momentum-short"}
        ):
            continue
        payload = event["payload"]
        assert isinstance(payload, dict)
        first_reasons[str(event["role"])] = str(payload["reason"])
    assert first_reasons.keys() == {"strategy", "control:relative-momentum-short"}
    assert "insufficient_evidence" not in first_reasons.values()

    mixed_directory = run_basket_with_qap(
        scan_id=scan.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        decision_resolution="1h",
        economic_assets=tuple(asset.key for asset in ASSETS),
        candidate_ids=(
            str(direct_candidate["candidate_id"]),
            str(candidate["candidate_id"]),
        ),
        momentum_scan_id=momentum.momentum_scan_id,
        data_root=data_root,
        run_root=run_root,
        repository_root=Path(__file__).resolve().parents[2],
        run_timestamp=AS_OF + timedelta(days=1),
    )
    mixed_basket, mixed_attempt, _mixed_manifest = read_basket_generation(
        mixed_directory
    )
    assert mixed_attempt.status is BasketReplayStatus.COMPLETED
    assert mixed_attempt.qap_run_id is not None
    assert {edge.deep_replay_status for edge in mixed_basket.selected_edges} == {
        "completed",
        None,
    }
    assert any(
        edge.pair_id != "AAA/BBB" and edge.deep_replay_status is None
        for edge in mixed_basket.selected_edges
    )

    repeated = run_basket_with_qap(
        scan_id=scan.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        decision_resolution="1h",
        economic_assets=tuple(asset.key for asset in ASSETS),
        candidate_ids=(str(candidate["candidate_id"]),),
        momentum_scan_id=momentum.momentum_scan_id,
        data_root=data_root,
        run_root=run_root,
        repository_root=Path(__file__).resolve().parents[2],
        run_timestamp=AS_OF + timedelta(days=2),
    )
    assert repeated == basket_directory

    negative_directory = run_basket_with_qap(
        scan_id=scan.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        decision_resolution="1h",
        economic_assets=tuple(asset.key for asset in ASSETS),
        candidate_ids=(str(negative_candidate["candidate_id"]),),
        momentum_scan_id=momentum.momentum_scan_id,
        data_root=data_root,
        run_root=run_root,
        repository_root=Path(__file__).resolve().parents[2],
        run_timestamp=AS_OF + timedelta(days=1),
    )
    _negative_basket, negative_attempt, _negative_manifest = read_basket_generation(
        negative_directory
    )
    assert negative_attempt.status is BasketReplayStatus.COMPLETED
    assert negative_attempt.economic_gate_status is (
        BasketEconomicGateStatus.DEVELOPMENT_REJECTED
    )
    assert negative_attempt.qap_run_id is not None

    qap = read_run_artifacts(run_root / negative_attempt.qap_run_id)
    assert qap.result.data_role is DataRole.DEVELOPMENT
    assert qap.result.final_oos_consumed is False
    assert {role.role for role in qap.result.roles} >= {
        "hodl",
        "strategy",
        "control:band-5pct-half",
        "control:relative-momentum-short",
    }
