"""Narrow Scanner-V1 manual-basket adapter into ordinary authoritative QAP replay."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qap.experiment.artifacts import (
    ArtifactError,
    read_run_artifacts,
    run_experiment_to_artifacts,
)
from qap.experiment.basket_manifest import basket_edge_rule, pair_blind_window_returns
from qap.experiment.basket_policy import compose_basket_strategy_policy
from qap.experiment.data import ExperimentSetupError
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.result import ExperimentResult
from qap.experiment.runner import prepare_experiment
from qap.market import BarInterval
from qap.portfolio._decimal import divide
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.scanner.artifacts import read_completed_scan
from qap.scanner.basket import BasketDefinition
from qap.scanner.basket_artifacts import (
    BasketArtifactGeneration,
    BasketEconomicGateStatus,
    BasketReplayStatus,
    read_basket_attempt,
    transition_basket_attempt,
)
from qap.scanner.basket_protocol import basket_protocol_identity
from qap.scanner.basket_source import (
    BasketSourceError,
    basket_source_contract,
    resolve_product_execution_generations,
)
from qap.scanner.catalog import (
    ResolvedCatalogSource,
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    catalog_semantic_identity,
    resolve_catalog_source,
)
from qap.scanner.models import ScanDefinition
from qap.scanner.protocol import SCANNER_V1_SLICE1


class BasketReplaySetupError(ExperimentSetupError):
    """Basket-specific setup failure with a stable attributable stage."""

    def __init__(self, reason: str, *, stage: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.stage = stage


@dataclass(frozen=True, slots=True)
class PreparedBasketReplay:
    manifest: ExperimentManifest
    execution_instrument_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BasketReplayOutcome:
    basket_id: str
    status: BasketReplayStatus
    qap_run_id: str | None
    economic_gate_status: BasketEconomicGateStatus | None
    failure_stage: str | None = None
    failure_reason: str | None = None


def _require_source_scan_contract(
    definition: BasketDefinition,
    source_scan_directory: str | Path,
    catalog: ScannerCatalog,
) -> ScanDefinition:
    try:
        scan, _tables = read_completed_scan(source_scan_directory)
    except ValueError as exc:
        raise BasketReplaySetupError(
            "source_scan_integrity_invalid",
            stage="source_scan_admission",
        ) from exc
    if scan.scan_id != definition.source_scan_id:
        raise BasketReplaySetupError(
            "source_scan_identity_mismatch",
            stage="source_scan_admission",
        )
    try:
        source_contract = basket_source_contract(scan)
    except BasketSourceError as exc:
        raise BasketReplaySetupError(
            "source_scan_protocol_mismatch",
            stage="source_scan_admission",
        ) from exc
    if (
        definition.basket_protocol_id != source_contract.basket_protocol.protocol_id
        or definition.basket_protocol_identity
        != basket_protocol_identity(source_contract.basket_protocol)
    ):
        raise BasketReplaySetupError(
            "basket_source_policy_mismatch",
            stage="source_scan_admission",
        )
    if (
        not source_contract.product_current_approved
        and scan.catalog_identity != catalog_semantic_identity(catalog)
    ):
        raise BasketReplaySetupError(
            "catalog_identity_mismatch",
            stage="source_scan_admission",
        )
    if scan.eligible_information_end != definition.source_as_of:
        raise BasketReplaySetupError(
            "basket_source_cutoff_mismatch",
            stage="source_scan_admission",
        )
    return scan


def _resolved_execution_sources(
    definition: BasketDefinition,
    catalog: ScannerCatalog,
    *,
    source_scan: ScanDefinition,
    data_root: str | Path,
) -> tuple[ResolvedCatalogSource, ...]:
    execution = dict(definition.execution_dataset_ids)
    frozen = (
        None
        if definition.execution_generations is None
        else {item.asset_id: item for item in definition.execution_generations}
    )
    if frozen is not None:
        try:
            expected = resolve_product_execution_generations(
                source_scan,
                data_root=data_root,
                venue=definition.venue,
                resolution=definition.decision_resolution,
                economic_assets=definition.economic_assets,
                execution_bridge=definition.execution_bridge,
            )
        except BasketSourceError as exc:
            raise BasketReplaySetupError(
                "frozen_execution_lineage_invalid",
                stage="execution_data_admission",
            ) from exc
        if tuple(sorted(frozen.values(), key=lambda item: item.asset_id)) != expected:
            raise BasketReplaySetupError(
                "frozen_execution_lineage_mismatch",
                stage="execution_data_admission",
            )
    resolved: list[ResolvedCatalogSource] = []
    for asset in definition.economic_assets:
        dataset_id = execution[asset]
        if frozen is None:
            try:
                source = resolve_catalog_source(
                    catalog,
                    dataset_id=dataset_id,
                    data_root=data_root,
                )
            except ScannerCatalogError as exc:
                raise BasketReplaySetupError(
                    "execution_source_admission_failed",
                    stage="execution_data_admission",
                ) from exc
        else:
            binding = frozen[asset]
            try:
                provenance, series = resolve_immutable_generation(
                    data_root,
                    dataset_id=binding.dataset_id,
                    semantic_fingerprint=binding.source_artifact_fingerprint,
                )
            except ProductGenerationReadError as exc:
                raise BasketReplaySetupError(
                    "frozen_execution_generation_invalid",
                    stage="execution_data_admission",
                ) from exc
            if provenance.relative_path != binding.relative_path:
                raise BasketReplaySetupError(
                    "frozen_execution_generation_path_mismatch",
                    stage="execution_data_admission",
                )
            spec = ScannerSourceSpec(
                dataset_id=provenance.dataset_id,
                relative_path=provenance.relative_path,
                venue=provenance.venue,
                venue_symbol=provenance.venue_symbol,
                base_asset=provenance.base_asset,
                quote_asset=provenance.quote_asset,
                interval=provenance.interval,
                expected_semantic_fingerprint=provenance.semantic_fingerprint,
            )
            source = ResolvedCatalogSource(
                spec=spec,
                series=series,
                source_artifact_fingerprint=provenance.semantic_fingerprint,
            )
        if (
            source.spec.venue != definition.venue
            or source.spec.base_asset != asset
            or source.spec.quote_asset != definition.execution_bridge
            or source.spec.interval != definition.decision_resolution
        ):
            raise BasketReplaySetupError(
                "execution_source_contract_mismatch",
                stage="execution_data_admission",
            )
        resolved.append(source)
    return tuple(resolved)


def _warmup_bars(definition: BasketDefinition) -> int:
    policy_config: dict[str, object] = {"horizon": definition.horizon.value}
    edge_windows = tuple(
        basket_edge_rule(
            policy_config,
            definition.decision_resolution,
            edge.template_id.value,
        )[0]
        for edge in definition.selected_edges
    )
    return max(
        *edge_windows,
        pair_blind_window_returns(policy_config, definition.decision_resolution) + 1,
    )


def _require_window(
    source: ResolvedCatalogSource,
    *,
    start: datetime,
    end: datetime,
) -> None:
    bars = tuple(
        bar for bar in source.series.bars if start <= bar.candle_open_time < end
    )
    if (
        not bars
        or bars[0].candle_open_time != start
        or bars[-1].bar_end_exclusive != end
    ):
        raise BasketReplaySetupError(
            "historical_window_unavailable",
            stage="historical_window_admission",
        )


def _starting_quantities(
    definition: BasketDefinition,
    sources: tuple[ResolvedCatalogSource, ...],
    *,
    evaluation_start: datetime,
) -> dict[str, Decimal]:
    normalized_value = divide(Decimal("1"), Decimal(len(definition.economic_assets)))
    quantities: dict[str, Decimal] = {}
    for source in sources:
        matches = tuple(
            bar
            for bar in source.series.bars
            if bar.bar_end_exclusive == evaluation_start
        )
        if len(matches) != 1:
            raise BasketReplaySetupError(
                "evaluation_start_price_unavailable",
                stage="normalization",
            )
        price = Decimal(str(matches[0].close))
        if not price.is_finite() or price <= 0:
            raise BasketReplaySetupError(
                "evaluation_start_price_invalid",
                stage="normalization",
            )
        quantities[source.spec.base_asset] = divide(normalized_value, price)
    return quantities


def _edge_config(definition: BasketDefinition) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    for edge in definition.selected_edges:
        candidate_base, candidate_quote = edge.candidate_orientation.split(
            "/", maxsplit=1
        )
        edges.append(
            {
                "edge_id": edge.candidate_id,
                "asset_a": edge.asset_a,
                "asset_b": edge.asset_b,
                "candidate_base": candidate_base,
                "candidate_quote": candidate_quote,
                "model_family": edge.model_family.value,
                "template_id": edge.template_id.value,
            }
        )
    return edges


def prepare_basket_replay_manifest(
    *,
    generation: BasketArtifactGeneration,
    source_scan_directory: str | Path,
    catalog: ScannerCatalog,
    data_root: str | Path,
) -> PreparedBasketReplay:
    """Build one development-only ordinary-QAP manifest from an enumerated basket."""

    attempt = read_basket_attempt(generation)
    if attempt.status is not BasketReplayStatus.ENUMERATED:
        raise BasketReplaySetupError(
            "basket_replay_attempt_not_enumerated",
            stage="attempt_validation",
        )
    definition = generation.definition
    source_scan = _require_source_scan_contract(
        definition, source_scan_directory, catalog
    )
    sources = _resolved_execution_sources(
        definition,
        catalog,
        source_scan=source_scan,
        data_root=data_root,
    )

    interval = BarInterval(definition.decision_resolution)
    evaluation_end = definition.source_as_of
    evaluation_start = (
        evaluation_end - SCANNER_V1_SLICE1.horizon(definition.horizon).evaluation_window
    )
    data_start = evaluation_start - _warmup_bars(definition) * interval.duration
    for source in sources:
        _require_window(source, start=data_start, end=evaluation_end)
    starting_quantities = _starting_quantities(
        definition,
        sources,
        evaluation_start=evaluation_start,
    )

    instrument_specs = [
        {
            "instrument_id": source.spec.dataset_id,
            "venue": source.spec.venue,
            "venue_symbol": source.spec.venue_symbol,
            "base_asset": source.spec.base_asset,
            "quote_asset": source.spec.quote_asset,
        }
        for source in sources
    ]
    data_sources = [
        {
            "dataset_id": source.spec.dataset_id,
            "instrument_id": source.spec.dataset_id,
            "relative_path": source.spec.relative_path,
            "expected_semantic_fingerprint": source.source_artifact_fingerprint,
        }
        for source in sources
    ]
    primary_control = f"relative-momentum-{definition.horizon.value}"
    protocol = SCANNER_V1_SLICE1
    manifest = ExperimentManifest.model_validate(
        {
            "schema_version": "qap.experiment.manifest.v1",
            "experiment_name": (
                f"basket-{definition.horizon.value}-{definition.basket_id[:12]}"
            ),
            "description": (
                "Scanner-V1 manual basket development replay "
                f"basket={definition.basket_id}; scan={definition.source_scan_id}."
            ),
            "research_family_id": definition.research_family_id,
            "parent_run_id": None,
            "basket": list(definition.economic_assets),
            "starting_quantities": {
                key: str(value) for key, value in starting_quantities.items()
            },
            "universe_mode": "declared_fixed_basket",
            "analysis_anchor": definition.execution_bridge,
            "instruments": instrument_specs,
            "evidence_instrument_ids": [],
            "interval": definition.decision_resolution,
            "data_window": {
                "start": data_start.isoformat(),
                "end": evaluation_end.isoformat(),
            },
            "evaluation_window": {
                "start": evaluation_start.isoformat(),
                "end": evaluation_end.isoformat(),
            },
            "data_sources": data_sources,
            "relationship": {"component_id": "none", "config": {}},
            "policy": {
                "component_id": "basket_graph",
                "config": {
                    "horizon": definition.horizon.value,
                    "edges": _edge_config(definition),
                },
            },
            "execution": {
                "mode": "multi_asset_bridge",
                "execution_instrument_ids": [
                    source.spec.dataset_id for source in sources
                ],
                "bridge_asset": definition.execution_bridge,
                "market_metadata_mode": "historical_unconstrained",
                "numeraire_asset": definition.execution_bridge,
                "fee_bps": str(protocol.cost_policy.fee_bps),
                "slippage_bps": str(protocol.cost_policy.slippage_bps),
                "minimum_rebalance_notional": str(
                    protocol.normalization.minimum_rebalance_notional
                ),
                "adverse_cost_scenario": {
                    "fee_bps": str(protocol.cost_policy.adverse_fee_bps),
                    "slippage_bps": str(protocol.cost_policy.adverse_slippage_bps),
                },
            },
            "external_flows": [],
            "benchmarks": {
                "relationship_alpha_claim": True,
                "primary_incremental_benchmark": primary_control,
                "controls": [
                    {
                        "kind": "band_partial",
                        "control_id": protocol.primary_control.control_id,
                        "band_width": str(protocol.primary_control.band_width),
                        "partial_correction_fraction": str(
                            protocol.primary_control.partial_correction_fraction
                        ),
                    },
                    {
                        "kind": "pair_blind_relative_momentum",
                        "control_id": primary_control,
                    },
                ],
            },
            "data_role": "development",
            "primary_metric": "primary_control_relative_terminal_wealth",
            "success_threshold": "0",
            "random_seed": None,
        }
    )
    return PreparedBasketReplay(
        manifest=manifest,
        execution_instrument_ids=tuple(source.spec.dataset_id for source in sources),
    )


def _gate_status(
    result: ExperimentResult,
    *,
    horizon: str,
) -> BasketEconomicGateStatus:
    strategy_vs_hodl = result.strategy_vs_hodl
    strategy_vs_primary = result.strategy_vs_primary_control
    strategy = result.role("strategy").terminal_value
    band = result.role("control:band-5pct-half").terminal_value
    pair_blind = result.role(f"control:relative-momentum-{horizon}").terminal_value
    survivor = (
        strategy_vs_hodl > Decimal("0")
        and strategy_vs_primary is not None
        and strategy_vs_primary > Decimal("0")
        and strategy > band
        and strategy > pair_blind
    )
    return (
        BasketEconomicGateStatus.DEVELOPMENT_SURVIVOR
        if survivor
        else BasketEconomicGateStatus.DEVELOPMENT_REJECTED
    )


def _recover_product_terminal_attempt(
    *,
    generation: BasketArtifactGeneration,
    source_scan_directory: str | Path,
    catalog: ScannerCatalog,
    data_root: str | Path,
    run_root: str | Path,
) -> BasketReplayOutcome:
    attempt = read_basket_attempt(generation)
    if attempt.status is BasketReplayStatus.ENUMERATED:
        raise RuntimeError("enumerated Product basket attempt is not recoverable")
    if attempt.status is not BasketReplayStatus.COMPLETED:
        return BasketReplayOutcome(
            basket_id=generation.definition.basket_id,
            status=attempt.status,
            qap_run_id=None,
            economic_gate_status=None,
            failure_stage=attempt.failure_stage,
            failure_reason=attempt.failure_reason,
        )

    source_scan = _require_source_scan_contract(
        generation.definition,
        source_scan_directory,
        catalog,
    )
    _resolved_execution_sources(
        generation.definition,
        catalog,
        source_scan=source_scan,
        data_root=data_root,
    )
    if attempt.qap_run_id is None or attempt.economic_gate_status is None:
        raise BasketReplaySetupError(
            "completed_attempt_lineage_invalid",
            stage="recovery_validation",
        )
    try:
        loaded = read_run_artifacts(Path(run_root).resolve() / attempt.qap_run_id)
    except (ArtifactError, OSError, ValueError) as exc:
        raise BasketReplaySetupError(
            "completed_qap_artifact_invalid",
            stage="recovery_validation",
        ) from exc
    gate = _gate_status(loaded.result, horizon=generation.definition.horizon.value)
    if gate is not attempt.economic_gate_status:
        raise BasketReplaySetupError(
            "completed_attempt_gate_mismatch",
            stage="recovery_validation",
        )
    return BasketReplayOutcome(
        basket_id=generation.definition.basket_id,
        status=attempt.status,
        qap_run_id=attempt.qap_run_id,
        economic_gate_status=attempt.economic_gate_status,
    )


def _setup_failure(
    generation: BasketArtifactGeneration,
    failure: BasketReplaySetupError,
) -> BasketReplayOutcome:
    transition_basket_attempt(
        generation,
        status=BasketReplayStatus.SETUP_FAILED,
        failure_stage=failure.stage,
        failure_reason=failure.reason,
    )
    return BasketReplayOutcome(
        basket_id=generation.definition.basket_id,
        status=BasketReplayStatus.SETUP_FAILED,
        qap_run_id=None,
        economic_gate_status=None,
        failure_stage=failure.stage,
        failure_reason=failure.reason,
    )


def run_basket_replay(
    *,
    generation: BasketArtifactGeneration,
    source_scan_directory: str | Path,
    catalog: ScannerCatalog,
    data_root: str | Path,
    repository_root: str | Path,
    run_root: str | Path,
    run_timestamp: datetime | None = None,
) -> BasketReplayOutcome:
    """Execute one enumerated manual basket through ordinary QAP artifacts."""

    attempt = read_basket_attempt(generation)
    if (
        generation.definition.execution_generations is not None
        and attempt.status is not BasketReplayStatus.ENUMERATED
    ):
        return _recover_product_terminal_attempt(
            generation=generation,
            source_scan_directory=source_scan_directory,
            catalog=catalog,
            data_root=data_root,
            run_root=run_root,
        )

    try:
        prepared = prepare_basket_replay_manifest(
            generation=generation,
            source_scan_directory=source_scan_directory,
            catalog=catalog,
            data_root=data_root,
        )
    except BasketReplaySetupError as exc:
        return _setup_failure(generation, exc)

    timestamp = datetime.now(UTC) if run_timestamp is None else run_timestamp
    try:
        preflight = prepare_experiment(
            prepared.manifest,
            data_root=data_root,
            repository_root=repository_root,
            run_timestamp=timestamp,
        )
        compose_basket_strategy_policy(prepared.manifest, preflight.loaded)
    except ExperimentSetupError:
        return _setup_failure(
            generation,
            BasketReplaySetupError(
                "experiment_setup_failed",
                stage="experiment_preparation",
            ),
        )

    run_directory = Path(run_root).resolve() / preflight.provenance.run_id
    try:
        if run_directory.is_dir():
            loaded = read_run_artifacts(run_directory)
            qap_run_id = preflight.provenance.run_id
        else:
            paths = run_experiment_to_artifacts(
                prepared.manifest,
                data_root=data_root,
                repository_root=repository_root,
                run_root=run_root,
                run_timestamp=timestamp,
            )
            loaded = read_run_artifacts(paths.run_directory)
            qap_run_id = paths.run_id
    except Exception as exc:
        transition_basket_attempt(
            generation,
            status=BasketReplayStatus.REPLAY_FAILED,
            failure_stage="authoritative_replay",
            failure_reason=type(exc).__name__,
        )
        return BasketReplayOutcome(
            basket_id=generation.definition.basket_id,
            status=BasketReplayStatus.REPLAY_FAILED,
            qap_run_id=None,
            economic_gate_status=None,
            failure_stage="authoritative_replay",
            failure_reason=type(exc).__name__,
        )

    gate = _gate_status(loaded.result, horizon=generation.definition.horizon.value)
    transition_basket_attempt(
        generation,
        status=BasketReplayStatus.COMPLETED,
        qap_run_id=qap_run_id,
        economic_gate_status=gate,
    )
    return BasketReplayOutcome(
        basket_id=generation.definition.basket_id,
        status=BasketReplayStatus.COMPLETED,
        qap_run_id=qap_run_id,
        economic_gate_status=gate,
    )


__all__ = [
    "BasketReplayOutcome",
    "BasketReplaySetupError",
    "PreparedBasketReplay",
    "prepare_basket_replay_manifest",
    "run_basket_replay",
]
