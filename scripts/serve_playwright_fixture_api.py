"""Serve deterministic local evidence for the critical browser E2E flows."""

import json
import math
import shutil
from argparse import ArgumentParser
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn

from qap.api import ApiSettings, create_app
from qap.experiment import load_manifest, run_experiment_to_artifacts
from qap.market import (
    BookLevel,
    InstrumentLifecycleEvent,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    MarketBar,
    MarketMetadata,
    PublicBookSnapshot,
    ValidatedBarSeries,
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
from qap.scanner.artifacts import read_completed_scan
from qap.scanner.asset_momentum_artifacts import read_asset_momentum_generation
from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import generate_asset_momentum, run_scan_with_qap

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
_RUN_TIMESTAMP = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
_SCANNER_AS_OF = datetime(2024, 1, 1, tzinfo=UTC)
_ADVANCE_THROUGH = _SCANNER_AS_OF + timedelta(days=7)
_QUALIFICATION_AS_OF = _SCANNER_AS_OF + timedelta(days=15)
_SCANNER_ASSETS = (AssetId("BTC"), AssetId("ETH"), AssetId("SOL"))
_USDT = AssetId("USDT")


def _lifecycle_payload(event: InstrumentLifecycleEvent) -> dict[str, object]:
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


def _scanner_data(data_root: Path):
    market_root = data_root / "market"
    market_root.mkdir(parents=True, exist_ok=True)
    events: list[InstrumentLifecycleEvent] = []
    sources: list[dict[str, object]] = []
    series_by_asset: dict[AssetId, ValidatedBarSeries] = {}
    for index, asset in enumerate(_SCANNER_ASSETS):
        original = read_parquet_bar_series(
            _ROOT / "tests/fixtures/market" / f"{asset.key}USDT_1d_2023.parquet"
        )
        bars = list(original.bars)
        last_close = bars[-1].close
        for day in range(40):
            candle_open = _SCANNER_AS_OF + timedelta(days=day)
            factor = (
                1.0 + 0.0008 * (index + 1) + 0.002 * math.sin((day + 1) / (3.0 + index))
            )
            close = last_close * factor
            bars.append(
                MarketBar(
                    instrument=original.instrument,
                    interval=original.interval,
                    candle_open_time=candle_open,
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=1000.0,
                )
            )
            last_close = close
        series = validate_bar_series(tuple(bars))
        series_by_asset[asset] = series
        relative_path = f"market/{asset.key}USDT_1d.parquet"
        write_parquet_bar_series(data_root / relative_path, series)
        event = InstrumentLifecycleEvent(
            canonical_asset_id=asset,
            asset_identity_version=f"{asset.key.lower()}-v1",
            venue="binance",
            venue_symbol=f"{asset.key}USDT",
            quote_asset=_USDT,
            event_type=LifecycleEventType.LISTING_OR_TRADING_STARTED,
            effective_at=datetime(2022, 1, 1, tzinfo=UTC),
            observed_at=datetime(2022, 1, 1, tzinfo=UTC),
            source_type=LifecycleSourceType.OFFICIAL_EXCHANGE_ANNOUNCEMENT,
            source_id=f"fixture-{asset.key.lower()}-listing",
            confidence=LifecycleConfidence.CONFIRMED,
        )
        events.append(event)
        sources.append(
            {
                "dataset_id": f"{asset.key.lower()}-usdt-1d",
                "relative_path": relative_path,
                "venue": "binance",
                "venue_symbol": f"{asset.key}USDT",
                "base_asset": asset.key,
                "quote_asset": _USDT.key,
                "interval": "1d",
                "expected_semantic_fingerprint": fingerprint_bar_series(series),
                "lifecycle_evidence_ids": [event.event_id],
                "direct_pair_dataset_ids": (
                    ["btc-eth-1d"] if asset.key in {"BTC", "ETH"} else []
                ),
            }
        )

    direct_instrument = VenueInstrument(
        venue="binance",
        venue_symbol="BTCETH",
        base=AssetId("BTC"),
        quote=AssetId("ETH"),
    )
    direct_bars: list[MarketBar] = []
    for btc, eth in zip(
        series_by_asset[AssetId("BTC")].bars,
        series_by_asset[AssetId("ETH")].bars,
        strict=True,
    ):
        close = btc.close / eth.close
        direct_bars.append(
            MarketBar(
                instrument=direct_instrument,
                interval=btc.interval,
                candle_open_time=btc.candle_open_time,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000.0,
            )
        )
    direct = validate_bar_series(tuple(direct_bars))
    write_parquet_bar_series(data_root / "market/BTCETH_1d.parquet", direct)
    sources.append(
        {
            "dataset_id": "btc-eth-1d",
            "relative_path": "market/BTCETH_1d.parquet",
            "venue": "binance",
            "venue_symbol": "BTCETH",
            "base_asset": "BTC",
            "quote_asset": "ETH",
            "interval": "1d",
            "expected_semantic_fingerprint": fingerprint_bar_series(direct),
            "lifecycle_evidence_ids": [],
            "direct_pair_dataset_ids": [],
        }
    )
    (data_root / "lifecycle.jsonl").write_text(
        "".join(
            json.dumps(_lifecycle_payload(event), sort_keys=True) + "\n"
            for event in events
        ),
        encoding="utf-8",
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
    return direct


def _market_metadata(instrument: VenueInstrument) -> MarketMetadata:
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


def _fixture_binance_exchange_info(symbol: str) -> dict[str, object]:
    if symbol.strip().upper() != "BTCETH":
        return {"symbols": []}
    return {
        "timezone": "UTC",
        "serverTime": 0,
        "symbols": [
            {
                "symbol": "BTCETH",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "ETH",
                "isSpotTradingAllowed": True,
                "permissionSets": [["SPOT"]],
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0",
                        "maxPrice": "0",
                        "tickSize": "0.0001",
                    },
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0",
                        "maxQty": "0",
                        "stepSize": "0.001",
                    },
                    {
                        "filterType": "MARKET_LOT_SIZE",
                        "minQty": "0",
                        "maxQty": "0",
                        "stepSize": "0.001",
                    },
                ],
            }
        ],
    }


