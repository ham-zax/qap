"""Sequential deterministic Scanner-V1 Slice-1 orchestration core."""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from qap.market import (
    AssetIdentityContinuity,
    BarInterval,
    InstrumentLifecycleEvent,
    InstrumentLifecycleEvidence,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import RelationshipObservationStatus, build_log_ratio_series
from qap.relationship.models import (
    rolling_log_ratio_observation,
    rolling_residual_observation,
)
from qap.scanner.artifacts import (
    ReplayAttemptRecord,
    ReplayAttemptStatus,
    ScanArtifactGeneration,
    enumerate_replay_attempt,
    publish_scan_generation,
    read_replay_attempt,
    start_scan_generation,
    write_scan_tables,
)
from qap.scanner.catalog import (
    ResolvedCatalogSource,
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    catalog_semantic_identity,
    load_scanner_catalog,
    resolve_catalog_source,
)
from qap.scanner.forensic_graph import ScopedManualPin, build_scanner_graph
from qap.scanner.graph import NeighborRecord, SsdGraph
from qap.scanner.models import ScanDefinition, ScanInputIdentity, ScannerPinSpec
from qap.scanner.promotion import PromotionRecord, apply_promotion_policy
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    ScannerProtocol,
    TemplateId,
    protocol_identity,
)
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus, run_scout_trial
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.trials import (
    ScannerModelFamily,
    ScannerTrial,
    enumerate_fixed_trials,
)
from qap.scanner.universe import (
    EligibleAssetRecord,
    HistoricalEligibilityState,
    UniverseAssetInput,
    build_venue_horizon_universe,
    classify_historical_eligibility,
)


class ScannerRunError(RuntimeError):
    """Generation-level scanner failure that must abort publication."""


@dataclass(frozen=True, slots=True)
class ReplayReference:
    status: str
    direct_execution_instrument_id: str | None
    deep_replay_run_id: str | None
    economic_gate_status: str | None
    failure_stage: str | None = None
    failure_reason: str | None = None


