"""Narrow Scanner-V1 candidate adapter into ordinary authoritative QAP replay."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import cast

from qap.experiment.artifacts import read_run_artifacts, run_experiment_to_artifacts
from qap.experiment.data import ExperimentSetupError
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.model_policies import compose_model_strategy_policy
from qap.experiment.runner import prepare_experiment
from qap.portfolio import AssetId
from qap.portfolio._decimal import divide
from qap.scanner.artifacts import (
    ReplayAttemptStatus,
    ScanArtifactGeneration,
    read_replay_attempt,
    transition_replay_attempt,
)
from qap.scanner.catalog import (
    ResolvedCatalogSource,
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    catalog_semantic_identity,
    resolve_catalog_source,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerProtocol, protocol_identity
from qap.scanner.trials import ScannerModelFamily, ScannerTrial


class ScannerReplayStatus(StrEnum):
    SETUP_FAILED = "setup_failed"
    REPLAY_FAILED = "replay_failed"
    COMPLETED = "completed"


class ScannerEconomicGateStatus(StrEnum):
    DEEP_REPLAY_SURVIVOR = "deep_replay_survivor"
    DEEP_REPLAY_REJECTED = "deep_replay_rejected"


class ScannerReplaySetupError(ExperimentSetupError):
    """Candidate-specific setup failure with a stable scanner failure reason."""

    def __init__(self, reason: str, *, stage: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.stage = stage


@dataclass(frozen=True, slots=True)
class PreparedScannerReplay:
    manifest: ExperimentManifest
    direct_execution_instrument_id: str
    evidence_instrument_ids: tuple[str, str]


@dataclass(frozen=True, slots=True)
class ScannerReplayOutcome:
    candidate_id: str
    attempt_id: str
    status: ScannerReplayStatus
    direct_execution_instrument_id: str | None
    deep_replay_run_id: str | None
    economic_gate_status: ScannerEconomicGateStatus | None
    failure_stage: str | None = None
    failure_reason: str | None = None


def _require_enumerated_attempt(
    generation: ScanArtifactGeneration,
    *,
    attempt_id: str,
    trial: ScannerTrial,
) -> None:
    attempt = read_replay_attempt(generation, attempt_id)
    if (
        attempt.scan_id != generation.definition.scan_id
        or attempt.scan_id != trial.scan_id
    ):
        raise ScannerReplaySetupError(
            "attempt_scan_mismatch", stage="attempt_validation"
        )
    if attempt.candidate_id != trial.candidate_id:
        raise ScannerReplaySetupError(
            "attempt_candidate_mismatch",
            stage="attempt_validation",
        )
    if attempt.attempt_status is not ReplayAttemptStatus.ENUMERATED:
        raise ScannerReplaySetupError(
            "replay_attempt_not_enumerated",
            stage="attempt_validation",
        )


def _validate_candidate_contract(
    generation: ScanArtifactGeneration,
    trial: ScannerTrial,
    catalog: ScannerCatalog,
    protocol: ScannerProtocol,
) -> None:
    definition = generation.definition
    if trial.scan_id != definition.scan_id:
        raise ScannerReplaySetupError(
            "candidate_scan_mismatch", stage="candidate_validation"
        )
    if definition.scanner_protocol_version != protocol.protocol_id or (
        definition.protocol_identity != protocol_identity(protocol)
    ):
        raise ScannerReplaySetupError(
            "scanner_protocol_mismatch",
            stage="candidate_validation",
        )
    if definition.catalog_identity != catalog_semantic_identity(catalog):
        raise ScannerReplaySetupError(
            "catalog_identity_mismatch",
            stage="candidate_validation",
        )
    if trial.venue not in definition.venues or trial.horizon not in definition.horizons:
        raise ScannerReplaySetupError(
            "candidate_scope_mismatch",
            stage="candidate_validation",
        )
    frozen = {
        (
            item.dataset_id,
            item.source_artifact_fingerprint,
            item.selection_slice_fingerprint,
        )
        for item in definition.input_slices
    }
    for dataset_id, source_fingerprint, selection_fingerprint in zip(
        trial.evidence_dataset_ids,
        trial.source_artifact_fingerprints,
        trial.selection_slice_fingerprints,
        strict=True,
    ):
        if (dataset_id, source_fingerprint, selection_fingerprint) not in frozen:
            raise ScannerReplaySetupError(
                "candidate_evidence_identity_mismatch",
                stage="candidate_validation",
            )


def _direct_source_spec(
    catalog: ScannerCatalog,
    trial: ScannerTrial,
) -> ScannerSourceSpec:
    candidate_assets = {trial.asset_a.key, trial.asset_b.key}
    matches = tuple(
        source
        for source in catalog.sources
        if source.venue == trial.venue
        and source.interval == trial.resolution.label
        and {source.base_asset, source.quote_asset} == candidate_assets
    )
    if not matches:
        raise ScannerReplaySetupError(
            "unsupported_direct_market",
            stage="direct_market_resolution",
        )
    if len(matches) != 1:
        raise ScannerReplaySetupError(
            "ambiguous_direct_market",
            stage="direct_market_resolution",
        )
    return matches[0]


def _resolved_evidence_sources(
    catalog: ScannerCatalog,
    *,
    trial: ScannerTrial,
    data_root: str | Path,
    protocol: ScannerProtocol,
) -> tuple[ResolvedCatalogSource, ResolvedCatalogSource]:
    resolved: list[ResolvedCatalogSource] = []
    expected_assets = {trial.asset_a, trial.asset_b}
    for dataset_id, expected_fingerprint in zip(
        trial.evidence_dataset_ids,
        trial.source_artifact_fingerprints,
        strict=True,
    ):
        try:
            item = resolve_catalog_source(
                catalog,
                dataset_id=dataset_id,
                data_root=data_root,
            )
        except ScannerCatalogError as exc:
            raise ScannerReplaySetupError(
                "evidence_source_admission_failed",
                stage="evidence_data_admission",
            ) from exc
        if item.source_artifact_fingerprint != expected_fingerprint:
            raise ScannerReplaySetupError(
                "candidate_evidence_identity_mismatch",
                stage="evidence_data_admission",
            )
        if (
            item.spec.venue != trial.venue
            or item.spec.interval != trial.resolution.label
            or item.series.instrument.base not in expected_assets
            or item.series.instrument.quote != AssetId(protocol.quote_asset)
        ):
            raise ScannerReplaySetupError(
                "evidence_source_contract_mismatch",
                stage="evidence_data_admission",
            )
        resolved.append(item)
    if {item.series.instrument.base for item in resolved} != expected_assets:
        raise ScannerReplaySetupError(
            "evidence_source_contract_mismatch",
            stage="evidence_data_admission",
        )
    return cast(tuple[ResolvedCatalogSource, ResolvedCatalogSource], tuple(resolved))


def _require_window(
    source: ResolvedCatalogSource,
    *,
    start: datetime,
    end: datetime,
    stage: str,
) -> tuple[object, ...]:
    bars = tuple(
        bar for bar in source.series.bars if start <= bar.candle_open_time < end
    )
    if (
        not bars
        or bars[0].candle_open_time != start
        or bars[-1].bar_end_exclusive != end
    ):
        raise ScannerReplaySetupError("historical_window_unavailable", stage=stage)
    return cast(tuple[object, ...], bars)


def _starting_quantities(
    direct: ResolvedCatalogSource,
    *,
    evaluation_start: datetime,
    protocol: ScannerProtocol,
) -> dict[str, Decimal]:
    matches = tuple(
        bar for bar in direct.series.bars if bar.bar_end_exclusive == evaluation_start
    )
    if len(matches) != 1:
        raise ScannerReplaySetupError(
            "evaluation_start_price_unavailable",
            stage="normalization",
        )
    price = Decimal(str(matches[0].close))
    if not price.is_finite() or price <= 0:
        raise ScannerReplaySetupError(
            "evaluation_start_price_invalid",
            stage="normalization",
        )
    total = protocol.normalization.total_direct_quote_value
    half = total / Decimal("2")
    instrument = direct.series.instrument
    return {
        instrument.base.key: divide(half, price),
        instrument.quote.key: half,
    }


def prepare_scanner_replay_manifest(
    *,
    generation: ScanArtifactGeneration,
    attempt_id: str,
    trial: ScannerTrial,
    catalog: ScannerCatalog,
    data_root: str | Path,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> PreparedScannerReplay:
    """Build one direct-market development manifest from a durably enumerated trial."""

    if not isinstance(cast(object, generation), ScanArtifactGeneration):
        raise TypeError("generation must be a ScanArtifactGeneration")
    if not isinstance(cast(object, trial), ScannerTrial):
        raise TypeError("trial must be a ScannerTrial")
    if not isinstance(cast(object, catalog), ScannerCatalog):
        raise TypeError("catalog must be a ScannerCatalog")
    _require_enumerated_attempt(generation, attempt_id=attempt_id, trial=trial)
    _validate_candidate_contract(generation, trial, catalog, protocol)

    direct_spec = _direct_source_spec(catalog, trial)
    try:
        direct = resolve_catalog_source(
            catalog,
            dataset_id=direct_spec.dataset_id,
            data_root=data_root,
        )
    except ScannerCatalogError as exc:
        raise ScannerReplaySetupError(
            "direct_market_data_admission_failed",
            stage="direct_market_data_admission",
        ) from exc
    evidence = _resolved_evidence_sources(
        catalog,
        trial=trial,
        data_root=data_root,
        protocol=protocol,
    )

    evaluation_end = generation.definition.eligible_information_end
    horizon = protocol.horizon(trial.horizon)
    evaluation_start = evaluation_end - horizon.evaluation_window
    data_start = evaluation_start - trial.window_bars * trial.resolution.duration
    for source in (*evidence, direct):
        _require_window(
            source,
            start=data_start,
            end=evaluation_end,
            stage="historical_window_admission",
        )
    starting_quantities = _starting_quantities(
        direct,
        evaluation_start=evaluation_start,
        protocol=protocol,
    )

    direct_instrument_id = direct.spec.dataset_id
    evidence_instrument_ids = cast(
        tuple[str, str], tuple(item.spec.dataset_id for item in evidence)
    )
    instrument_specs = [
        {
            "instrument_id": direct_instrument_id,
            "venue": direct.spec.venue,
            "venue_symbol": direct.spec.venue_symbol,
            "base_asset": direct.spec.base_asset,
            "quote_asset": direct.spec.quote_asset,
        }
    ]
    instrument_specs.extend(
        {
            "instrument_id": item.spec.dataset_id,
            "venue": item.spec.venue,
            "venue_symbol": item.spec.venue_symbol,
            "base_asset": item.spec.base_asset,
            "quote_asset": item.spec.quote_asset,
        }
        for item in evidence
    )
    data_sources = [
        {
            "dataset_id": direct.spec.dataset_id,
            "instrument_id": direct_instrument_id,
            "relative_path": direct.spec.relative_path,
            "expected_semantic_fingerprint": direct.source_artifact_fingerprint,
        }
    ]
    data_sources.extend(
        {
            "dataset_id": item.spec.dataset_id,
            "instrument_id": item.spec.dataset_id,
            "relative_path": item.spec.relative_path,
            "expected_semantic_fingerprint": item.source_artifact_fingerprint,
        }
        for item in evidence
    )

    relationship_id = (
        "rolling_log_ratio_zscore"
        if trial.model_family is ScannerModelFamily.LOG_RATIO_MEAN_REVERSION
        else "residual_mean_reversion"
    )
    manifest = ExperimentManifest.model_validate(
        {
            "schema_version": "qap.experiment.manifest.v1",
            "experiment_name": (
                f"scanner-{trial.horizon.value}-{trial.candidate_id[:12]}"
            ),
            "description": (
                "Scanner-V1 searched-development replay "
                f"candidate={trial.candidate_id}; scan={trial.scan_id}; normalization="
                f"{protocol.normalization.policy_id}."
            ),
            "research_family_id": f"scanner-{trial.candidate_id}",
            "parent_run_id": None,
            "basket": [trial.asset_a.key, trial.asset_b.key],
            "starting_quantities": {
                key: str(value) for key, value in starting_quantities.items()
            },
            "universe_mode": "declared_fixed_basket",
            "analysis_anchor": direct.spec.quote_asset,
            "instruments": instrument_specs,
            "evidence_instrument_ids": list(evidence_instrument_ids),
            "interval": trial.resolution.label,
            "data_window": {
                "start": data_start.isoformat(),
                "end": evaluation_end.isoformat(),
            },
            "evaluation_window": {
                "start": evaluation_start.isoformat(),
                "end": evaluation_end.isoformat(),
            },
            "data_sources": data_sources,
            "relationship": {
                "component_id": relationship_id,
                "config": {
                    "base_asset": trial.orientation.base.key,
                    "quote_asset": trial.orientation.quote.key,
                    "window_bars": trial.window_bars,
                    "min_observations": trial.minimum_observations,
                    "evidence_instrument_ids": list(evidence_instrument_ids),
                },
            },
            "policy": {
                "component_id": "evidence_tilt",
                "config": {
                    "base_asset": trial.orientation.base.key,
                    "quote_asset": trial.orientation.quote.key,
                    "neutral_weights": {
                        trial.asset_a.key: "0.5",
                        trial.asset_b.key: "0.5",
                    },
                    "neutral_threshold": str(protocol.neutral_threshold),
                    "enter_threshold": str(protocol.entry_threshold),
                    "maximum_tilt": str(protocol.maximum_tilt),
                    "neutral_mode": "neutral_target",
                },
            },
            "execution": {
                "execution_instrument_id": direct_instrument_id,
                "numeraire_asset": direct.spec.quote_asset,
                "fee_bps": str(protocol.cost_policy.fee_bps),
                "slippage_bps": str(protocol.cost_policy.slippage_bps),
                "minimum_rebalance_notional": str(
                    protocol.normalization.minimum_rebalance_notional
                ),
                "base_step": (
                    None
                    if protocol.normalization.base_step is None
                    else str(protocol.normalization.base_step)
                ),
                "adverse_cost_scenario": {
                    "fee_bps": str(protocol.cost_policy.adverse_fee_bps),
                    "slippage_bps": str(protocol.cost_policy.adverse_slippage_bps),
                },
            },
            "external_flows": [],
            "benchmarks": {
                "relationship_alpha_claim": True,
                "primary_incremental_benchmark": protocol.primary_control.control_id,
                "controls": [
                    {
                        "kind": "band_partial",
                        "control_id": protocol.primary_control.control_id,
                        "band_width": str(protocol.primary_control.band_width),
                        "partial_correction_fraction": str(
                            protocol.primary_control.partial_correction_fraction
                        ),
                    }
                ],
            },
            "data_role": "development",
            "primary_metric": "primary_control_relative_terminal_wealth",
            "success_threshold": "0",
            "random_seed": None,
        }
    )
    return PreparedScannerReplay(
        manifest=manifest,
        direct_execution_instrument_id=direct_instrument_id,
        evidence_instrument_ids=evidence_instrument_ids,
    )


def _setup_failure_outcome(
    generation: ScanArtifactGeneration,
    *,
    attempt_id: str,
    trial: ScannerTrial,
    failure: ScannerReplaySetupError,
) -> ScannerReplayOutcome:
    transition_replay_attempt(
        generation,
        attempt_id,
        status=ReplayAttemptStatus.SETUP_FAILED,
        failure_stage=failure.stage,
        failure_reason=failure.reason,
    )
    return ScannerReplayOutcome(
        candidate_id=trial.candidate_id,
        attempt_id=attempt_id,
        status=ScannerReplayStatus.SETUP_FAILED,
        direct_execution_instrument_id=None,
        deep_replay_run_id=None,
        economic_gate_status=None,
        failure_stage=failure.stage,
        failure_reason=failure.reason,
    )


def run_scanner_candidate_replay(
    *,
    generation: ScanArtifactGeneration,
    attempt_id: str,
    trial: ScannerTrial,
    catalog: ScannerCatalog,
    data_root: str | Path,
    repository_root: str | Path,
    run_root: str | Path,
    run_timestamp: datetime | None = None,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> ScannerReplayOutcome:
    """Execute one eligible scanner candidate through ordinary QAP artifacts."""

    try:
        prepared = prepare_scanner_replay_manifest(
            generation=generation,
            attempt_id=attempt_id,
            trial=trial,
            catalog=catalog,
            data_root=data_root,
            protocol=protocol,
        )
    except ScannerReplaySetupError as exc:
        return _setup_failure_outcome(
            generation,
            attempt_id=attempt_id,
            trial=trial,
            failure=exc,
        )

    timestamp = datetime.now(UTC) if run_timestamp is None else run_timestamp
    try:
        preflight = prepare_experiment(
            prepared.manifest,
            data_root=data_root,
            repository_root=repository_root,
            run_timestamp=timestamp,
        )
        compose_model_strategy_policy(prepared.manifest, preflight.loaded)
    except ExperimentSetupError:
        return _setup_failure_outcome(
            generation,
            attempt_id=attempt_id,
            trial=trial,
            failure=ScannerReplaySetupError(
                "experiment_setup_failed",
                stage="experiment_preparation",
            ),
        )

    try:
        paths = run_experiment_to_artifacts(
            prepared.manifest,
            data_root=data_root,
            repository_root=repository_root,
            run_root=run_root,
            run_timestamp=timestamp,
        )
        loaded = read_run_artifacts(paths.run_directory)
    except Exception as exc:
        transition_replay_attempt(
            generation,
            attempt_id,
            status=ReplayAttemptStatus.REPLAY_FAILED,
            failure_stage="authoritative_replay",
            failure_reason=type(exc).__name__,
        )
        return ScannerReplayOutcome(
            candidate_id=trial.candidate_id,
            attempt_id=attempt_id,
            status=ScannerReplayStatus.REPLAY_FAILED,
            direct_execution_instrument_id=prepared.direct_execution_instrument_id,
            deep_replay_run_id=None,
            economic_gate_status=None,
            failure_stage="authoritative_replay",
            failure_reason=type(exc).__name__,
        )

    primary = loaded.result.strategy_vs_primary_control
    survivor = (
        loaded.result.strategy_vs_hodl > Decimal("0")
        and primary is not None
        and primary > Decimal("0")
    )
    gate = (
        ScannerEconomicGateStatus.DEEP_REPLAY_SURVIVOR
        if survivor
        else ScannerEconomicGateStatus.DEEP_REPLAY_REJECTED
    )
    transition_replay_attempt(
        generation,
        attempt_id,
        status=ReplayAttemptStatus.COMPLETED,
        deep_replay_run_id=paths.run_id,
    )
    return ScannerReplayOutcome(
        candidate_id=trial.candidate_id,
        attempt_id=attempt_id,
        status=ScannerReplayStatus.COMPLETED,
        direct_execution_instrument_id=prepared.direct_execution_instrument_id,
        deep_replay_run_id=paths.run_id,
        economic_gate_status=gate,
    )


__all__ = [
    "PreparedScannerReplay",
    "ScannerEconomicGateStatus",
    "ScannerReplayOutcome",
    "ScannerReplaySetupError",
    "ScannerReplayStatus",
    "prepare_scanner_replay_manifest",
    "run_scanner_candidate_replay",
]