def _write_capture(capture_root: Path, *, mid: float) -> None:
    instrument = VenueInstrument(
        venue="binance",
        venue_symbol="BTCETH",
        base=AssetId("BTC"),
        quote=AssetId("ETH"),
    )
    start = _QUALIFICATION_AS_OF - timedelta(days=14)
    bid = mid * (1.0 - 0.0001)
    ask = mid * (1.0 + 0.0001)

    def snapshot(observed_at: datetime, fingerprint: str) -> PublicBookSnapshot:
        return PublicBookSnapshot(
            instrument=instrument,
            observed_at=observed_at,
            source_id="playwright:book",
            source_fingerprint=fingerprint,
            bids=(BookLevel(price=bid, quantity=1_000_000.0),),
            asks=(BookLevel(price=ask, quantity=1_000_000.0),),
        )

    write_public_book_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.L1,
        ),
        tuple(
            snapshot(start + index * timedelta(minutes=1), "1" * 64)
            for index in range(14 * 24 * 60)
        ),
    )
    write_public_book_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.DEPTH,
        ),
        tuple(
            snapshot(start + index * timedelta(minutes=5), "2" * 64)
            for index in range(14 * 24 * 12)
        ),
    )
    metadata = public_market_metadata_snapshot_from_metadata(
        metadata=_market_metadata(instrument),
        observed_at=_QUALIFICATION_AS_OF,
        source_id="playwright:metadata",
    )
    write_public_market_metadata_snapshots(
        capture_file(
            capture_root,
            venue="binance",
            venue_symbol="BTCETH",
            kind=CaptureKind.METADATA,
        ),
        (metadata,),
    )


