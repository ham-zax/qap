"""HTTP DTOs for terminal Scanner-V1 basket evidence."""

from datetime import datetime
from typing import Literal

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


class BasketSummaryDto(ApiDto):
    artifact_status: Literal["valid", "invalid"]
    basket_id: str
    source_scan_id: str | None = None
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
    qap_experiment_run_id: str | None
    qap_portfolio_run_id: str | None
    resolver_audit_available: bool


__all__ = [
    "BasketDetailDto",
    "BasketEdgeDto",
    "BasketListDto",
    "BasketSummaryDto",
]
