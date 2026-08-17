"""HTTP-only DTOs for the read-only QAP API boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from qap.experiment import (
    ExperimentManifest,
    ExperimentResult,
    FinalOosCommitment,
    RunProvenance,
)


class ApiDto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthDto(ApiDto):
    schema_version: Literal["qap.api.health.v1"] = "qap.api.health.v1"
    status: Literal["ok"] = "ok"


class ErrorDetailDto(ApiDto):
    code: str
    message: str
    context: dict[str, str]


class ErrorEnvelopeDto(ApiDto):
    error: ErrorDetailDto


class RunSummaryDto(ApiDto):
    artifact_status: Literal["valid", "invalid"]
    run_id: str
    experiment_name: str | None = None
    research_family_id: str | None = None
    parent_run_id: str | None = None
    universe_mode: str | None = None
    basket: tuple[str, ...] | None = None
    analysis_anchor: str | None = None
    relationship_id: str | None = None
    policy_id: str | None = None
    data_role: str | None = None
    final_oos_consumed: bool | None = None
    status: str | None = None
    primary_metric: str | None = None
    primary_metric_value: str | None = None
    primary_incremental_benchmark: str | None = None
    incremental_vs_primary_control: str | None = None
    incremental_vs_matched_contribution: str | None = None
    created_timestamp: datetime | None = None
    git_dirty: bool | None = None
    sibling_trial_count: int | None = None
    error: ErrorDetailDto | None = None


ExperimentSummaryDto = RunSummaryDto


class ExperimentListDto(ApiDto):
    schema_version: Literal["qap.api.experiment_list.v1"] = "qap.api.experiment_list.v1"
    items: tuple[RunSummaryDto, ...]


class ArtifactSeriesMetadataDto(ApiDto):
    name: str
    schema_version: str
    columns: tuple[str, ...]
    row_count: int


class ExperimentDetailDto(ApiDto):
    schema_version: Literal["qap.api.experiment_detail.v1"] = (
        "qap.api.experiment_detail.v1"
    )
    run_id: str
    sibling_trial_count: int
    manifest: ExperimentManifest
    provenance: RunProvenance
    result: ExperimentResult
    final_oos_commitment: FinalOosCommitment | None
    available_series: tuple[ArtifactSeriesMetadataDto, ...]


class HoldingDto(ApiDto):
    asset: str
    quantity: str
    value: str
    weight: str


class HoldingsSnapshotDto(ApiDto):
    timestamp: datetime
    role: str
    holdings: tuple[HoldingDto, ...]


class CostSummaryDto(ApiDto):
    fill_count: int
    fees_value: str
    slippage_value: str
    turnover_value: str


class FillAuditDto(ApiDto):
    fill_id: str
    side: str
    base: str
    quote: str
    reference_price: str
    execution_price: str
    base_quantity: str
    gross_quote_notional: str
    fee_amount: str
    fee_asset: str
    slippage_value: str


class RebalanceDecisionAuditDto(ApiDto):
    decision_id: str
    decision_time: datetime
    reason: str
    evidence_ids: tuple[str, ...]
    current_weights: dict[str, str] | None
    baseline_target_weights: dict[str, str] | None
    target_weights: dict[str, str] | None
    modeled_fee_bps: str
    modeled_slippage_bps: str
    requested_quantity_deltas: dict[str, str] | None
    selected: bool
    fills: tuple[FillAuditDto, ...]
    post_fill_holdings: tuple[HoldingDto, ...]


class ConcentrationSummaryDto(ApiDto):
    start_max_weight: str
    terminal_max_weight: str
    start_herfindahl: str
    terminal_herfindahl: str


class AssetDeltaDto(ApiDto):
    asset: str
    quantity_delta: str
    value_delta: str


class PortfolioSnapshotDto(ApiDto):
    schema_version: Literal["qap.api.portfolio_snapshot.v1"] = (
        "qap.api.portfolio_snapshot.v1"
    )
    run_id: str
    starting: HoldingsSnapshotDto
    terminal: HoldingsSnapshotDto
    hodl_terminal: HoldingsSnapshotDto
    role_terminals: tuple[HoldingsSnapshotDto, ...]
    allocation_history: tuple[HoldingsSnapshotDto, ...]
    concentration: ConcentrationSummaryDto
    strategy_vs_hodl_terminal_deltas: tuple[AssetDeltaDto, ...]
    strategy_vs_matched_contribution_terminal_deltas: tuple[AssetDeltaDto, ...] | None
    strategy_costs: CostSummaryDto
    rebalance_audit: tuple[RebalanceDecisionAuditDto, ...]


class ExactPointDto(ApiDto):
    timestamp: datetime
    value: str


class PerformanceSeriesDto(ApiDto):
    name: str
    points: tuple[ExactPointDto, ...]


class PortfolioPerformanceDto(ApiDto):
    schema_version: Literal["qap.api.portfolio_performance.v1"] = (
        "qap.api.portfolio_performance.v1"
    )
    run_id: str
    primary_incremental_benchmark: str | None
    maximum_relative_drawdown_vs_hodl: str
    time_below_hodl_seconds: int
    time_below_primary_control_seconds: int | None
    series: tuple[PerformanceSeriesDto, ...]


class FloatPointDto(ApiDto):
    timestamp: datetime
    value: float


class RebalanceMarkerDto(ApiDto):
    timestamp: datetime
    decision_id: str
    selected: bool
    executed: bool
    fill_id: str | None


class RelationshipEvidencePointDto(ApiDto):
    timestamp: datetime
    value: float | None
    status: str
    window_observations: int
    required_observations: int
    coverage_observations: int
    input_fingerprint: str


class RelationshipEvidenceSeriesDto(ApiDto):
    persisted_orientation: str
    model_id: str
    model_version: str
    evidence_field: str
    fit_reciprocity: str
    evidence_reciprocity: str
    base_source_fingerprint: str
    quote_source_fingerprint: str
    points: tuple[RelationshipEvidencePointDto, ...]


class PairEvidenceDto(ApiDto):
    schema_version: Literal["qap.api.pair_evidence.v1"] = "qap.api.pair_evidence.v1"
    run_id: str
    canonical_pair: tuple[str, str]
    requested_orientation: str
    series: tuple[RelationshipEvidenceSeriesDto, ...]


class PairSeriesDto(ApiDto):
    schema_version: Literal["qap.api.pair_series.v1"] = "qap.api.pair_series.v1"
    run_id: str
    canonical_pair: tuple[str, str]
    requested_orientation: str
    available_anchors: tuple[str, ...]
    identity_coordinate_assets: tuple[str, ...]
    interval: str
    base_source_fingerprint: str
    quote_source_fingerprint: str
    fit_reciprocity: str
    evidence_reciprocity: str
    ratio: tuple[FloatPointDto, ...]
    log_ratio: tuple[FloatPointDto, ...]
    normalized_base: tuple[FloatPointDto, ...]
    normalized_quote: tuple[FloatPointDto, ...]
    rebalance_markers: tuple[RebalanceMarkerDto, ...]
    descriptive_only: bool


class AnchorLensDto(ApiDto):
    schema_version: Literal["qap.api.anchor_lens.v1"] = "qap.api.anchor_lens.v1"
    run_id: str
    canonical_pair: tuple[str, str]
    requested_orientation: str
    anchor: str
    identity_coordinate_assets: tuple[str, ...]
    interval: str
    base_source_fingerprint: str
    quote_source_fingerprint: str
    anchor_source_fingerprint: str | None
    fit_reciprocity: str
    evidence_reciprocity: str
    reduction: str
    pair_ratio: tuple[FloatPointDto, ...]
    pair_log_ratio: tuple[FloatPointDto, ...]
    base_to_anchor: tuple[FloatPointDto, ...]
    quote_to_anchor: tuple[FloatPointDto, ...]
    base_to_anchor_log: tuple[FloatPointDto, ...]
    quote_to_anchor_log: tuple[FloatPointDto, ...]
    max_ratio_decomposition_error: float
    max_log_decomposition_error: float
    descriptive_only: bool


__all__ = [
    "AnchorLensDto",
    "ApiDto",
    "ArtifactSeriesMetadataDto",
    "AssetDeltaDto",
    "ConcentrationSummaryDto",
    "CostSummaryDto",
    "ErrorDetailDto",
    "ErrorEnvelopeDto",
    "ExactPointDto",
    "ExperimentDetailDto",
    "ExperimentListDto",
    "ExperimentSummaryDto",
    "FillAuditDto",
    "FloatPointDto",
    "HealthDto",
    "HoldingDto",
    "HoldingsSnapshotDto",
    "PairEvidenceDto",
    "PairSeriesDto",
    "PerformanceSeriesDto",
    "PortfolioPerformanceDto",
    "PortfolioSnapshotDto",
    "RebalanceDecisionAuditDto",
    "RebalanceMarkerDto",
    "RelationshipEvidencePointDto",
    "RelationshipEvidenceSeriesDto",
    "RunSummaryDto",
]
