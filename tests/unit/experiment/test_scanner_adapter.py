# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq

from qap.experiment.artifacts import read_run_artifacts
from qap.experiment.manifest import DataRole, PrimaryMetric
from qap.experiment.scanner_adapter import (
    ScannerEconomicGateStatus,
    ScannerReplayStatus,
    prepare_scanner_replay_manifest,
    run_scanner_candidate_replay,
)
from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    fingerprint_bar_series,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.portfolio._decimal import divide
from qap.scanner.artifacts import (
    ReplayAttemptStatus,
    enumerate_replay_attempt,
    read_replay_attempt,
    start_scan_generation,
    write_scan_tables,
)
from qap.scanner.catalog import (
    ScannerCatalog,
    ScannerSourceSpec,
    catalog_semantic_identity,
)
from qap.scanner.graph import NeighborRecord
from qap.scanner.models import ScanDefinition, ScanInputIdentity
from qap.scanner.promotion import PromotionRecord, PromotionStatus
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    TemplateId,
    protocol_identity,
)
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus
from qap.scanner.trials import ScannerModelFamily, ScannerTrial
from qap.scanner.universe import EligibleAssetRecord, HistoricalEligibilityState

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, tzinfo=UTC)
BAR_COUNT = 32 * 24
END = START + BAR_COUNT * INTERVAL.duration
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _series(instrument: VenueInstrument, closes: tuple[float, ...]):
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + index * INTERVAL.duration,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000.0,
            )
            for index, close in enumerate(closes)
        )
    )


def _write_source(
    data_root: Path,
    *,
    dataset_id: str,
    instrument: VenueInstrument,
    closes: tuple[float, ...],
) -> ScannerSourceSpec:
    series = _series(instrument, closes)
    relative = f"market/{dataset_id}.parquet"
    path = data_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    write_parquet_bar_series(path, series)
    return ScannerSourceSpec(
        dataset_id=dataset_id,
        relative_path=relative,
        venue=instrument.venue,
        venue_symbol=instrument.venue_symbol,
        base_asset=instrument.base.key,
        quote_asset=instrument.quote.key,
        interval=INTERVAL.label,
        expected_semantic_fingerprint=fingerprint_bar_series(series),
    )


def _catalog(data_root: Path, *, include_direct: bool) -> ScannerCatalog:
    btc_prices = tuple(
        100.0 + index * 0.03 + math.sin(index / 11.0) * 2.0
        for index in range(BAR_COUNT)
    )
    eth_prices = tuple(
        50.0 + index * 0.012 + math.cos(index / 13.0) * 1.2
        for index in range(BAR_COUNT)
    )
    btc_usdt = VenueInstrument(
        venue="binance", venue_symbol="BTCUSDT", base=BTC, quote=USDT
    )
    eth_usdt = VenueInstrument(
        venue="binance", venue_symbol="ETHUSDT", base=ETH, quote=USDT
    )
    sources = [
        _write_source(
            data_root,
            dataset_id="btc-usdt-1h",
            instrument=btc_usdt,
            closes=btc_prices,
        ),
        _write_source(
            data_root,
            dataset_id="eth-usdt-1h",
            instrument=eth_usdt,
            closes=eth_prices,
        ),
    ]
    if include_direct:
        direct = VenueInstrument(
            venue="binance", venue_symbol="BTCETH", base=BTC, quote=ETH
        )
        sources.append(
            _write_source(
                data_root,
                dataset_id="btc-eth-1h",
                instrument=direct,
                closes=tuple(
                    btc / eth for btc, eth in zip(btc_prices, eth_prices, strict=True)
                ),
            )
        )
    lifecycle = data_root / "lifecycle.jsonl"
    lifecycle.write_text("\n", encoding="utf-8")
    return ScannerCatalog(
        schema_version="qap.scanner.catalog.v1",
        lifecycle_evidence_relative_path="lifecycle.jsonl",
        sources=tuple(sources),
    )


def _definition(catalog: ScannerCatalog) -> ScanDefinition:
    inputs: list[ScanInputIdentity] = []
    for dataset_id, selection in (
        ("btc-usdt-1h", "1" * 64),
        ("eth-usdt-1h", "2" * 64),
    ):
        source = catalog.source(dataset_id)
        inputs.append(
            ScanInputIdentity(
                dataset_id=dataset_id,
                source_artifact_fingerprint=source.expected_semantic_fingerprint,
                selection_slice_fingerprint=selection,
            )
        )
    return ScanDefinition(
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        catalog_identity=catalog_semantic_identity(catalog),
        as_of=END,
        eligible_information_end=END,
        venues=("binance",),
        horizons=(ScannerHorizon.SHORT,),
        input_slices=tuple(inputs),
        created_at=datetime(2026, 8, 18, tzinfo=UTC),
    )