class ScannerReplayService(Protocol):
    def execute(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt_id: str,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference: ...

    def recover(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt: ReplayAttemptRecord,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference: ...


@dataclass(frozen=True, slots=True)
class ScanRunResult:
    scan_id: str
    artifact_directory: Path
    eligible_count: int
    excluded_count: int
    retained_edge_count: int
    enumerated_trial_count: int
    valid_trial_count: int
    invalid_trial_count: int
    automatic_promotion_count: int
    budget_exclusion_count: int
    replay_survivor_count: int
    replay_failure_count: int

    def summary_payload(self) -> dict[str, object]:
        return {
            "scan_id": self.scan_id,
            "artifact_path": str(self.artifact_directory),
            "eligible_assets": self.eligible_count,
            "excluded_assets": self.excluded_count,
            "retained_edges": self.retained_edge_count,
            "enumerated_trials": self.enumerated_trial_count,
            "valid_trials": self.valid_trial_count,
            "invalid_trials": self.invalid_trial_count,
            "automatic_promotions": self.automatic_promotion_count,
            "budget_exclusions": self.budget_exclusion_count,
            "replay_survivors": self.replay_survivor_count,
            "replay_failures": self.replay_failure_count,
        }


class _ContinuityDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    from_asset_identity_version: str
    to_asset_identity_version: str
    source_id: str


class _LifecycleEventDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    canonical_asset_id: str
    asset_identity_version: str
    venue: str
    venue_symbol: str
    quote_asset: str
    event_type: LifecycleEventType
    effective_at: datetime
    observed_at: datetime
    source_type: LifecycleSourceType
    source_id: str
    confidence: LifecycleConfidence
    continuity: _ContinuityDocument | None = None

    def to_domain(self) -> InstrumentLifecycleEvent:
        if self.schema_version != "qap.market.lifecycle-event.v1":
            raise ValueError("unsupported lifecycle event schema_version")
        continuity = (
            None
            if self.continuity is None
            else AssetIdentityContinuity(
                from_asset_identity_version=(
                    self.continuity.from_asset_identity_version
                ),
                to_asset_identity_version=self.continuity.to_asset_identity_version,
                source_id=self.continuity.source_id,
            )
        )
        return InstrumentLifecycleEvent(
            canonical_asset_id=AssetId(self.canonical_asset_id),
            asset_identity_version=self.asset_identity_version,
            venue=self.venue,
            venue_symbol=self.venue_symbol,
            quote_asset=AssetId(self.quote_asset),
            event_type=self.event_type,
            effective_at=self.effective_at,
            observed_at=self.observed_at,
            source_type=self.source_type,
            source_id=self.source_id,
            confidence=self.confidence,
            continuity=continuity,
        )


@dataclass(frozen=True, slots=True)
class _PreparedInputs:
    catalog: ScannerCatalog
    definition: ScanDefinition
    graph_sources: Mapping[tuple[str, ScannerHorizon], tuple[ScannerSourceSpec, ...]]
    graph_series: Mapping[tuple[str, ScannerHorizon], Mapping[str, EvaluatedSeries]]
    model_series: Mapping[
        tuple[str, ScannerHorizon], Mapping[tuple[str, str], EvaluatedSeries]
    ]
    model_failure_reasons: Mapping[
        tuple[str, ScannerHorizon], Mapping[tuple[str, str], str]
    ]
    lifecycle_events: Mapping[str, InstrumentLifecycleEvent]


def _safe_input_path(root: Path, relative: str) -> Path:
    base = root.resolve()
    try:
        path = (base / relative).resolve(strict=True)
        path.relative_to(base)
    except (OSError, ValueError) as exc:
        raise ScannerRunError(
            "scanner input path escapes data root or is missing"
        ) from exc
    if not path.is_file():
        raise ScannerRunError("scanner input path must be a regular file")
    return path


def _load_lifecycle_events(
    data_root: Path,
    catalog: ScannerCatalog,
) -> dict[str, InstrumentLifecycleEvent]:
    path = _safe_input_path(data_root, catalog.lifecycle_evidence_relative_path)
    events: dict[str, InstrumentLifecycleEvent] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            event = _LifecycleEventDocument.model_validate_json(line).to_domain()
        except (ValidationError, TypeError, ValueError) as exc:
            raise ScannerRunError(
                f"invalid lifecycle event at line {line_number}: {exc}"
            ) from exc
        if event.event_id in events:
            raise ScannerRunError("duplicate lifecycle event identity")
        events[event.event_id] = event
    return events


def _evidence_for_source(
    source: ScannerSourceSpec,
    events: Mapping[str, InstrumentLifecycleEvent],
) -> InstrumentLifecycleEvidence:
    asset = AssetId(source.base_asset)
    quote = AssetId(source.quote_asset)
    if not source.lifecycle_evidence_ids:
        return InstrumentLifecycleEvidence.empty(
            canonical_asset_id=asset,
            venue=source.venue,
            quote_asset=quote,
        )
    try:
        selected = tuple(events[event_id] for event_id in source.lifecycle_evidence_ids)
    except KeyError as exc:
        raise ScannerRunError(
            f"catalog references unknown lifecycle event {exc.args[0]}"
        ) from exc
    try:
        evidence = InstrumentLifecycleEvidence.from_events(selected)
    except (TypeError, ValueError) as exc:
        raise ScannerRunError("lifecycle evidence bundle is inconsistent") from exc
    if (
        evidence.canonical_asset_id != asset
        or evidence.venue != source.venue
        or evidence.quote_asset != quote
    ):
        raise ScannerRunError(
            "lifecycle evidence does not match catalog source identity"
        )
    return evidence


def _sources_by_base(
    catalog: ScannerCatalog,
    *,
    venue: str,
    interval: BarInterval,
    quote_asset: str,
) -> dict[str, ScannerSourceSpec]:
    result: dict[str, ScannerSourceSpec] = {}
    for source in catalog.sources:
        if (
            source.venue != venue
            or source.interval != interval.label
            or source.quote_asset != quote_asset
            or source.base_asset == quote_asset
        ):
            continue
        if source.base_asset in result:
            raise ScannerRunError(
                "ambiguous scanner source for venue/base/quote/interval"
            )
        result[source.base_asset] = source
    return result


def _prepare_inputs(
    *,
    as_of: datetime,
    horizons: tuple[ScannerHorizon, ...],
    data_root: Path,
    pins: tuple[ScannerPinSpec, ...],
    protocol: ScannerProtocol,
) -> _PreparedInputs:
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC")
    as_of = as_of.astimezone(UTC)
    if not horizons or len(set(horizons)) != len(horizons):
        raise ValueError("horizons must be non-empty and unique")
    if not set(horizons) <= set(ScannerHorizon):
        raise ValueError("unsupported scanner horizon")
    requested = set(horizons)
    for pin in pins:
        if not set(pin.horizons) <= requested:
            raise ValueError("pin horizon must be included in requested scan horizons")

    catalog = load_scanner_catalog(data_root)
    lifecycle_events = _load_lifecycle_events(data_root, catalog)
    resolved_cache: dict[str, ResolvedCatalogSource] = {}
    evaluated_cache: dict[tuple[str, int], EvaluatedSeries] = {}

    def resolved(source: ScannerSourceSpec) -> ResolvedCatalogSource:
        item = resolved_cache.get(source.dataset_id)
        if item is None:
            try:
                item = resolve_catalog_source(
                    catalog,
                    dataset_id=source.dataset_id,
                    data_root=data_root,
                )
            except ScannerCatalogError as exc:
                raise ScannerRunError(
                    f"scanner source admission failed: {source.dataset_id}"
                ) from exc
            resolved_cache[source.dataset_id] = item
        return item

    def evaluated(source: ScannerSourceSpec, lookback: timedelta) -> EvaluatedSeries:
        key = (source.dataset_id, int(lookback.total_seconds()))
        item = evaluated_cache.get(key)
        if item is None:
            admitted = resolved(source)
            item = evaluate_series(
                admitted.series,
                dataset_id=source.dataset_id,
                eligible_information_end=as_of,
                lookback=lookback,
            )
            evaluated_cache[key] = item
        return item

    graph_sources: dict[tuple[str, ScannerHorizon], tuple[ScannerSourceSpec, ...]] = {}
    graph_series: dict[tuple[str, ScannerHorizon], dict[str, EvaluatedSeries]] = {}
    model_series: dict[
        tuple[str, ScannerHorizon], dict[tuple[str, str], EvaluatedSeries]
    ] = {}
    model_failure_reasons: dict[
        tuple[str, ScannerHorizon], dict[tuple[str, str], str]
    ] = {}
    input_identities: dict[tuple[str, str, str], ScanInputIdentity] = {}

    for horizon in horizons:
        horizon_protocol = protocol.horizon(horizon)
        model_lookback = horizon_protocol.evaluation_window + max(
            duration for _template, duration in horizon_protocol.template_windows
        )
        for venue in protocol.venues:
            scope = (venue, horizon)
            graph_map = _sources_by_base(
                catalog,
                venue=venue,
                interval=horizon_protocol.graph_interval,
                quote_asset=protocol.quote_asset,
            )
            sources = tuple(
                sorted(graph_map.values(), key=lambda item: item.base_asset)
            )
            graph_sources[scope] = sources
            graph_values: dict[str, EvaluatedSeries] = {}
            model_values: dict[tuple[str, str], EvaluatedSeries] = {}
            model_failures: dict[tuple[str, str], str] = {}
            for source in sources:
                graph_value = evaluated(source, horizon_protocol.graph_window)
                graph_values[source.base_asset] = graph_value
                identity = ScanInputIdentity(
                    dataset_id=graph_value.dataset_id,
                    source_artifact_fingerprint=graph_value.source_artifact_fingerprint,
                    selection_slice_fingerprint=graph_value.selection_slice_fingerprint,
                )
                input_identities[
                    (
                        identity.dataset_id,
                        identity.source_artifact_fingerprint,
                        identity.selection_slice_fingerprint,
                    )
                ] = identity

                for resolution in horizon_protocol.model_resolutions:
                    model_map = _sources_by_base(
                        catalog,
                        venue=venue,
                        interval=resolution,
                        quote_asset=protocol.quote_asset,
                    )
                    model_key = (source.base_asset, resolution.label)
                    model_source = model_map.get(source.base_asset)
                    if model_source is None:
                        model_failures[model_key] = "model_source_unavailable"
                        continue
                    lifecycle = _evidence_for_source(
                        model_source,
                        lifecycle_events,
                    )
                    lifecycle_decision = classify_historical_eligibility(
                        lifecycle,
                        required_start=as_of - model_lookback,
                        required_end=as_of,
                    )
                    if (
                        lifecycle_decision.state
                        is not HistoricalEligibilityState.KNOWN_ELIGIBLE
                    ):
                        model_failures[model_key] = "model_lifecycle_ineligible"
                        continue
                    try:
                        model_value = evaluated(model_source, model_lookback)
                    except TypeError, ValueError:
                        model_failures[model_key] = "model_slice_unavailable"
                        continue
                    model_values[model_key] = model_value
                    model_identity = ScanInputIdentity(
                        dataset_id=model_value.dataset_id,
                        source_artifact_fingerprint=(
                            model_value.source_artifact_fingerprint
                        ),
                        selection_slice_fingerprint=(
                            model_value.selection_slice_fingerprint
                        ),
                    )
                    input_identities[
                        (
                            model_identity.dataset_id,
                            model_identity.source_artifact_fingerprint,
                            model_identity.selection_slice_fingerprint,
                        )
                    ] = model_identity
            graph_series[scope] = graph_values
            model_series[scope] = model_values
            model_failure_reasons[scope] = model_failures

    manual_inputs = tuple(
        sorted(token for pin in pins for token in pin.semantic_tokens())
    )
    definition = ScanDefinition(
        scanner_protocol_version=protocol.protocol_id,
        protocol_identity=protocol_identity(protocol),
        catalog_identity=catalog_semantic_identity(catalog),
        as_of=as_of,
        eligible_information_end=as_of,
        venues=protocol.venues,
        horizons=horizons,
        input_slices=tuple(input_identities.values()),
        manual_inputs=manual_inputs,
        created_at=datetime.now(UTC),
    )
    return _PreparedInputs(
        catalog=catalog,
        definition=definition,
        graph_sources=graph_sources,
        graph_series=graph_series,
        model_series=model_series,
        model_failure_reasons=model_failure_reasons,
        lifecycle_events=lifecycle_events,
    )


def _scope_pins(
    pins: tuple[ScannerPinSpec, ...],
    *,
    venue: str,
    horizon: ScannerHorizon,
) -> tuple[ScopedManualPin, ...]:
    return tuple(
        ScopedManualPin(
            asset_a=AssetId(pin.asset_a),
            asset_b=AssetId(pin.asset_b),
            forensic=pin.forensic,
        )
        for pin in pins
        if pin.venue == venue and horizon in pin.horizons
    )


def _invalid_trial_id(
    *,
    graph: SsdGraph,
    record: NeighborRecord,
    resolution: BarInterval,
    family: ScannerModelFamily,
    template: TemplateId,
    orientation: PairOrientation,
    reason: str,
    protocol: ScannerProtocol,
) -> str:
    payload = {
        "identity_version": "qap.scanner.invalid-trial.v1",
        "scan_id": graph.scan_id,
        "protocol_identity": protocol_identity(protocol),
        "universe_snapshot_id": graph.universe_snapshot_id,
        "venue": graph.venue,
        "horizon": graph.horizon,
        "pair_id": record.pair_id,
        "resolution": resolution.label,
        "model_family": family.value,
        "template_id": template.value,
        "orientation": [orientation.base.key, orientation.quote.key],
        "failure_reason": reason,
        "automatic_neighbor_selected": record.automatic_neighbor_selected,
        "manual_pinned": record.manual_pinned,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _invalid_resolution_records(
    *,
    graph: SsdGraph,
    record: NeighborRecord,
    resolution: BarInterval,
    reason: str,
    protocol: ScannerProtocol,
) -> tuple[ScoutTrialRecord, ...]:
    asset_a = AssetId(record.asset_a)
    asset_b = AssetId(record.asset_b)
    canonical = PairOrientation(base=asset_a, quote=asset_b)
    rows: list[ScoutTrialRecord] = []
    for template, _duration in protocol.horizon(
        ScannerHorizon(graph.horizon)
    ).template_windows:
        for family, orientations in (
            (ScannerModelFamily.LOG_RATIO_MEAN_REVERSION, (canonical,)),
            (
                ScannerModelFamily.RESIDUAL_MEAN_REVERSION,
                (canonical, canonical.inverted()),
            ),
        ):
            for orientation in orientations:
                rows.append(
                    ScoutTrialRecord(
                        candidate_id=_invalid_trial_id(
                            graph=graph,
                            record=record,
                            resolution=resolution,
                            family=family,
                            template=template,
                            orientation=orientation,
                            reason=reason,
                            protocol=protocol,
                        ),
                        scan_id=graph.scan_id,
                        venue=graph.venue,
                        horizon=graph.horizon,
                        pair_id=record.pair_id,
                        orientation=(f"{orientation.base.key}/{orientation.quote.key}"),
                        resolution=resolution.label,
                        model_family=family.value,
                        template_id=template.value,
                        trial_status=ScoutTrialStatus.INVALID,
                        failure_reason=reason,
                        scout_relative_wealth_proxy=None,
                        scout_turnover_proxy=0.0,
                        signal_count=0,
                        automatic_neighbor_selected=(
                            record.automatic_neighbor_selected
                        ),
                        manual_pinned=record.manual_pinned,
                    )
                )
    return tuple(rows)


def _invalid_scout_for_trial(
    trial: ScannerTrial,
    *,
    reason: str,
) -> ScoutTrialRecord:
    return ScoutTrialRecord(
        candidate_id=trial.candidate_id,
        scan_id=trial.scan_id,
        venue=trial.venue,
        horizon=trial.horizon.value,
        pair_id=trial.pair_id,
        orientation=f"{trial.orientation.base.key}/{trial.orientation.quote.key}",
        resolution=trial.resolution.label,
        model_family=trial.model_family.value,
        template_id=trial.template_id.value,
        trial_status=ScoutTrialStatus.INVALID,
        failure_reason=reason,
        scout_relative_wealth_proxy=None,
        scout_turnover_proxy=0.0,
        signal_count=0,
        automatic_neighbor_selected=trial.automatic_neighbor_selected,
        manual_pinned=trial.manual_pinned,
    )


def _trial_scout_record(
    trial: ScannerTrial,
    *,
    model_series: Mapping[tuple[str, str], EvaluatedSeries],
    as_of: datetime,
    protocol: ScannerProtocol,
) -> ScoutTrialRecord:
    left = model_series[(trial.asset_a.key, trial.resolution.label)]
    right = model_series[(trial.asset_b.key, trial.resolution.label)]
    aligned = align_bar_series(
        (
            validate_bar_series(left.bars),
            validate_bar_series(right.bars),
        )
    )
    fingerprints = {
        left.instrument.base: left.source_artifact_fingerprint,
        right.instrument.base: right.source_artifact_fingerprint,
    }
    evaluation_start = as_of - protocol.horizon(trial.horizon).evaluation_window
    timestamps = tuple(
        timestamp + trial.resolution.duration
        for timestamp in aligned.timestamps
        if evaluation_start <= timestamp + trial.resolution.duration <= as_of
    )
    if len(timestamps) < 2:
        return _invalid_scout_for_trial(
            trial,
            reason="insufficient_evaluation_window",
        )

    aligned_by_asset = {item.instrument.base: item for item in aligned.series}
    prices_by_asset = {
        asset: tuple(
            item.bars[index].close
            for index, timestamp in enumerate(aligned.timestamps)
            if evaluation_start <= timestamp + trial.resolution.duration <= as_of
        )
        for asset, item in aligned_by_asset.items()
    }

    scores: list[float | None] = []
    if trial.model_family is ScannerModelFamily.LOG_RATIO_MEAN_REVERSION:
        source = build_log_ratio_series(
            aligned,
            orientation=trial.orientation,
            source_fingerprints=fingerprints,
            as_of=as_of,
        )
        for timestamp in timestamps:
            observation = rolling_log_ratio_observation(
                source,
                window_bars=trial.window_bars,
                min_observations=trial.minimum_observations,
                as_of=timestamp,
            )
            scores.append(
                observation.values.get("score")
                if observation.status is RelationshipObservationStatus.VALID
                else None
            )
    else:
        for timestamp in timestamps:
            observation = rolling_residual_observation(
                aligned,
                orientation=trial.orientation,
                source_fingerprints=fingerprints,
                window_bars=trial.window_bars,
                min_observations=trial.minimum_observations,
                as_of=timestamp,
            )
            scores.append(
                observation.values.get("score")
                if observation.status is RelationshipObservationStatus.VALID
                else None
            )
    return run_scout_trial(
        trial,
        timestamps=timestamps,
        z_scores=tuple(scores),
        prices_by_asset=prices_by_asset,
        evaluation_start=evaluation_start,
        evaluation_end=as_of,
        cost_policy=protocol.cost_policy,
    )


def _search_scope(
    *,
    prepared: _PreparedInputs,
    generation: ScanArtifactGeneration,
    venue: str,
    horizon: ScannerHorizon,
    pins: tuple[ScannerPinSpec, ...],
    protocol: ScannerProtocol,
) -> tuple[
    tuple[EligibleAssetRecord, ...],
    tuple[NeighborRecord, ...],
    tuple[ScoutTrialRecord, ...],
    dict[str, ScannerTrial],
]:
    scope = (venue, horizon)
    source_specs = prepared.graph_sources[scope]
    scope_pins = _scope_pins(pins, venue=venue, horizon=horizon)
    if not source_specs:
        if scope_pins:
            raise ScannerRunError(
                "manual pin references a venue with no admitted sources"
            )
        return (), (), (), {}
    forensic = any(
        pin.forensic and pin.venue == venue and horizon in pin.horizons for pin in pins
    )
    universe_inputs = tuple(
        UniverseAssetInput(
            source=source,
            evaluated=prepared.graph_series[scope][source.base_asset],
            lifecycle=_evidence_for_source(source, prepared.lifecycle_events),
        )
        for source in source_specs
    )
    snapshot = build_venue_horizon_universe(
        scan_id=generation.definition.scan_id,
        venue=venue,
        horizon=horizon,
        inputs=universe_inputs,
        forensic=forensic,
        protocol=protocol,
    )
    graph = build_scanner_graph(
        snapshot,
        evaluated_by_asset=prepared.graph_series[scope],
        manual_pins=scope_pins,
        protocol=protocol,
    )

    scouts: list[ScoutTrialRecord] = []
    trials_by_id: dict[str, ScannerTrial] = {}
    model_values = prepared.model_series[scope]
    model_failures = prepared.model_failure_reasons[scope]
    horizon_protocol = protocol.horizon(horizon)
    for record in graph.records:
        pair_graph = replace(graph, records=(record,))
        for resolution in horizon_protocol.model_resolutions:
            required_keys = (
                (record.asset_a, resolution.label),
                (record.asset_b, resolution.label),
            )
            if any(key not in model_values for key in required_keys):
                failure_reasons = {
                    model_failures.get(key, "model_source_unavailable")
                    for key in required_keys
                    if key not in model_values
                }
                reason = (
                    "model_lifecycle_ineligible"
                    if "model_lifecycle_ineligible" in failure_reasons
                    else (
                        "model_slice_unavailable"
                        if "model_slice_unavailable" in failure_reasons
                        else "model_source_unavailable"
                    )
                )
                scouts.extend(
                    _invalid_resolution_records(
                        graph=graph,
                        record=record,
                        resolution=resolution,
                        reason=reason,
                        protocol=protocol,
                    )
                )
                continue
            try:
                trials = enumerate_fixed_trials(
                    pair_graph,
                    model_series_by_asset=model_values,
                    model_resolutions=(resolution,),
                    protocol=protocol,
                )
            except TypeError, ValueError:
                scouts.extend(
                    _invalid_resolution_records(
                        graph=graph,
                        record=record,
                        resolution=resolution,
                        reason="model_slice_invalid",
                        protocol=protocol,
                    )
                )
                continue
            for trial in trials:
                trials_by_id[trial.candidate_id] = trial
                try:
                    scouts.append(
                        _trial_scout_record(
                            trial,
                            model_series=model_values,
                            as_of=generation.definition.eligible_information_end,
                            protocol=protocol,
                        )
                    )
                except ArithmeticError, TypeError, ValueError:
                    scouts.append(
                        _invalid_scout_for_trial(
                            trial,
                            reason="scout_evaluation_failed",
                        )
                    )
    return snapshot.records, graph.records, tuple(scouts), trials_by_id


def _promotion_with_replay(
    promotion: PromotionRecord,
    reference: ReplayReference,
    attempt: ReplayAttemptRecord,
) -> PromotionRecord:
    if reference.status != attempt.attempt_status.value:
        raise ScannerRunError("replay service status does not match durable attempt")
    if reference.deep_replay_run_id != attempt.deep_replay_run_id:
        raise ScannerRunError("replay service run ID does not match durable attempt")
    return replace(
        promotion,
        direct_execution_instrument_id=reference.direct_execution_instrument_id,
        deep_replay_run_id=attempt.deep_replay_run_id,
        deep_replay_status=attempt.attempt_status.value,
        economic_gate_status=reference.economic_gate_status,
    )


def run_scan(
    *,
    as_of: datetime,
    horizons: tuple[ScannerHorizon, ...],
    data_root: str | Path,
    run_root: str | Path,
    pins: Sequence[ScannerPinSpec] = (),
    replay_service: ScannerReplayService,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> ScanRunResult:
    """Run one frozen scan sequentially, delegating only authoritative replay outward."""

    data_path = Path(data_root).resolve()
    run_path = Path(run_root).resolve()
    pin_tuple = tuple(pins)
    prepared = _prepare_inputs(
        as_of=as_of,
        horizons=tuple(horizons),
        data_root=data_path,
        pins=pin_tuple,
        protocol=protocol,
    )
    generation = start_scan_generation(run_path, prepared.definition)

    eligible_rows: list[EligibleAssetRecord] = []
    neighbor_rows: list[NeighborRecord] = []
    scout_rows: list[ScoutTrialRecord] = []
    trials_by_id: dict[str, ScannerTrial] = {}
    scouts_by_horizon: dict[ScannerHorizon, list[ScoutTrialRecord]] = {
        horizon: [] for horizon in horizons
    }

    for horizon in horizons:
        for venue in protocol.venues:
            eligible, neighbors, scouts, scope_trials = _search_scope(
                prepared=prepared,
                generation=generation,
                venue=venue,
                horizon=horizon,
                pins=pin_tuple,
                protocol=protocol,
            )
            eligible_rows.extend(eligible)
            neighbor_rows.extend(neighbors)
            scout_rows.extend(scouts)
            scouts_by_horizon[horizon].extend(scouts)
            overlap = set(trials_by_id) & set(scope_trials)
            if overlap:
                raise ScannerRunError("deterministic scanner candidate ID collision")
            trials_by_id.update(scope_trials)

    promotions: list[PromotionRecord] = []
    for horizon in horizons:
        promotions.extend(
            apply_promotion_policy(
                tuple(scouts_by_horizon[horizon]),
                protocol=protocol,
            )
        )

    write_scan_tables(
        generation,
        eligible_assets=tuple(eligible_rows),
        neighbors=tuple(neighbor_rows),
        scout_trials=tuple(scout_rows),
        promotions=tuple(promotions),
    )

    for index, promotion in enumerate(tuple(promotions)):
        if not promotion.selected_for_replay:
            continue
        trial = trials_by_id.get(promotion.candidate_id)
        if trial is None:
            raise ScannerRunError("selected promotion has no immutable scanner trial")
        attempt = enumerate_replay_attempt(generation, promotion)
        if attempt.attempt_status is ReplayAttemptStatus.ENUMERATED:
            reference = replay_service.execute(
                generation=generation,
                attempt_id=attempt.attempt_id,
                trial=trial,
                catalog=prepared.catalog,
                data_root=data_path,
                run_root=run_path,
            )
        else:
            reference = replay_service.recover(
                generation=generation,
                attempt=attempt,
                trial=trial,
                catalog=prepared.catalog,
                data_root=data_path,
                run_root=run_path,
            )
        persisted = read_replay_attempt(generation, attempt.attempt_id)
        promotions[index] = _promotion_with_replay(
            promotion,
            reference,
            persisted,
        )
        write_scan_tables(
            generation,
            eligible_assets=tuple(eligible_rows),
            neighbors=tuple(neighbor_rows),
            scout_trials=tuple(scout_rows),
            promotions=tuple(promotions),
        )

    final_directory = publish_scan_generation(generation)
    valid_trials = sum(row.trial_status is ScoutTrialStatus.VALID for row in scout_rows)
    survivors = sum(
        row.economic_gate_status == "deep_replay_survivor" for row in promotions
    )
    replay_failures = sum(
        row.deep_replay_status in {"setup_failed", "replay_failed"}
        for row in promotions
    )
    return ScanRunResult(
        scan_id=prepared.definition.scan_id,
        artifact_directory=final_directory,
        eligible_count=sum(row.automatic_eligible for row in eligible_rows),
        excluded_count=sum(not row.automatic_eligible for row in eligible_rows),
        retained_edge_count=len(neighbor_rows),
        enumerated_trial_count=len(scout_rows),
        valid_trial_count=valid_trials,
        invalid_trial_count=len(scout_rows) - valid_trials,
        automatic_promotion_count=sum(row.automatic_selected for row in promotions),
        budget_exclusion_count=sum(
            row.promotion_status.value == "automatic_excluded" for row in promotions
        ),
        replay_survivor_count=survivors,
        replay_failure_count=replay_failures,
    )


__all__ = [
    "ReplayReference",
    "ScanRunResult",
    "ScannerReplayService",
    "ScannerRunError",
    "run_scan",
]
