"""HTTP DTOs for the Product Research Universe boundary."""

from datetime import datetime
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.portfolio import AssetId


class ProductApiDto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DirectorySourceDto(ProductApiDto):
    venue: Literal["binance", "gate"]
    observed_at: datetime
    source_id: str
    source_fingerprint: str


class ResearchUniverseVenueDto(ProductApiDto):
    venue: Literal["binance", "gate"]
    venue_symbol: str
    venue_asset_code: str
    status: str
    trading: bool


class ResearchUniverseAssetDto(ProductApiDto):
    canonical_asset_id: str
    approved: bool
    identity_state: Literal["resolved", "review_required"]
    identity_reason: Literal[
        "resolved",
        "mapping_unavailable",
        "identity_version_conflict",
    ]
    asset_identity_version: str | None
    data_state: Literal["not_approved", "needs_data"]
    venues: tuple[ResearchUniverseVenueDto, ...]


class IdentityReviewDto(ProductApiDto):
    venue: Literal["binance", "gate"]
    venue_asset_code: str
    venue_symbols: tuple[str, ...]


class ResearchUniverseDto(ProductApiDto):
    schema_version: Literal["qap.api.research_universe.v1"] = (
        "qap.api.research_universe.v1"
    )
    directory_status: Literal["not_refreshed", "observed"]
    directory_id: str | None
    directory_observed_at: datetime | None
    sources: tuple[DirectorySourceDto, ...]
    assets: tuple[ResearchUniverseAssetDto, ...]
    identity_reviews: tuple[IdentityReviewDto, ...]


class IdentityMappingRequestDto(ProductApiDto):
    venue: Literal["binance", "gate"]
    venue_asset_code: str
    canonical_asset_id: str
    asset_identity_version: str

    @field_validator("venue_asset_code", mode="before")
    @classmethod
    def normalize_venue_asset_code(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("venue_asset_code must be a non-empty string")
        return value.strip().upper()

    @field_validator("canonical_asset_id", mode="before")
    @classmethod
    def normalize_canonical_asset_id(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("canonical_asset_id must be a string")
        return AssetId(value).key

    @field_validator("asset_identity_version", mode="before")
    @classmethod
    def validate_identity_version(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("asset_identity_version must be a non-empty string")
        return value.strip()


class AssetAdmissionRequestDto(ProductApiDto):
    canonical_asset_id: str
    approved: bool

    @field_validator("canonical_asset_id", mode="before")
    @classmethod
    def normalize_canonical_asset_id(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("canonical_asset_id must be a string")
        return AssetId(value).key


class MarketDataPreparationRequestDto(ProductApiDto):
    horizons: tuple[Literal["short", "medium", "swing"], ...]
    asset_ids: tuple[str, str] | None = None
    analysis_reference_ids: tuple[str, ...] | None = None

    @field_validator("horizons")
    @classmethod
    def validate_horizons(
        cls,
        values: tuple[Literal["short", "medium", "swing"], ...],
    ) -> tuple[Literal["short", "medium", "swing"], ...]:
        if not values:
            raise ValueError("horizons must contain at least one timeframe")
        if len(set(values)) != len(values):
            raise ValueError("horizons must not contain duplicates")
        return values

    @field_validator("asset_ids", mode="before")
    @classmethod
    def normalize_asset_ids(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, (tuple, list)):
            raise ValueError("asset_ids must be a list or tuple")
        items = cast(tuple[object, ...] | list[object], value)
        if len(items) != 2:
            raise ValueError("asset_ids must contain exactly two economic assets")
        normalized = tuple(AssetId(item).key for item in items if isinstance(item, str))
        if len(normalized) != len(items):
            raise ValueError("asset_ids must contain canonical asset strings")
        if len(set(normalized)) != 2:
            raise ValueError("asset_ids must contain two distinct economic assets")
        return normalized

    @field_validator("analysis_reference_ids", mode="before")
    @classmethod
    def normalize_analysis_reference_ids(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, (tuple, list)):
            raise ValueError("analysis_reference_ids must be a list or tuple")
        items = cast(tuple[object, ...] | list[object], value)
        normalized = tuple(AssetId(item).key for item in items if isinstance(item, str))
        if len(normalized) != len(items):
            raise ValueError("analysis_reference_ids must contain asset strings")
        if len(set(normalized)) != len(normalized):
            raise ValueError("analysis_reference_ids must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_selected_scope(self) -> "MarketDataPreparationRequestDto":
        if self.analysis_reference_ids and self.asset_ids is None:
            raise ValueError("analysis_reference_ids require asset_ids")
        return self


class MarketDataMaintenanceDto(ProductApiDto):
    status: Literal["idle", "running", "failed"]
    kind: Literal["prepare_market_data", "refresh_market_data"] | None
    started_at: datetime | None
    finished_at: datetime | None
    failure_reason: str | None


class MarketDataGenerationDto(ProductApiDto):
    dataset_id: str
    relative_path: str
    venue: str
    venue_symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    semantic_fingerprint: str
    coverage_start: datetime | None
    coverage_end_exclusive: datetime | None
    provenance_status: Literal["complete", "missing", "invalid"]
    provenance_relative_path: str | None
    issue: str | None


class ProductMarketDataDto(ProductApiDto):
    schema_version: Literal["qap.api.product_market_data.v1"] = (
        "qap.api.product_market_data.v1"
    )
    generations: tuple[MarketDataGenerationDto, ...]
    maintenance: MarketDataMaintenanceDto


__all__ = [
    "AssetAdmissionRequestDto",
    "DirectorySourceDto",
    "IdentityMappingRequestDto",
    "IdentityReviewDto",
    "MarketDataGenerationDto",
    "MarketDataMaintenanceDto",
    "MarketDataPreparationRequestDto",
    "ProductMarketDataDto",
    "ResearchUniverseAssetDto",
    "ResearchUniverseDto",
    "ResearchUniverseVenueDto",
]