def _trial(definition: ScanDefinition, catalog: ScannerCatalog) -> ScannerTrial:
    return ScannerTrial(
        candidate_id="c" * 64,
        scan_id=definition.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        universe_snapshot_id="b" * 64,
        pair_id="BTC/ETH",
        asset_a=BTC,
        asset_b=ETH,
        orientation=PairOrientation(base=BTC, quote=ETH),
        resolution=INTERVAL,
        model_family=ScannerModelFamily.LOG_RATIO_MEAN_REVERSION,
        template_id=TemplateId.FAST,
        window_bars=48,
        minimum_observations=46,
        source_artifact_fingerprints=(
            catalog.source("btc-usdt-1h").expected_semantic_fingerprint,
            catalog.source("eth-usdt-1h").expected_semantic_fingerprint,
        ),
        selection_slice_fingerprints=("1" * 64, "2" * 64),
        evidence_dataset_ids=("btc-usdt-1h", "eth-usdt-1h"),
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )


def _generation(tmp_path: Path, catalog: ScannerCatalog):
    definition = _definition(catalog)
    trial = _trial(definition, catalog)
    generation = start_scan_generation(tmp_path / "scanner-runs", definition)
    eligible = tuple(
        EligibleAssetRecord(
            scan_id=definition.scan_id,
            venue="binance",
            horizon=ScannerHorizon.SHORT,
            asset_id=asset.key,
            venue_symbol=f"{asset.key}USDT",
            eligibility_state=HistoricalEligibilityState.KNOWN_ELIGIBLE,
            eligibility_reason="covered_active_window",
            lifecycle_evidence_refs=(f"{asset.key.lower()}-event",),
            source_artifact_fingerprint=source,
            selection_slice_fingerprint=selection,
            bar_coverage=1.0,
            longest_missing_run=0,
            automatic_eligible=True,
            forensic_research_allowed=False,
        )
        for asset, source, selection in (
            (BTC, trial.source_artifact_fingerprints[0], "1" * 64),
            (ETH, trial.source_artifact_fingerprints[1], "2" * 64),
        )
    )
    neighbor = NeighborRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="BTC/ETH",
        asset_a="BTC",
        asset_b="ETH",
        ssd_distance=0.01,
        rank_from_a=1,
        rank_from_b=1,
        selected_by_a=True,
        selected_by_b=True,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )
    scout = ScoutTrialRecord(
        candidate_id=trial.candidate_id,
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="BTC/ETH",
        orientation="BTC/ETH",
        resolution="1h",
        model_family="log_ratio_mean_reversion",
        template_id="fast",
        trial_status=ScoutTrialStatus.VALID,
        failure_reason=None,
        scout_relative_wealth_proxy=0.01,
        scout_turnover_proxy=0.2,
        signal_count=3,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )
    promotion = PromotionRecord(
        candidate_id=trial.candidate_id,
        promotion_rank=1,
        promotion_status=PromotionStatus.AUTOMATIC_PROMOTED,
        budget_reason=None,
        automatic_selected=True,
        manual_selected=False,
        selected_for_replay=True,
    )
    write_scan_tables(
        generation,
        eligible_assets=eligible,
        neighbors=(neighbor,),
        scout_trials=(scout,),
        promotions=(promotion,),
    )
    attempt = enumerate_replay_attempt(generation, promotion)
    return generation, trial, attempt


