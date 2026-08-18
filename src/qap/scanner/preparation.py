"""Scanner input admission, lifecycle replay, and frozen scan preparation."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from qap.market import (
    AssetIdentityContinuity,
    BarInterval,
    InstrumentLifecycleEvent,
    InstrumentLifecycleEvidence,
    LifecycleConfidence,
    LifecycleEventType,
    LifecycleSourceType,
)
from qap.portfolio import AssetId
from qap.scanner.catalog import (
    ResolvedCatalogSource,
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    catalog_semantic_identity,
    load_scanner_catalog,
    resolve_catalog_source,
)
from qap.scanner.models import ScanDefinition, ScanInputIdentity, ScannerPinSpec
from qap.scanner.protocol import ScannerHorizon, ScannerProtocol, protocol_identity
from qap.scanner.slices import EvaluatedSeries, evaluate_series
from qap.scanner.universe import (
    HistoricalEligibilityState,
    classify_historical_eligibility,
)


class ScannerRunError(RuntimeError):
    """Generation-level scanner failure that must abort publication."""


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
    manual_replay_candidate_ids: tuple[str, ...],
    catalog_admission_guard: Callable[[ScannerCatalog], None],
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
    catalog_admission_guard(catalog)
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
        sorted(
            [token for pin in pins for token in pin.semantic_tokens()]
            + [
                f"manual_replay:{candidate_id}"
                for candidate_id in manual_replay_candidate_ids
            ]
        )
    )
    definition = ScanDefinition(
        scanner_protocol_version=protocol.protocol_id,
        protocol_identity=protocol_identity(protocol),
        catalog_identity=catalog_semantic_identity(catalog),
        universe_policy_version=protocol.universe_policy_version,
        candidate_generator_version=protocol.candidate_generator_version,
        template_set_version=protocol.template_set_version,
        promotion_policy_version=protocol.promotion_policy_version,
        cost_policy_reference=protocol.cost_policy.policy_id,
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


__all__ = [
    "ScannerRunError",
    "_PreparedInputs",
    "_evidence_for_source",
    "_prepare_inputs",
]
