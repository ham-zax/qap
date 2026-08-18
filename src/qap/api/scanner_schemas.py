"""HTTP DTOs for Scanner-V1 discovery and prospective evidence."""

from datetime import datetime
from typing import Literal

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
    schema_version: Literal["qap.api.candidate_list.v1"] = (
        "qap.api.candidate_list.v1"
    )
    scan_id: str
    items: tuple[CandidateSummaryDto, ...]


class CandidateDetailDto(ApiDto):
    schema_version: Literal["qap.api.candidate_detail.v1"] = (
        "qap.api.candidate_detail.v1"
    )
    candidate: CandidateSummaryDto
    forward_cohort_ids: tuple[str, ...]
    qualification_ids: tuple[str, ...]
    basket_ids: tuple[str, ...]


class ScanDetailDto(ApiDto):
    schema_version: Literal["qap.api.scan_detail.v1"] = "qap.api.scan_detail.v1"
    summary: ScanSummaryDto
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
    candidate_capital_ceiling: str | None
    current_state_qap_run_id: str | None
    requested_capital_qap_run_id: str | None
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
    checkpoint_count: int | None = None
    qualification_count: int | None = None
    error: ErrorDetailDto | None = None


class ForwardCohortListDto(ApiDto):
    schema_version: Literal["qap.api.forward_cohort_list.v1"] = (
        "qap.api.forward_cohort_list.v1"
    )
    items: tuple[ForwardCohortSummaryDto, ...]


class ForwardCohortDetailDto(ApiDto):
    schema_version: Literal["qap.api.forward_cohort_detail.v1"] = (
        "qap.api.forward_cohort_detail.v1"
    )
    summary: ForwardCohortSummaryDto
    freezes: tuple[CandidateFreezeDto, ...]
    checkpoints: tuple[ForwardCheckpointDto, ...]
    qualifications: tuple[QualificationDto, ...]


__all__ = [
    "CandidateDetailDto",
    "CandidateFreezeDto",
    "CandidateListDto",
    "CandidateSummaryDto",
    "ForwardCheckpointDto",
    "ForwardCohortDetailDto",
    "ForwardCohortListDto",
    "ForwardCohortSummaryDto",
    "GraphScopeDto",
    "MomentumGenerationDto",
    "MomentumObservationDto",
    "QualificationDto",
    "ScanDetailDto",
    "ScanListDto",
    "ScanSummaryDto",
    "ScannerHorizonDto",
    "ScannerProtocolDto",
    "UniverseAssetDto",
]
