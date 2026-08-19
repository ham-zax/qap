"""HTTP DTOs for Scanner-V1 evidence and bounded application commands."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import Field, JsonValue, field_validator

from qap.api.schemas import ApiDto, ErrorDetailDto


class ScannerHorizonDto(ApiDto):
    horizon: str
    graph_interval: str
    graph_window_seconds: int
    evaluation_window_seconds: int
    model_resolutions: tuple[str, ...]
    momentum_resolution: str
    momentum_formation_seconds: int


class ScannerProtocolDto(ApiDto):
    schema_version: Literal["qap.api.scanner_protocol.v1"] = (
        "qap.api.scanner_protocol.v1"
    )
    protocol_id: str
    protocol_identity: str
    basket_protocol_id: str
    basket_protocol_identity: str
    venues: tuple[str, ...]
    quote_asset: str
    horizons: tuple[ScannerHorizonDto, ...]


class ResearchClaimDto(ApiDto):
    kind: Literal[
        "current_approved_retrospective",
        "historical_pit",
        "versioned_other",
    ]
    label: str
    claim_identity: str | None
    scope_identity: str | None


class ScanSummaryDto(ApiDto):
    artifact_status: Literal["valid", "invalid"]
    scan_id: str
    as_of: datetime | None = None
    eligible_information_end: datetime | None = None
    created_at: datetime | None = None
    venues: tuple[str, ...] = ()
    horizons: tuple[str, ...] = ()
    candidate_count: int | None = None
    selected_replay_count: int | None = None
    survivor_count: int | None = None
    claim: ResearchClaimDto | None = None
    error: ErrorDetailDto | None = None


class ScanListDto(ApiDto):
    schema_version: Literal["qap.api.scan_list.v1"] = "qap.api.scan_list.v1"
    items: tuple[ScanSummaryDto, ...]


class UniverseAssetDto(ApiDto):
    venue: str
    horizon: str
    asset_id: str
    venue_symbol: str
    eligibility_state: str
    eligibility_reason: str
    bar_coverage: float
    longest_missing_run: int
    automatic_eligible: bool
    forensic_research_allowed: bool


class GraphScopeDto(ApiDto):
    venue: str
    horizon: str
    universe_snapshot_id: str
    graph_interval: str
    graph_window_seconds: int
    eligible_asset_count: int
    total_valid_pair_comparisons: int


class MomentumObservationDto(ApiDto):
    asset_id: str
    venue_symbol: str
    status: str
    reason: str
    bar_coverage: float
    longest_missing_run: int
    own_momentum: float | None
    common_mode: float | None
    relative_momentum: float | None
    common_mode_member_count: int
    rank: int | None


class MomentumGenerationDto(ApiDto):
    momentum_scan_id: str
    source_scan_id: str
    venue: str
    horizon: str
    as_of: datetime
    universe_snapshot_id: str
    resolution: str
    formation_seconds: int
    observations: tuple[MomentumObservationDto, ...]


class CandidateSummaryDto(ApiDto):
    candidate_id: str
    scan_id: str
    venue: str
    horizon: str
    pair_id: str
    orientation: str
    resolution: str
    model_family: str
    template_id: str
    trial_status: str
    failure_reason: str | None
    scout_relative_wealth_proxy: float | None
    scout_turnover_proxy: float | None
    signal_count: int
    automatic_neighbor_selected: bool
    manual_pinned: bool
    promotion_rank: int | None = None
    promotion_status: str | None = None
    budget_reason: str | None = None
    automatic_selected: bool = False
    manual_selected: bool = False
    selected_for_replay: bool = False
    deep_replay_status: str | None = None
    deep_replay_run_id: str | None = None
    economic_gate_status: str | None = None
    replay_failure_stage: str | None = None
    replay_failure_reason: str | None = None


class CandidateListDto(ApiDto):
    schema_version: Literal["qap.api.candidate_list.v1"] = "qap.api.candidate_list.v1"
    scan_id: str
    items: tuple[CandidateSummaryDto, ...]


class ProductFollowUpDto(ApiDto):
    state: Literal["start_available", "existing", "unavailable"]
    horizon: str | None
    survivor_count: int
    cohort_id: str | None = None
    reason: str | None = None


class ResearchIdeaForwardCheckpointDto(ApiDto):
    checkpoint_id: str
    active_cohort_id: str
    checkpoint_index: int
    information_end: datetime
    outcome_status: Literal["pending", "partial", "matured", "invalid"]
    qap_run_id: str | None
    strategy_vs_hodl: str | None
    strategy_vs_primary_control: str | None
    baseline_economic_gates_passed: bool | None
    adverse_economic_gates_passed: bool | None
    failure_reason: str | None


class ResearchIdeaCurrentAssessmentDto(ApiDto):
    qualification_id: str
    active_cohort_id: str
    checkpoint_id: str
    as_of: datetime
    requested_capital: str
    state: Literal["research_only", "small_capacity", "tradable_now"]
    reason: str
    candidate_capital_ceiling: str | None


class ResearchIdeaFollowUpMembershipDto(ApiDto):
    selection_cohort_id: str
    membership_kind: Literal["new_freeze", "reselection"]
    candidate_id: str
    source_scan_id: str
    selected_at: datetime
    automatic_selected: bool
    manual_selected: bool
    active_freeze_id: str
    active_cohort_id: str
    active_candidate_id: str
    active_source_scan_id: str
    forward_start: datetime
    forward_end: datetime
    checkpoints: tuple[ResearchIdeaForwardCheckpointDto, ...]
    assessments: tuple[ResearchIdeaCurrentAssessmentDto, ...]


class ResearchIdeaLongitudinalDto(ApiDto):
    historical_discovery_state: Literal["evaluated", "unavailable"]
    historical_replay_state: Literal[
        "supported",
        "not_supported",
        "unavailable",
        "not_completed",
    ]
    later_state: Literal[
        "not_started",
        "waiting_for_later_evidence",
        "later_evidence_accumulating",
        "later_evidence_supported",
        "later_evidence_not_supported",
        "later_evidence_unavailable",
    ]
    later_reason: str | None
    memberships: tuple[ResearchIdeaFollowUpMembershipDto, ...]
    current_evidence_state: Literal["not_assessed", "assessment_available"]
    current_assessments: tuple[ResearchIdeaCurrentAssessmentDto, ...]


class CandidateDetailDto(ApiDto):
    schema_version: Literal["qap.api.candidate_detail.v3"] = (
        "qap.api.candidate_detail.v3"
    )
    candidate: CandidateSummaryDto
    claim: ResearchClaimDto
    product_follow_up: ProductFollowUpDto | None
    longitudinal: ResearchIdeaLongitudinalDto
    forward_cohort_ids: tuple[str, ...]
    qualification_ids: tuple[str, ...]
    basket_ids: tuple[str, ...]


class CompletedResearchScopeStagesDto(ApiDto):
    venue: str
    horizon: str
    scope_asset_count: int
    relationship_comparison_count: int
    retained_relationship_count: int
    enumerated_rule_count: int
    valid_rule_count: int
    invalid_rule_count: int
    selected_for_replay_count: int
    completed_replay_count: int
    replay_unavailable_count: int
    rejected_replay_count: int
    research_idea_count: int


class CompletedResearchStagesDto(ApiDto):
    scopes: tuple[CompletedResearchScopeStagesDto, ...]


class ScanDetailDto(ApiDto):
    schema_version: Literal["qap.api.scan_detail.v3"] = "qap.api.scan_detail.v3"
    summary: ScanSummaryDto
    stages: CompletedResearchStagesDto
    product_follow_up: ProductFollowUpDto | None
    universe: tuple[UniverseAssetDto, ...]
    graph_scopes: tuple[GraphScopeDto, ...]
    momentum_generations: tuple[MomentumGenerationDto, ...]


class CandidateFreezeDto(ApiDto):
    freeze_id: str
    candidate_id: str
    source_scan_id: str
    automatic_selected: bool
    manual_selected: bool
    frozen_at: datetime
    forward_start: datetime
    forward_end: datetime
    horizon: str
    venue: str
    pair_id: str
    orientation: str
    resolution: str
    model_family: str
    template_id: str
    candidate_deep_replay_run_id: str


class ForwardReselectionDto(ApiDto):
    active_freeze_id: str
    candidate_id: str
    source_scan_id: str
    automatic_selected: bool
    manual_selected: bool
    reselected_at: datetime
    active_cohort_id: str
    active_candidate_id: str
    active_source_scan_id: str
    forward_start: datetime
    forward_end: datetime


class ForwardCheckpointDto(ApiDto):
    checkpoint_id: str
    cohort_id: str
    candidate_id: str
    freeze_id: str
    checkpoint_index: int
    information_end: datetime
    outcome_id: str
    outcome_status: str
    qap_run_id: str | None
    strategy_vs_hodl: str | None
    strategy_vs_primary_control: str | None
    baseline_economic_gates_passed: bool | None
    adverse_economic_gates_passed: bool | None


class QualificationDto(ApiDto):
    qualification_id: str
    checkpoint_id: str
    candidate_id: str
    freeze_id: str
    as_of: datetime
    requested_capital: str
    state: str
    reason: str
    capture_snapshot_ids: tuple[str, ...]
    capture_contract_satisfied: bool
    eligibility_resolved: bool
    current_two_way_trading: bool
    order_constraints_satisfied: bool
    market_metadata_fingerprint: str | None
    candidate_capital_ceiling: str | None
    current_state_qap_run_id: str | None
    requested_capital_qap_run_id: str | None
    requested_baseline_gate_passed: bool | None
    requested_adverse_gate_passed: bool | None
    q_star_buy: str | None
    q_safe_buy: str | None
    q_star_sell: str | None
    q_safe_sell: str | None


class ForwardCohortSummaryDto(ApiDto):
    artifact_status: Literal["valid", "invalid"]
    cohort_id: str
    source_scan_id: str | None = None
    horizon: str | None = None
    freeze_at: datetime | None = None
    candidate_ids: tuple[str, ...] = ()
    automatic_member_count: int | None = None
    manual_member_count: int | None = None
    checkpoint_count: int | None = None
    qualification_count: int | None = None
    error: ErrorDetailDto | None = None


class ForwardCohortListDto(ApiDto):
    schema_version: Literal["qap.api.forward_cohort_list.v1"] = (
        "qap.api.forward_cohort_list.v1"
    )
    items: tuple[ForwardCohortSummaryDto, ...]


class ForwardCohortDetailDto(ApiDto):
    schema_version: Literal["qap.api.forward_cohort_detail.v2"] = (
        "qap.api.forward_cohort_detail.v2"
    )
    summary: ForwardCohortSummaryDto
    freezes: tuple[CandidateFreezeDto, ...]
    reselections: tuple[ForwardReselectionDto, ...]
    checkpoints: tuple[ForwardCheckpointDto, ...]
    qualifications: tuple[QualificationDto, ...]


class CaptureReadinessDto(ApiDto):
    schema_version: Literal["qap.api.capture_readiness.v1"] = (
        "qap.api.capture_readiness.v1"
    )
    cohort_id: str
    checkpoint_id: str
    as_of: datetime
    window_start: datetime
    window_end: datetime
    venue: Literal["binance", "gate"]
    venue_symbol: str
    base_asset: str
    quote_asset: str
    l1_expected_slots: int
    l1_captured_slots: int
    l1_overall_coverage: str
    depth_expected_slots: int
    depth_captured_slots: int
    depth_overall_coverage: str
    metadata_available: bool
    ready: bool
    missing_capture_kinds: tuple[Literal["l1", "depth", "metadata"], ...]


class ScannerPinRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    asset_a: str
    asset_b: str
    horizons: tuple[Literal["short", "medium", "swing"], ...] = Field(min_length=1)
    forensic: bool = False


class RunScanRequestDto(ApiDto):
    as_of: datetime
    horizons: tuple[Literal["short", "medium", "swing"], ...] = Field(min_length=1)
    pins: tuple[ScannerPinRequestDto, ...] = ()
    manual_replay_candidate_ids: tuple[str, ...] = ()


class MomentumGenerationRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    horizon: Literal["short", "medium", "swing"]


class FreezeForwardCohortRequestDto(ApiDto):
    scan_id: str
    horizon: Literal["short", "medium", "swing"]
    freeze_at: datetime


class AdvanceForwardCohortRequestDto(ApiDto):
    through: datetime


class CapturePublicEvidenceRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    venue_symbol: str
    base_asset: str
    quote_asset: str
    kind: Literal["l1", "depth", "metadata"]


class QualificationRequestDto(ApiDto):
    cohort_id: str
    checkpoint_id: str
    as_of: datetime
    requested_capital: str

    @field_validator("requested_capital")
    @classmethod
    def validate_capital(cls, value: str) -> str:
        try:
            parsed = Decimal(value.strip())
        except InvalidOperation as exc:
            raise ValueError(
                "requested_capital must be an exact decimal string"
            ) from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ValueError("requested_capital must be positive finite")
        return format(parsed, "f")


class OperationRefDto(ApiDto):
    schema_version: Literal["qap.api.operation_ref.v1"] = "qap.api.operation_ref.v1"
    operation_id: str
    status: Literal["running"] = "running"


class OperationDto(ApiDto):
    schema_version: Literal["qap.api.operation.v1"] = "qap.api.operation.v1"
    operation_id: str
    kind: str
    status: Literal["running", "completed", "failed", "interrupted"]
    requested_at: datetime
    started_at: datetime
    finished_at: datetime | None
    request_summary: dict[str, JsonValue]
    result: dict[str, JsonValue] | None
    failure: ErrorDetailDto | None


class OperationListDto(ApiDto):
    schema_version: Literal["qap.api.operation_list.v1"] = "qap.api.operation_list.v1"
    items: tuple[OperationDto, ...]


__all__ = [
    "AdvanceForwardCohortRequestDto",
    "CandidateDetailDto",
    "CandidateFreezeDto",
    "CandidateListDto",
    "CandidateSummaryDto",
    "CompletedResearchScopeStagesDto",
    "CompletedResearchStagesDto",
    "CaptureReadinessDto",
    "CapturePublicEvidenceRequestDto",
    "ForwardCheckpointDto",
    "ForwardCohortDetailDto",
    "ForwardCohortListDto",
    "ForwardCohortSummaryDto",
    "ForwardReselectionDto",
    "FreezeForwardCohortRequestDto",
    "GraphScopeDto",
    "MomentumGenerationDto",
    "MomentumGenerationRequestDto",
    "MomentumObservationDto",
    "OperationDto",
    "OperationListDto",
    "OperationRefDto",
    "ProductFollowUpDto",
    "QualificationDto",
    "QualificationRequestDto",
    "ResearchClaimDto",
    "ResearchIdeaCurrentAssessmentDto",
    "ResearchIdeaFollowUpMembershipDto",
    "ResearchIdeaForwardCheckpointDto",
    "ResearchIdeaLongitudinalDto",
    "RunScanRequestDto",
    "ScanDetailDto",
    "ScanListDto",
    "ScanSummaryDto",
    "ScannerHorizonDto",
    "ScannerPinRequestDto",
    "ScannerProtocolDto",
    "UniverseAssetDto",
]
