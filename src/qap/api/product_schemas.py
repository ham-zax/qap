"""HTTP DTOs for the Product Research Universe boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

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


__all__ = [
    "AssetAdmissionRequestDto",
    "DirectorySourceDto",
    "IdentityMappingRequestDto",
    "IdentityReviewDto",
    "ResearchUniverseAssetDto",
    "ResearchUniverseDto",
    "ResearchUniverseVenueDto",
]
