"""HTTP contracts for Product current-approved research readiness and launch."""

from datetime import datetime
from typing import Literal

from pydantic import field_validator

from qap.api.product_schemas import MarketDataMaintenanceDto, ProductApiDto

ReasonCode = Literal[
    "not_approved",
    "identity_review_required",
    "current_market_unavailable",
    "history_missing",
    "history_insufficient",
    "refresh_running",
    "refresh_failed",
    "direct_market_unavailable",
    "insufficient_ready_scope",
]


class ReadinessReasonDto(ProductApiDto):
    code: ReasonCode
    detail: str
    blocking: bool


class GenerationBindingDto(ProductApiDto):
    dataset_id: str
    semantic_fingerprint: str
    interval: str


class ResearchPathReadinessDto(ProductApiDto):
    canonical_asset_id: str
    venue: Literal["binance", "gate"]
    venue_symbol: str
    ready: bool
    data_through: datetime | None
    reasons: tuple[ReadinessReasonDto, ...]
    generations: tuple[GenerationBindingDto, ...]


class ResearchAssetReadinessDto(ProductApiDto):
    canonical_asset_id: str
    approved: bool
    identity_state: Literal["resolved", "review_required"]
    ready: bool
    reasons: tuple[ReadinessReasonDto, ...]
    paths: tuple[ResearchPathReadinessDto, ...]


class DirectMarketReadinessDto(ProductApiDto):
    venue: Literal["binance", "gate"]
    asset_a: str
    asset_b: str
    venue_symbol: str | None
    status: Literal["ready", "unavailable", "history_missing", "history_insufficient"]
    reasons: tuple[ReadinessReasonDto, ...]
    generations: tuple[GenerationBindingDto, ...]


class CurrentApprovedReadinessDto(ProductApiDto):
    schema_version: Literal["qap.api.current_approved_readiness.v1"] = (
        "qap.api.current_approved_readiness.v1"
    )
    claim_id: str
    claim_label: str
    claim_identity: str
    scanner_protocol_id: str
    scanner_protocol_identity: str
    horizon: Literal["short", "medium", "swing"]
    readiness_id: str
    directory_id: str | None
    directory_observed_at: datetime | None
    catalog_identity: str | None
    safe_cutoff: datetime | None
    approved_asset_count: int
    ready_asset_count: int
    ready_path_count: int
    ready_venues: tuple[Literal["binance", "gate"], ...]
    assets: tuple[ResearchAssetReadinessDto, ...]
    direct_markets: tuple[DirectMarketReadinessDto, ...]
    maintenance: MarketDataMaintenanceDto
    reasons: tuple[ReadinessReasonDto, ...]
    ready_for_research: bool


class CurrentApprovedResearchRequestDto(ProductApiDto):
    horizon: Literal["short", "medium", "swing"]
    readiness_id: str

    @field_validator("readiness_id")
    @classmethod
    def validate_readiness_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("readiness_id must be a 64-character SHA-256 fingerprint")
        return normalized


class ProductRunScanRequestDto(CurrentApprovedResearchRequestDto):
    research_mode: Literal["current_approved"] = "current_approved"


__all__ = [
    "CurrentApprovedReadinessDto",
    "CurrentApprovedResearchRequestDto",
    "DirectMarketReadinessDto",
    "GenerationBindingDto",
    "ProductRunScanRequestDto",
    "ReadinessReasonDto",
    "ResearchAssetReadinessDto",
    "ResearchPathReadinessDto",
]
