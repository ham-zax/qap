"""Outer composition root for scanner research and authoritative QAP replay."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qap.experiment.artifacts import read_run_artifacts
from qap.experiment.basket_scanner_adapter import run_basket_replay
from qap.experiment.dataset_seals import validate_expected_fingerprints_for_role
from qap.experiment.manifest import DataRole
from qap.experiment.prospective_scanner_adapter import (
    run_prospective_checkpoint,
    run_prospective_current_state,
    run_prospective_qualification,
)
from qap.experiment.scanner_adapter import run_scanner_candidate_replay
from qap.market.public_evidence import PublicEvidenceBundle
from qap.scanner.artifacts import (
    ReplayAttemptRecord,
    ReplayAttemptStatus,
    ScanArtifactGeneration,
    read_completed_scan,
)
from qap.scanner.asset_momentum import build_asset_momentum_generation
from qap.scanner.asset_momentum_artifacts import (
    publish_asset_momentum_generation,
    read_asset_momentum_generation,
)
from qap.scanner.basket import build_basket_definition_from_scan
from qap.scanner.basket_artifacts import (
    BasketReplayStatus,
    publish_basket_generation,
    read_basket_attempt,
    read_basket_generation,
    start_basket_generation,
)
from qap.scanner.basket_protocol import SCANNER_V1_BASKET
from qap.scanner.catalog import (
    ScannerCatalog,
    catalog_semantic_identity,
    load_scanner_catalog,
    resolve_catalog_source,
)
from qap.scanner.current_scope import CurrentApprovedScanScope
from qap.scanner.models import ScanDefinition, ScannerPinSpec
from qap.scanner.prospective import CandidateFreeze, ForwardCheckpoint
from qap.scanner.prospective_run import (
    HistoricalReplayTemplate,
    advance_forward_cohort,
    freeze_completed_scan,
)
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    ScannerProtocol,
    protocol_identity,
)
from qap.scanner.qualification_run import (
    ForwardQapState,
    qualify_forward_checkpoint,
)
from qap.scanner.run import ReplayReference, ScanRunResult, run_scan
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.trials import ScannerTrial
from qap.scanner.universe import (
    EligibleAssetRecord,
    HistoricalEligibilityState,
    UniverseSnapshot,
)


def _validate_scanner_catalog_admission(catalog: ScannerCatalog) -> None:
    validate_expected_fingerprints_for_role(
        (source.expected_semantic_fingerprint for source in catalog.sources),
        data_role=DataRole.DEVELOPMENT,
    )


def _direct_execution_instrument_id(
    catalog: ScannerCatalog,
    trial: ScannerTrial,
    *,
    allowed_dataset_ids: frozenset[str] | None = None,
) -> str:
    candidate_assets = {trial.asset_a.key, trial.asset_b.key}
    matches = tuple(
        source.dataset_id
        for source in catalog.sources
        if source.venue == trial.venue
        and source.interval == trial.resolution.label
        and {source.base_asset, source.quote_asset} == candidate_assets
        and (allowed_dataset_ids is None or source.dataset_id in allowed_dataset_ids)
    )
    if len(matches) != 1:
        raise RuntimeError("terminal replay cannot resolve its frozen direct market")
    return matches[0]


def _economic_gate(run_root: Path, run_id: str) -> str:
    loaded = read_run_artifacts(run_root / run_id)
    primary = loaded.result.strategy_vs_primary_control
    survivor = (
        loaded.result.strategy_vs_hodl > Decimal("0")
        and primary is not None
        and primary > Decimal("0")
    )
    return "deep_replay_survivor" if survivor else "deep_replay_rejected"


class _QapReplayService:
    def __init__(
        self,
        repository_root: Path,
        protocol: ScannerProtocol,
        current_approved_scope: CurrentApprovedScanScope | None,
    ) -> None:
        self._repository_root = repository_root
        self._protocol = protocol
        self._current_approved_scope = current_approved_scope

    def execute(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt_id: str,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference:
        outcome = run_scanner_candidate_replay(
            generation=generation,
            attempt_id=attempt_id,
            trial=trial,
            catalog=catalog,
            data_root=data_root,
            repository_root=self._repository_root,
            run_root=run_root,
            protocol=self._protocol,
            allowed_direct_dataset_ids=(
                None
                if self._current_approved_scope is None
                else self._current_approved_scope.datasets
            ),
        )
        return ReplayReference(
            status=outcome.status.value,
            direct_execution_instrument_id=(outcome.direct_execution_instrument_id),
            deep_replay_run_id=outcome.deep_replay_run_id,
            economic_gate_status=(
                None
                if outcome.economic_gate_status is None
                else outcome.economic_gate_status.value
            ),
            failure_stage=outcome.failure_stage,
            failure_reason=outcome.failure_reason,
        )

    def recover(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt: ReplayAttemptRecord,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference:
        del generation, data_root
        if attempt.attempt_status is ReplayAttemptStatus.ENUMERATED:
            raise RuntimeError("enumerated replay attempt must execute, not recover")
        if attempt.attempt_status is ReplayAttemptStatus.COMPLETED:
            if attempt.deep_replay_run_id is None:
                raise RuntimeError("completed replay attempt is missing its run ID")
            direct_id = _direct_execution_instrument_id(
                catalog,
                trial,
                allowed_dataset_ids=(
                    None
                    if self._current_approved_scope is None
                    else self._current_approved_scope.datasets
                ),
            )
            gate = _economic_gate(run_root, attempt.deep_replay_run_id)
        else:
            direct_id = (
                _direct_execution_instrument_id(
                    catalog,
                    trial,
                    allowed_dataset_ids=(
                        None
                        if self._current_approved_scope is None
                        else self._current_approved_scope.datasets
                    ),
                )
                if attempt.attempt_status is ReplayAttemptStatus.REPLAY_FAILED
                else None
            )
            gate = None
        return ReplayReference(
            status=attempt.attempt_status.value,
            direct_execution_instrument_id=direct_id,
            deep_replay_run_id=attempt.deep_replay_run_id,
            economic_gate_status=gate,
            failure_stage=attempt.failure_stage,
            failure_reason=attempt.failure_reason,
        )


def _historical_replay_template(
    deep_replay_run_id: str,
    run_root: Path,
) -> HistoricalReplayTemplate:
    loaded = read_run_artifacts(run_root / deep_replay_run_id)
    manifest = loaded.manifest
    evidence_ids = set(manifest.evidence_instrument_ids)
    evidence_sources = tuple(
        sorted(
            (
                source.dataset_id,
                source.expected_semantic_fingerprint,
            )
            for source in manifest.data_sources
            if source.instrument_id in evidence_ids
        )
    )
    if len(evidence_sources) != 2:
        raise RuntimeError("historical survivor must have exactly two evidence legs")
    config = manifest.relationship.config
    window_bars = config.get("window_bars")
    minimum_observations = config.get("min_observations")
    if not isinstance(window_bars, int) or not isinstance(minimum_observations, int):
        raise RuntimeError("historical survivor model parameters are incomplete")
    return HistoricalReplayTemplate(
        evidence_sources=evidence_sources,
        data_source_dataset_ids=tuple(
            source.dataset_id for source in manifest.data_sources
        ),
        model_parameters=(
            ("min_observations", str(minimum_observations)),
            ("window_bars", str(window_bars)),
        ),
        warmup=(
            manifest.effective_evaluation_window().start - manifest.data_window.start
        ),
        evidence_source_paths=tuple(
            sorted(
                (source.dataset_id, source.relative_path)
                for source in manifest.data_sources
                if source.instrument_id in evidence_ids
            )
        ),
    )


def _forward_qap_state(run_id: str, run_root: Path) -> ForwardQapState:
    loaded = read_run_artifacts(run_root / run_id)
    direct_id = loaded.manifest.execution.execution_instrument_id
    instrument = next(
        (
            item
            for item in loaded.manifest.instruments
            if item.instrument_id == direct_id
        ),
        None,
    )
    source = next(
        (
            item
            for item in loaded.manifest.data_sources
            if item.instrument_id == direct_id
        ),
        None,
    )
    if instrument is None or source is None:
        raise RuntimeError("forward QAP direct-market lineage is incomplete")
    strategy = loaded.result.role("strategy")
    try:
        base_quantity = strategy.terminal_quantities[instrument.base_asset]
        quote_quantity = strategy.terminal_quantities[instrument.quote_asset]
    except KeyError as exc:
        raise RuntimeError("forward QAP terminal holdings are incomplete") from exc
    return ForwardQapState(
        qap_run_id=run_id,
        direct_dataset_id=source.dataset_id,
        instrument=instrument.to_domain(),
        base_quantity=base_quantity,
        quote_quantity=quote_quantity,
    )


def freeze_scan_with_qap(
    *,
    run_root: str | Path,
    data_root: str | Path,
    prospective_root: str | Path,
    scan_id: str,
    horizon: ScannerHorizon,
    freeze_at: datetime,
) -> Path:
    """Freeze completed scanner survivors while reading QAP lineage externally."""

    return freeze_completed_scan(
        run_root=run_root,
        data_root=data_root,
        prospective_root=prospective_root,
        scan_id=scan_id,
        horizon=horizon,
        freeze_at=freeze_at,
        load_historical_template=_historical_replay_template,
    )


def advance_forward_with_qap(
    *,
    cohort_root: str | Path,
    catalog: ScannerCatalog,
    data_root: str | Path,
    run_root: str | Path,
    through: datetime,
    repository_root: str | Path | None = None,
    run_timestamp: datetime | None = None,
) -> tuple[Path, ...]:
    """Advance one scanner cohort through the ordinary QAP prospective adapter."""

    repository = (
        Path.cwd().resolve()
        if repository_root is None
        else Path(repository_root).resolve()
    )

    def run_checkpoint(
        freeze: CandidateFreeze,
        checkpoint: ForwardCheckpoint,
        current_catalog: ScannerCatalog,
        current_data_root: Path,
        current_run_root: Path,
        timestamp: datetime | None,
    ):
        return run_prospective_checkpoint(
            freeze,
            checkpoint,
            data_root=current_data_root,
            repository_root=repository,
            run_root=current_run_root,
            catalog=current_catalog,
            run_timestamp=timestamp,
        )

    return advance_forward_cohort(
        cohort_root=cohort_root,
        catalog=catalog,
        data_root=data_root,
        run_root=run_root,
        through=through,
        load_historical_template=_historical_replay_template,
        run_checkpoint=run_checkpoint,
        run_timestamp=run_timestamp,
    )


def qualify_forward_with_qap(
    *,
    cohort_root: str | Path,
    checkpoint_id: str,
    as_of: datetime,
    requested_capital: Decimal,
    catalog: ScannerCatalog,
    data_root: str | Path,
    capture_root: str | Path,
    run_root: str | Path,
    repository_root: str | Path | None = None,
    run_timestamp: datetime | None = None,
    capture_evidence: PublicEvidenceBundle | None = None,
) -> Path:
    """Qualify explicit capital while delegating economics to ordinary QAP."""

    repository = (
        Path.cwd().resolve()
        if repository_root is None
        else Path(repository_root).resolve()
    )

    def load_current_state(
        freeze: CandidateFreeze,
        current_as_of: datetime,
        current_catalog: ScannerCatalog,
        current_data_root: Path,
        current_run_root: Path,
        timestamp: datetime | None,
    ) -> ForwardQapState:
        run_id = run_prospective_current_state(
            freeze,
            as_of=current_as_of,
            data_root=current_data_root,
            repository_root=repository,
            run_root=current_run_root,
            catalog=current_catalog,
            run_timestamp=timestamp,
        )
        return _forward_qap_state(run_id, current_run_root)

    def run_qualification(
        freeze: CandidateFreeze,
        checkpoint: ForwardCheckpoint,
        current_as_of: datetime,
        capital: Decimal,
        slippage_bps: Decimal,
        current_catalog: ScannerCatalog,
        current_data_root: Path,
        current_run_root: Path,
        timestamp: datetime | None,
    ) -> tuple[str, bool, bool]:
        return run_prospective_qualification(
            freeze,
            checkpoint,
            as_of=current_as_of,
            requested_capital=capital,
            empirical_slippage_bps=slippage_bps,
            data_root=current_data_root,
            repository_root=repository,
            run_root=current_run_root,
            catalog=current_catalog,
            run_timestamp=timestamp,
        )

    return qualify_forward_checkpoint(
        cohort_root=cohort_root,
        checkpoint_id=checkpoint_id,
        as_of=as_of,
        requested_capital=requested_capital,
        catalog=catalog,
        data_root=data_root,
        capture_root=capture_root,
        run_root=run_root,
        load_current_state=load_current_state,
        run_qualification=run_qualification,
        run_timestamp=run_timestamp,
        capture_evidence=capture_evidence,
    )


def _completed_scan_scope(
    *,
    run_root: str | Path,
    scan_id: str,
    venue: str,
    horizon: ScannerHorizon,
) -> tuple[ScanDefinition, UniverseSnapshot]:
    scan_directory = Path(run_root).resolve() / "scans" / scan_id
    definition, tables = read_completed_scan(scan_directory)
    if (
        definition.scanner_protocol_version != SCANNER_V1_SLICE1.protocol_id
        or definition.protocol_identity != protocol_identity(SCANNER_V1_SLICE1)
    ):
        raise RuntimeError("source scan is not Scanner-V1 Slice-1 evidence")
    normalized_venue = venue.strip().lower()
    if normalized_venue not in definition.venues or horizon not in definition.horizons:
        raise ValueError("momentum scope is absent from source scan")
    eligible_rows = [
        row
        for row in tables["eligible_assets.parquet"]
        if row["venue"] == normalized_venue and row["horizon"] == horizon.value
    ]
    metadata_rows = [
        row
        for row in tables["graph_metadata.parquet"]
        if row["venue"] == normalized_venue and row["horizon"] == horizon.value
    ]
    if len(metadata_rows) != 1:
        raise RuntimeError("source scan momentum scope metadata is ambiguous")
    records = tuple(
        EligibleAssetRecord(
            scan_id=str(row["scan_id"]),
            venue=str(row["venue"]),
            horizon=ScannerHorizon(str(row["horizon"])),
            asset_id=str(row["asset_id"]),
            venue_symbol=str(row["venue_symbol"]),
            eligibility_state=HistoricalEligibilityState(str(row["eligibility_state"])),
            eligibility_reason=str(row["eligibility_reason"]),
            lifecycle_evidence_refs=tuple(row["lifecycle_evidence_refs"] or ()),
            source_artifact_fingerprint=str(row["source_artifact_fingerprint"]),
            selection_slice_fingerprint=str(row["selection_slice_fingerprint"]),
            bar_coverage=float(row["bar_coverage"]),
            longest_missing_run=int(row["longest_missing_run"]),
            automatic_eligible=bool(row["automatic_eligible"]),
            forensic_research_allowed=bool(row["forensic_research_allowed"]),
        )
        for row in eligible_rows
    )
    return definition, UniverseSnapshot(
        scan_id=definition.scan_id,
        venue=normalized_venue,
        horizon=horizon,
        records=records,
        universe_snapshot_id=str(metadata_rows[0]["universe_snapshot_id"]),
    )


def generate_asset_momentum(
    *,
    scan_id: str,
    venue: str,
    horizon: ScannerHorizon,
    data_root: str | Path,
    run_root: str | Path,
) -> Path:
    """Publish one frozen asset-native momentum generation from a completed scan."""

    definition, snapshot = _completed_scan_scope(
        run_root=run_root,
        scan_id=scan_id,
        venue=venue,
        horizon=horizon,
    )
    catalog = load_scanner_catalog(data_root)
    _validate_scanner_catalog_admission(catalog)
    if definition.catalog_identity != catalog_semantic_identity(catalog):
        raise RuntimeError("catalog does not match frozen source scan")
    rule = SCANNER_V1_BASKET.momentum_rule(horizon)
    evaluated_by_asset: dict[str, EvaluatedSeries] = {}
    for record in snapshot.records:
        matches = tuple(
            source
            for source in catalog.sources
            if source.venue == snapshot.venue
            and source.venue_symbol == record.venue_symbol
            and source.base_asset == record.asset_id
            and source.quote_asset == SCANNER_V1_BASKET.execution_bridge
            and source.interval == rule.resolution.label
        )
        if len(matches) != 1:
            raise RuntimeError(
                f"momentum source is not uniquely frozen for asset {record.asset_id}"
            )
        resolved = resolve_catalog_source(
            catalog,
            dataset_id=matches[0].dataset_id,
            data_root=data_root,
        )
        if resolved.source_artifact_fingerprint != record.source_artifact_fingerprint:
            raise RuntimeError("momentum source does not match source-scan provenance")
        evaluated_by_asset[record.asset_id] = evaluate_series(
            resolved.series,
            dataset_id=resolved.spec.dataset_id,
            eligible_information_end=definition.eligible_information_end,
            lookback=rule.formation,
        )
    generation = build_asset_momentum_generation(
        snapshot,
        evaluated_by_asset,
        as_of=definition.eligible_information_end,
    )
    return publish_asset_momentum_generation(run_root, generation, snapshot)


def run_basket_with_qap(
    *,
    scan_id: str,
    venue: str,
    horizon: ScannerHorizon,
    decision_resolution: str,
    economic_assets: Sequence[str],
    candidate_ids: Sequence[str],
    data_root: str | Path,
    run_root: str | Path,
    momentum_scan_id: str | None = None,
    repository_root: str | Path | None = None,
    run_timestamp: datetime | None = None,
) -> Path:
    """Run one manual basket intent through QAP and publish terminal evidence."""

    repository = (
        Path.cwd().resolve()
        if repository_root is None
        else Path(repository_root).resolve()
    )
    run_root_path = Path(run_root).resolve()
    source_scan_directory = run_root_path / "scans" / scan_id
    catalog = load_scanner_catalog(data_root)
    _validate_scanner_catalog_admission(catalog)
    source_momentum = None
    if momentum_scan_id is not None:
        source_momentum, _snapshot = read_asset_momentum_generation(
            run_root_path / "asset-momentum" / momentum_scan_id
        )
    created_at = datetime.now(UTC) if run_timestamp is None else run_timestamp
    definition = build_basket_definition_from_scan(
        source_scan_directory,
        catalog,
        venue=venue,
        horizon=horizon,
        decision_resolution=decision_resolution,
        economic_assets=economic_assets,
        candidate_ids=candidate_ids,
        created_at=created_at,
        source_momentum=source_momentum,
        data_root=data_root,
    )
    final_directory = run_root_path / "baskets" / definition.basket_id
    if final_directory.is_dir():
        read_basket_generation(final_directory)
        return final_directory

    generation = start_basket_generation(run_root_path, definition)
    attempt = read_basket_attempt(generation)
    if attempt.status is BasketReplayStatus.ENUMERATED:
        run_basket_replay(
            generation=generation,
            source_scan_directory=source_scan_directory,
            catalog=catalog,
            data_root=data_root,
            repository_root=repository,
            run_root=run_root_path,
            run_timestamp=run_timestamp,
        )
    return publish_basket_generation(generation)


def run_scan_with_qap(
    *,
    as_of: datetime,
    horizons: tuple[ScannerHorizon, ...],
    data_root: str | Path,
    run_root: str | Path,
    pins: Sequence[ScannerPinSpec] = (),
    manual_replay_candidate_ids: Sequence[str] = (),
    repository_root: str | Path | None = None,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
    current_approved_scope: CurrentApprovedScanScope | None = None,
) -> ScanRunResult:
    """Compose scanner discovery with the ordinary experiment replay adapter."""

    repository = (
        Path.cwd().resolve()
        if repository_root is None
        else Path(repository_root).resolve()
    )
    return run_scan(
        as_of=as_of,
        horizons=horizons,
        data_root=data_root,
        run_root=run_root,
        pins=pins,
        manual_replay_candidate_ids=manual_replay_candidate_ids,
        replay_service=_QapReplayService(
            repository,
            protocol,
            current_approved_scope,
        ),
        catalog_admission_guard=_validate_scanner_catalog_admission,
        protocol=protocol,
        current_approved_scope=current_approved_scope,
    )


__all__ = [
    "advance_forward_with_qap",
    "freeze_scan_with_qap",
    "generate_asset_momentum",
    "qualify_forward_with_qap",
    "run_basket_with_qap",
    "run_scan_with_qap",
]