def test_direct_market_candidate_builds_scale_free_development_manifest(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    catalog = _catalog(data_root, include_direct=True)
    generation, trial, attempt = _generation(tmp_path, catalog)

    prepared = prepare_scanner_replay_manifest(
        generation=generation,
        attempt_id=attempt.attempt_id,
        trial=trial,
        catalog=catalog,
        data_root=data_root,
    )
    manifest = prepared.manifest

    assert manifest.data_role is DataRole.DEVELOPMENT
    assert (
        manifest.primary_metric
        is PrimaryMetric.PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH
    )
    assert (
        manifest.execution.execution_instrument_id
        == prepared.direct_execution_instrument_id
    )
    assert manifest.evidence_instrument_ids == prepared.evidence_instrument_ids
    assert manifest.effective_evaluation_window().start == END - timedelta(days=30)
    assert manifest.effective_evaluation_window().end == END
    assert manifest.data_window.start == END - timedelta(days=32)
    assert manifest.data_window.end == END
    assert manifest.execution.fee_bps == Decimal("10")
    assert manifest.execution.slippage_bps == Decimal("5")
    assert manifest.execution.minimum_rebalance_notional == Decimal("0")
    assert manifest.execution.base_step is None
    assert manifest.benchmarks.primary_incremental_benchmark == "band-5pct-half"
    assert len(manifest.benchmarks.controls) == 1
    assert SCANNER_V1_SLICE1.normalization.policy_id in manifest.description

    direct_source = catalog.source("btc-eth-1h")
    direct_table = pq.read_table(data_root / direct_source.relative_path)
    assert direct_table.num_rows == BAR_COUNT
    direct_series = _series(
        VenueInstrument(venue="binance", venue_symbol="BTCETH", base=BTC, quote=ETH),
        tuple(float(value.as_py()) for value in direct_table.column("close")),
    )
    evaluation_start = manifest.effective_evaluation_window().start
    start_bar = next(
        bar for bar in direct_series.bars if bar.bar_end_exclusive == evaluation_start
    )
    assert manifest.starting_quantities["BTC"] == divide(
        Decimal("0.5"), Decimal(str(start_bar.close))
    )
    assert manifest.starting_quantities["ETH"] == Decimal("0.5")


def test_direct_market_candidate_runs_through_authoritative_qap_artifacts(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    catalog = _catalog(data_root, include_direct=True)
    generation, trial, attempt = _generation(tmp_path, catalog)
    experiment_root = tmp_path / "experiment-runs"

    outcome = run_scanner_candidate_replay(
        generation=generation,
        attempt_id=attempt.attempt_id,
        trial=trial,
        catalog=catalog,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=experiment_root,
        run_timestamp=datetime(2026, 8, 18, tzinfo=UTC),
    )

    assert outcome.status is ScannerReplayStatus.COMPLETED
    assert outcome.deep_replay_run_id is not None
    assert outcome.economic_gate_status in {
        ScannerEconomicGateStatus.DEEP_REPLAY_SURVIVOR,
        ScannerEconomicGateStatus.DEEP_REPLAY_REJECTED,
    }
    persisted = read_replay_attempt(generation, attempt.attempt_id)
    assert persisted.attempt_status is ReplayAttemptStatus.COMPLETED
    assert persisted.deep_replay_run_id == outcome.deep_replay_run_id
    loaded = read_run_artifacts(experiment_root / outcome.deep_replay_run_id)
    assert loaded.result.start_timestamp == END - timedelta(days=30)
    for role in loaded.result.roles:
        assert set(role.terminal_quantities) == {"BTC", "ETH"}
        assert "USDT" not in role.terminal_quantities


def test_catalog_semantic_drift_fails_before_direct_source_resolution(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    catalog = _catalog(data_root, include_direct=True)
    generation, trial, attempt = _generation(tmp_path, catalog)
    drifted = catalog.model_copy(
        update={
            "sources": tuple(
                source.model_copy(update={"expected_semantic_fingerprint": "f" * 64})
                if source.dataset_id == "btc-eth-1h"
                else source
                for source in catalog.sources
            )
        }
    )

    outcome = run_scanner_candidate_replay(
        generation=generation,
        attempt_id=attempt.attempt_id,
        trial=trial,
        catalog=drifted,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path / "experiment-runs",
        run_timestamp=datetime(2026, 8, 18, tzinfo=UTC),
    )

    assert outcome.status is ScannerReplayStatus.SETUP_FAILED
    assert outcome.failure_stage == "candidate_validation"
    assert outcome.failure_reason == "catalog_identity_mismatch"
    persisted = read_replay_attempt(generation, attempt.attempt_id)
    assert persisted.attempt_status is ReplayAttemptStatus.SETUP_FAILED
    assert persisted.failure_reason == "catalog_identity_mismatch"


def test_unsupported_cross_becomes_durable_setup_failure_without_experiment_run(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    catalog = _catalog(data_root, include_direct=False)
    generation, trial, attempt = _generation(tmp_path, catalog)
    experiment_root = tmp_path / "experiment-runs"

    outcome = run_scanner_candidate_replay(
        generation=generation,
        attempt_id=attempt.attempt_id,
        trial=trial,
        catalog=catalog,
        data_root=data_root,
        repository_root=REPOSITORY_ROOT,
        run_root=experiment_root,
        run_timestamp=datetime(2026, 8, 18, tzinfo=UTC),
    )

    assert outcome.status is ScannerReplayStatus.SETUP_FAILED
    assert outcome.failure_reason == "unsupported_direct_market"
    assert outcome.deep_replay_run_id is None
    persisted = read_replay_attempt(generation, attempt.attempt_id)
    assert persisted.attempt_status is ReplayAttemptStatus.SETUP_FAILED
    assert persisted.failure_reason == "unsupported_direct_market"
    assert not experiment_root.exists() or not any(experiment_root.iterdir())
