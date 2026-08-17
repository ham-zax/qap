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


class PaperResearchBoundaryDto(_Dto):
    eligible_for_parameter_selection: bool
    eligible_for_model_promotion: bool
    eligible_for_deployment_evidence: bool
    rule: str


class PaperOperationSummaryDto(_Dto):
    schema_version: Literal["qap.api.paper_operation_summary.v1"] = (
        "qap.api.paper_operation_summary.v1"
    )
    operation_id: str
    data_role: Literal["forward_paper"]
    execution_timestamp: datetime
    reconciliation_matches: bool
    fill_count: int
    total_fee_quote: str
    total_slippage_quote: str
    bridge_residual: str
    route_ids: tuple[str, ...]


class PaperOperationDetailDto(_Dto):
    schema_version: Literal["qap.api.paper_operation.v1"] = "qap.api.paper_operation.v1"
    operation_id: str
    data_role: Literal["forward_paper"]
    execution_timestamp: datetime
    input_fingerprint: str
    source_note: str
    bridge: str
    starting_holdings: dict[str, str]
    target_weights: dict[str, str]
    valuation_prices: dict[str, str]
    reference_prices: dict[str, str]
    market_metadata: dict[str, PaperMarketMetadataDto]
    orders: tuple[PaperOperationOrderDto, ...]
    fills: tuple[PaperOperationFillDto, ...]
    ending_holdings: dict[str, str]
    bridge_target_quantity: str
    bridge_residual: str
    total_fee_quote: str
    total_slippage_quote: str
    reconciliation_matches: bool
    research_boundary: PaperResearchBoundaryDto


__all__ = [
    "PaperMarketMetadataDto",
    "PaperOperationDetailDto",
    "PaperOperationFillDto",
    "PaperOperationOrderDto",
    "PaperOperationSummaryDto",
    "PaperResearchBoundaryDto",
]