def _seed_scanner(
    run_root: Path, data_root: Path, capture_root: Path
) -> dict[str, str]:
    direct = _scanner_data(data_root)
    baseline = run_scan_with_qap(
        as_of=_SCANNER_AS_OF,
        horizons=(ScannerHorizon.SWING,),
        data_root=data_root,
        run_root=run_root,
        repository_root=_ROOT,
    )
    _definition, tables = read_completed_scan(baseline.artifact_directory)
    manual_candidate = next(
        row
        for row in tables["scout_trials.parquet"]
        if row["trial_status"] == "valid"
        and row["pair_id"] == "BTC/ETH"
        and row["resolution"] == "1d"
        and row["model_family"] == "log_ratio_mean_reversion"
        and row["template_id"] == "slow"
        and row["orientation"] == "BTC/ETH"
    )
    basket_candidate = next(
        row
        for row in tables["scout_trials.parquet"]
        if row["trial_status"] == "valid"
        and row["pair_id"] == "BTC/SOL"
        and row["resolution"] == "1d"
        and row["model_family"] == "log_ratio_mean_reversion"
        and row["template_id"] == "base"
    )
    manual = run_scan_with_qap(
        as_of=_SCANNER_AS_OF,
        horizons=(ScannerHorizon.SWING,),
        data_root=data_root,
        run_root=run_root,
        manual_replay_candidate_ids=(str(manual_candidate["candidate_id"]),),
        repository_root=_ROOT,
    )
    _manual_definition, manual_tables = read_completed_scan(manual.artifact_directory)
    promotion = next(
        row
        for row in manual_tables["promotions.parquet"]
        if row["candidate_id"] == manual_candidate["candidate_id"]
    )
    if promotion["economic_gate_status"] != "deep_replay_survivor":
        raise RuntimeError("playwright manual candidate did not survive deep replay")

    momentum_directory = generate_asset_momentum(
        scan_id=baseline.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SWING,
        data_root=data_root,
        run_root=run_root,
    )
    momentum, _snapshot = read_asset_momentum_generation(momentum_directory)
    current = next(
        bar for bar in direct.bars if bar.bar_end_exclusive == _QUALIFICATION_AS_OF
    )
    _write_capture(capture_root, mid=current.close)
    return {
        "baseline_scan_id": baseline.scan_id,
        "manual_scan_id": manual.scan_id,
        "manual_candidate_id": str(manual_candidate["candidate_id"]),
        "basket_candidate_id": str(basket_candidate["candidate_id"]),
        "momentum_scan_id": momentum.momentum_scan_id,
        "scan_as_of": _SCANNER_AS_OF.isoformat().replace("+00:00", "Z"),
        "freeze_at": _SCANNER_AS_OF.isoformat().replace("+00:00", "Z"),
        "advance_through": _ADVANCE_THROUGH.isoformat().replace("+00:00", "Z"),
        "qualification_as_of": _QUALIFICATION_AS_OF.isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--frontend-port", type=int, required=True)
    args = parser.parse_args()

    with TemporaryDirectory(prefix="qap-playwright-") as temporary:
        temporary_root = Path(temporary)
        run_root = temporary_root / "runs"
        data_root = temporary_root / "data"
        capture_root = temporary_root / "capture"
        fixture_market = data_root / "tests/fixtures/market"
        fixture_market.mkdir(parents=True)
        shutil.copy2(
            _ROOT / "tests/fixtures/market/BTCUSDT_1h.csv",
            fixture_market / "BTCUSDT_1h.csv",
        )
        run_experiment_to_artifacts(
            load_manifest(_MANIFEST),
            data_root=data_root,
            repository_root=_ROOT,
            run_root=run_root,
            run_timestamp=_RUN_TIMESTAMP,
        )
        fixture_state = _seed_scanner(run_root, data_root, capture_root)
        app = create_app(
            ApiSettings(
                run_root=run_root,
                market_data_root=data_root,
                repository_root=_ROOT,
                capture_root=capture_root,
                allowed_origins=(f"http://127.0.0.1:{args.frontend_port}",),
                host="127.0.0.1",
                port=args.api_port,
            )
        )

        app.add_api_route(
            "/__fixture/state",
            lambda: fixture_state,
            methods=["GET"],
            include_in_schema=False,
        )
        app.add_api_route(
            "/__fixture/binance/api/v3/exchangeInfo",
            _fixture_binance_exchange_info,
            methods=["GET"],
            include_in_schema=False,
        )

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=args.api_port,
            log_level="warning",
        )


if __name__ == "__main__":
    main()
