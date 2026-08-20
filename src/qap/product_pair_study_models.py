"""Immutable read models and projections for Product Pair Study."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from qap.market import AlignedBarSeries, BarInterval, ValidatedBarSeries
from qap.portfolio import AssetId, PairOrientation
from qap.product_market_data_generation import provenance_relative_path
from qap.product_market_data_models import MarketDataGenerationProvenance
from qap.product_universe import ProductResearchScope, ResolvedProductInstrument
from qap.relationship import RelationshipObservation
from qap.scanner.protocol import ScannerHorizon

DataStatus = Literal["ready", "needs_setup"]
DirectMarketStatus = Literal["ready", "needs_data", "unavailable"]
ReferenceStatus = Literal["ready", "needs_data", "unavailable"]
BridgeStatus = Literal["not_available_in_current_recipe_contract"]


@dataclass(frozen=True, slots=True)
class PairStudyReason:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class PairStudyGenerationRef:
    dataset_id: str
    relative_path: str
    provenance_relative_path: str
    semantic_fingerprint: str
    venue: str
    venue_symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    coverage_start: datetime
    coverage_end_exclusive: datetime
    directory_source_id: str
    directory_source_fingerprint: str


@dataclass(frozen=True, slots=True)
class PairStudyQuestion:
    asset_a: str
    asset_b: str
    canonical_pair: tuple[str, str]
    orientation: str
    horizon: str
    venue: str
    available_venues: tuple[str, ...]
    coordinate_asset: str
    interval: str
    safe_cutoff: datetime | None


@dataclass(frozen=True, slots=True)
class PairStudyDirectMarket:
    status: DirectMarketStatus
    venue: str
    venue_symbol: str | None
    base_asset: str | None
    quote_asset: str | None
    generation: PairStudyGenerationRef | None


@dataclass(frozen=True, slots=True)
class PairStudyData:
    status: DataStatus
    reasons: tuple[PairStudyReason, ...]
    asset_a_path: PairStudyGenerationRef | None
    asset_b_path: PairStudyGenerationRef | None
    direct_market: PairStudyDirectMarket


@dataclass(frozen=True, slots=True)
class PairStudyObservation:
    model_id: str
    model_version: str
    orientation: str
    fit_reciprocity: str
    evidence_reciprocity: str
    status: str
    window_observations: int
    required_observations: int
    coverage_observations: int
    as_of: datetime
    base_source_fingerprint: str
    quote_source_fingerprint: str
    input_fingerprint: str
    values: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class PairStudyRelationship:
    raw_ratio_current: float
    log_ratio_current: float
    normalized_base_current: float
    normalized_quote_current: float
    rolling_log_ratio: PairStudyObservation
    residual_ols: PairStudyObservation


@dataclass(frozen=True, slots=True)
class PairStudyAnalysisLens:
    asset: str
    status: ReferenceStatus
    generation: PairStudyGenerationRef | None
    reason: PairStudyReason | None


@dataclass(frozen=True, slots=True)
class PairStudyEconomicExpression:
    direct_status: DirectMarketStatus
    bridge_status: BridgeStatus
    default_recipe_declarable: bool
    reasons: tuple[PairStudyReason, ...]


@dataclass(frozen=True, slots=True)
class PairStudyContext:
    question: PairStudyQuestion
    data: PairStudyData
    relationship: PairStudyRelationship | None
    analysis_lens: PairStudyAnalysisLens | None
    economic_expression: PairStudyEconomicExpression
    directory_id: str


@dataclass(frozen=True, slots=True)
class PairStudyPoint:
    timestamp: datetime
    value: float


@dataclass(frozen=True, slots=True)
class PairStudyReferenceSeries:
    asset: str
    generation: PairStudyGenerationRef
    base_to_reference: tuple[PairStudyPoint, ...]
    quote_to_reference: tuple[PairStudyPoint, ...]
    base_to_reference_log: tuple[PairStudyPoint, ...]
    quote_to_reference_log: tuple[PairStudyPoint, ...]


@dataclass(frozen=True, slots=True)
class PairStudySeries:
    question: PairStudyQuestion
    asset_a_path: PairStudyGenerationRef
    asset_b_path: PairStudyGenerationRef
    base_source_fingerprint: str
    quote_source_fingerprint: str
    ratio: tuple[PairStudyPoint, ...]
    log_ratio: tuple[PairStudyPoint, ...]
    normalized_base: tuple[PairStudyPoint, ...]
    normalized_quote: tuple[PairStudyPoint, ...]
    analysis_reference: PairStudyReferenceSeries | None


@dataclass(frozen=True, slots=True)
class LoadedPairStudyGeneration:
    ref: PairStudyGenerationRef
    series: ValidatedBarSeries


@dataclass(frozen=True, slots=True)
class PairStudySelection:
    scope: ProductResearchScope
    asset_a: AssetId
    asset_b: AssetId
    orientation: PairOrientation
    horizon: ScannerHorizon
    interval: BarInterval
    lookback: timedelta
    venue: str
    available_venues: tuple[str, ...]
    asset_a_instrument: ResolvedProductInstrument
    asset_b_instrument: ResolvedProductInstrument
    direct_instrument: ResolvedProductInstrument | None
    reference_asset: AssetId | None
    reference_instrument: ResolvedProductInstrument | None


@dataclass(frozen=True, slots=True)
class ReadyPairStudy:
    question: PairStudyQuestion
    selection: PairStudySelection
    asset_a: LoadedPairStudyGeneration
    asset_b: LoadedPairStudyGeneration
    aligned: AlignedBarSeries
    source_fingerprints: dict[AssetId, str]


def project_observation(value: RelationshipObservation) -> PairStudyObservation:
    return PairStudyObservation(
        model_id=value.model_id,
        model_version=value.model_version,
        orientation=f"{value.orientation.base.key}/{value.orientation.quote.key}",
        fit_reciprocity=value.fit_reciprocity.value,
        evidence_reciprocity=value.evidence_reciprocity.value,
        status=value.status.value,
        window_observations=value.window_observations,
        required_observations=value.required_observations,
        coverage_observations=value.coverage_observations,
        as_of=value.as_of,
        base_source_fingerprint=value.base_source_fingerprint,
        quote_source_fingerprint=value.quote_source_fingerprint,
        input_fingerprint=value.input_fingerprint,
        values=tuple(sorted(value.values.items())),
    )


def project_generation(
    provenance: MarketDataGenerationProvenance,
) -> PairStudyGenerationRef:
    return PairStudyGenerationRef(
        dataset_id=provenance.dataset_id,
        relative_path=provenance.relative_path,
        provenance_relative_path=provenance_relative_path(provenance.relative_path),
        semantic_fingerprint=provenance.semantic_fingerprint,
        venue=provenance.venue,
        venue_symbol=provenance.venue_symbol,
        base_asset=provenance.base_asset,
        quote_asset=provenance.quote_asset,
        interval=provenance.interval,
        coverage_start=provenance.coverage_start,
        coverage_end_exclusive=provenance.coverage_end_exclusive,
        directory_source_id=provenance.directory_source_id,
        directory_source_fingerprint=provenance.directory_source_fingerprint,
    )


def project_points(
    timestamps: tuple[datetime, ...],
    values: tuple[float, ...],
    *,
    interval: BarInterval,
) -> tuple[PairStudyPoint, ...]:
    return tuple(
        PairStudyPoint(timestamp=timestamp + interval.duration, value=float(value))
        for timestamp, value in zip(timestamps, values, strict=True)
    )


__all__ = [
    "LoadedPairStudyGeneration",
    "PairStudyAnalysisLens",
    "PairStudyContext",
    "PairStudyData",
    "PairStudyDirectMarket",
    "PairStudyEconomicExpression",
    "PairStudyGenerationRef",
    "PairStudyObservation",
    "PairStudyPoint",
    "PairStudyQuestion",
    "PairStudyReason",
    "PairStudyReferenceSeries",
    "PairStudyRelationship",
    "PairStudySelection",
    "PairStudySeries",
    "ReadyPairStudy",
    "project_generation",
    "project_observation",
    "project_points",
]
