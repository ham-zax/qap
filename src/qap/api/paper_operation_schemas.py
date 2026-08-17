"""Typed read-only DTOs for deterministic forward-paper operation artifacts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class _Dto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PaperOperationOrderDto(_Dto):
    phase: str
    asset: str
    route_id: str
    requested_source_quantity: str
    fill_ids: tuple[str, ...]
    leg_reason: str | None


class PaperOperationFillDto(_Dto):
    fill_id: str
    decision_id: str
    execution_timestamp: datetime
    venue: str
    venue_symbol: str
    side: str
    base_quantity: str
    reference_price: str
    execution_price: str
    gross_quote_notional: str
    fee_quote: str
    slippage_quote: str
    balance_deltas: dict[str, str]


class PaperMarketMetadataDto(_Dto):
    venue: str
    venue_symbol: str
    base: str
    quote: str
    status: str
    price_tick: str
    minimum_price: str | None
    maximum_price: str | None
    quantity_step: str
    minimum_quantity: str | None
    maximum_quantity: str | None
    minimum_notional: str | None
    maximum_notional: str | None
    minimum_notional_applies_to_market: bool
    maximum_notional_applies_to_market: bool
    notional_average_price_minutes: int
    market_quantity_step: str | None
    market_minimum_quantity: str | None
    market_maximum_quantity: str | None


class PaperTrackingErrorDto(_Dto):
    asset: str
    target_weight: str
    actual_weight: str
    weight_error: str
    unfilled_quantity: str
    unfilled_value: str


class PaperReconciliationEconomicDifferenceDto(_Dto):
    fill_id: str
    field: str
    reported: str
    recomputed: str


class PaperReconciliationDto(_Dto):
    matches: bool
    reported_fee_total: str
    recomputed_fee_total: str
    reported_turnover: str
    recomputed_turnover: str
    reported_slippage_total: str
    recomputed_slippage_total: str
    expected_terminal_value: str | None
    recomputed_terminal_value: str | None
    economic_differences: tuple[PaperReconciliationEconomicDifferenceDto, ...]


class PaperResearchBoundaryDto(_Dto):
    eligible_for_parameter_selection: bool
    eligible_for_model_promotion: bool
    eligible_for_deployment_evidence: bool
    rule: str


class PaperOperationErrorDto(_Dto):
    code: str
    message: str
    context: dict[str, str]


class PaperOperationSummaryDto(_Dto):
    schema_version: Literal["qap.api.paper_operation_summary.v1"] = (
        "qap.api.paper_operation_summary.v1"
    )
    artifact_status: Literal["valid", "invalid"]
    operation_id: str
    data_role: Literal["forward_paper"] | None = None
    evidence_class: Literal["operational_dry_run"] | None = None
    prospective_candidate_evidence: Literal[False] | None = None
    execution_timestamp: datetime | None = None
    reconciliation_matches: bool | None = None
    fill_count: int | None = None
    total_fee_quote: str | None = None
    total_slippage_quote: str | None = None
    bridge_residual: str | None = None
    route_ids: tuple[str, ...] | None = None
    error: PaperOperationErrorDto | None = None


class PaperOperationDetailDto(_Dto):
    schema_version: Literal["qap.api.paper_operation.v1"] = "qap.api.paper_operation.v1"
    operation_id: str
    data_role: Literal["forward_paper"]
    evidence_class: Literal["operational_dry_run"]
    prospective_candidate_evidence: Literal[False]
    execution_timestamp: datetime
    input_fingerprint: str
    code_fingerprint: str
    fee_bps: str
    slippage_bps: str
    source_note: str
    bridge: str
    starting_holdings: dict[str, str]
    target_weights: dict[str, str]
    valuation_prices: dict[str, str]
    reference_prices: dict[str, str]
    market_notional_reference_prices: dict[str, str]
    market_metadata: dict[str, PaperMarketMetadataDto]
    orders: tuple[PaperOperationOrderDto, ...]
    fills: tuple[PaperOperationFillDto, ...]
    ending_holdings: dict[str, str]
    bridge_target_quantity: str
    bridge_residual: str
    tracking_errors: tuple[PaperTrackingErrorDto, ...]
    total_fee_quote: str
    total_slippage_quote: str
    reconciliation_matches: bool
    reconciliation: PaperReconciliationDto
    research_boundary: PaperResearchBoundaryDto


__all__ = [
    "PaperMarketMetadataDto",
    "PaperOperationErrorDto",
    "PaperOperationDetailDto",
    "PaperOperationFillDto",
    "PaperOperationOrderDto",
    "PaperOperationSummaryDto",
    "PaperReconciliationDto",
    "PaperReconciliationEconomicDifferenceDto",
    "PaperResearchBoundaryDto",
    "PaperTrackingErrorDto",
]
