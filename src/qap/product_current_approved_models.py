"""Product current-approved readiness domain records."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from qap.product_maintenance import MarketDataMaintenanceState
from qap.scanner.protocol import ScannerHorizon

ReadinessReasonCode = Literal[
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
DirectMarketStatus = Literal[
    "ready",
    "unavailable",
    "history_missing",
    "history_insufficient",
]


@dataclass(frozen=True, slots=True)
class ReadinessReason:
    code: ReadinessReasonCode
    detail: str
    blocking: bool


@dataclass(frozen=True, slots=True)
class GenerationBinding:
    dataset_id: str
    semantic_fingerprint: str
    interval: str


@dataclass(frozen=True, slots=True)
class ResearchPathReadiness:
    canonical_asset_id: str
    venue: str
    venue_symbol: str
    ready: bool
    data_through: datetime | None
    reasons: tuple[ReadinessReason, ...]
    generations: tuple[GenerationBinding, ...]


@dataclass(frozen=True, slots=True)
class ResearchAssetReadiness:
    canonical_asset_id: str
    approved: bool
    identity_state: str
    ready: bool
    reasons: tuple[ReadinessReason, ...]
    paths: tuple[ResearchPathReadiness, ...]


@dataclass(frozen=True, slots=True)
class DirectMarketReadiness:
    venue: str
    asset_a: str
    asset_b: str
    venue_symbol: str | None
    status: DirectMarketStatus
    reasons: tuple[ReadinessReason, ...]
    generations: tuple[GenerationBinding, ...]


@dataclass(frozen=True, slots=True)
class CurrentApprovedReadiness:
    claim_id: str
    claim_label: str
    claim_identity: str
    scanner_protocol_id: str
    scanner_protocol_identity: str
    horizon: ScannerHorizon
    readiness_id: str
    directory_id: str | None
    directory_observed_at: datetime | None
    catalog_identity: str | None
    safe_cutoff: datetime | None
    approved_asset_count: int
    ready_asset_count: int
    ready_path_count: int
    ready_venues: tuple[str, ...]
    assets: tuple[ResearchAssetReadiness, ...]
    direct_markets: tuple[DirectMarketReadiness, ...]
    maintenance: MarketDataMaintenanceState
    reasons: tuple[ReadinessReason, ...]
    ready_for_research: bool


__all__ = [
    "CurrentApprovedReadiness",
    "DirectMarketReadiness",
    "DirectMarketStatus",
    "GenerationBinding",
    "ReadinessReason",
    "ReadinessReasonCode",
    "ResearchAssetReadiness",
    "ResearchPathReadiness",
]
