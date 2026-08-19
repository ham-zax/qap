"""HTTP DTOs for terminal Scanner-V1 basket evidence."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from qap.api.scanner_schemas import ResearchClaimDto
from qap.api.schemas import ApiDto, ErrorDetailDto


class BasketEdgeDto(ApiDto):
    candidate_id: str
    pair_id: str
    asset_a: str
    asset_b: str
    candidate_orientation: str
    resolution: str
    model_family: str
    template_id: str
    automatic_neighbor_selected: bool
    manual_pinned: bool
    automatic_selected: bool
    manual_selected: bool
    deep_replay_status: str | None
    deep_replay_failure_reason: str | None
    deep_replay_run_id: str | None
    economic_gate_status: str | None


class BasketExecutionGenerationDto(ApiDto):
    asset_id: str
    dataset_id: str
    relative_path: str
    source_artifact_fingerprint: str


class BasketSummaryDto(ApiDto):
    artifact_status: Literal["valid", "invalid"]
    basket_id: str
    source_scan_id: str | None = None
    source_claim: ResearchClaimDto | None = None
    source_scanner_protocol_id: str | None = None
    source_scanner_protocol_identity: str | None = None
    basket_protocol_id: str | None = None
    basket_protocol_identity: str | None = None
    source_momentum_scan_id: str | None = None
    source_as_of: datetime | None = None
    venue: str | None = None
    horizon: str | None = None
    decision_resolution: str | None = None
    economic_assets: tuple[str, ...] = ()
    forensic: bool | None = None
    attempt_status: str | None = None
    economic_gate_status: str | None = None
    qap_run_id: str | None = None
    error: ErrorDetailDto | None = None


class BasketListDto(ApiDto):
    schema_version: Literal["qap.api.basket_list.v1"] = "qap.api.basket_list.v1"
    items: tuple[BasketSummaryDto, ...]


class BasketDetailDto(ApiDto):
    schema_version: Literal["qap.api.basket_detail.v1"] = "qap.api.basket_detail.v1"
    summary: BasketSummaryDto
    selected_edges: tuple[BasketEdgeDto, ...]
    execution_generations: tuple[BasketExecutionGenerationDto, ...] | None = None
    qap_experiment_run_id: str | None
    qap_portfolio_run_id: str | None
    resolver_audit_available: bool


class BasketRunRequestDto(ApiDto):
    scan_id: str
    venue: Literal["binance", "gate"]
    horizon: Literal["short", "medium", "swing"]
    decision_resolution: str
    economic_assets: tuple[str, ...] = Field(min_length=3, max_length=6)
    candidate_ids: tuple[str, ...] = Field(min_length=1)
    momentum_scan_id: str | None = None


__all__ = [
    "BasketDetailDto",
    "BasketEdgeDto",
    "BasketExecutionGenerationDto",
    "BasketListDto",
    "BasketRunRequestDto",
    "BasketSummaryDto",
]
