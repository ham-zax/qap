"""Frozen universe contracts and pure mapping validation; no mutable owner."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.asset_resolver import AssetResolutionProposal
from qap.market.instruments import VenueInstrument
from qap.portfolio import AssetId
from qap.product_directory_models import (
    DirectoryMarket,
    DirectoryRefreshResult,
    DirectorySource,
)

Venue = Literal["binance", "gate"]
IdentityState = Literal["resolved", "review_required"]
IdentityReason = Literal["resolved", "mapping_unavailable", "identity_version_conflict"]
DataState = Literal["not_approved", "needs_data"]


class ProductUniverseError(RuntimeError):
    """Raised when Product universe state cannot be read or changed safely."""


class ProductDirectoryRefreshError(ProductUniverseError):
    """No current or previously observed public directory is available."""


def universe_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class AssetIdentityMapping(_FrozenModel):
    venue: Venue
    venue_asset_code: str
    canonical_asset_id: str
    asset_identity_version: str
    confirmed_at: datetime
    accepted_by: Literal["operator", "policy", "review"] = "operator"
    source: str = "operator"
    registry_coin_id: str | None = None
    evidence_fingerprint: str | None = None

    @field_validator("venue", mode="before")
    @classmethod
    def normalize_venue(cls, value: object) -> str:
        return _text(value, field="venue").lower()

    @field_validator("venue_asset_code", mode="before")
    @classmethod
    def normalize_venue_asset_code(cls, value: object) -> str:
        return _text(value, field="venue_asset_code").upper()

    @field_validator("canonical_asset_id", mode="before")
    @classmethod
    def normalize_canonical_asset_id(cls, value: object) -> str:
        return AssetId(_text(value, field="canonical_asset_id")).key

    @field_validator("asset_identity_version", mode="before")
    @classmethod
    def normalize_identity_version(cls, value: object) -> str:
        return _text(value, field="asset_identity_version")

    @field_validator("confirmed_at")
    @classmethod
    def validate_confirmed_at(cls, value: datetime) -> datetime:
        return universe_utc(value, field="confirmed_at")


class ProductUniverseState(_FrozenModel):
    schema_version: Literal[
        "qap.product.research-universe.v1", "qap.product.research-universe.v2"
    ] = "qap.product.research-universe.v2"
    updated_at: datetime | None = None
    approved_asset_ids: tuple[str, ...] = ()
    identity_mappings: tuple[AssetIdentityMapping, ...] = ()
    resolution_reviews: tuple[AssetResolutionProposal, ...] = ()
    retired_identity_mappings: tuple[AssetIdentityMapping, ...] = ()
    pending_admission_asset_ids: tuple[str, ...] = ()

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: datetime | None) -> datetime | None:
        return None if value is None else universe_utc(value, field="updated_at")

    @field_validator("approved_asset_ids", mode="before")
    @classmethod
    def normalize_approved_assets(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (tuple, list)):
            raise TypeError("approved_asset_ids must be a list or tuple")
        items = cast(list[object] | tuple[object, ...], value)
        assets = tuple(
            sorted(
                AssetId(_text(item, field="approved_asset_id")).key for item in items
            )
        )
        if len(assets) != len(set(assets)):
            raise ValueError("approved_asset_ids must not contain duplicates")
        return assets

    @model_validator(mode="after")
    def validate_mapping_keys(self) -> Self:
        keys = tuple(
            (mapping.venue, mapping.venue_asset_code)
            for mapping in self.identity_mappings
        )
        if len(keys) != len(set(keys)):
            raise ValueError("identity mappings must be unique by venue and asset code")
        return self


@dataclass(frozen=True, slots=True)
class ResearchUniverseVenue:
    venue: str
    venue_symbol: str
    venue_asset_code: str
    status: str
    trading: bool


@dataclass(frozen=True, slots=True)
class ResearchUniverseAsset:
    asset: AssetId
    approved: bool
    identity_state: IdentityState
    identity_reason: IdentityReason
    asset_identity_version: str | None
    data_state: DataState
    venues: tuple[ResearchUniverseVenue, ...]


@dataclass(frozen=True, slots=True)
class IdentityReview:
    venue: str
    venue_asset_code: str
    venue_symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchUniverseProjection:
    directory_id: str | None
    directory_observed_at: datetime | None
    sources: tuple[DirectorySource, ...]
    assets: tuple[ResearchUniverseAsset, ...]
    identity_reviews: tuple[IdentityReview, ...]
    directory_refreshes: tuple[DirectoryRefreshResult, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedProductInstrument:
    instrument: VenueInstrument
    base_asset_identity_version: str
    quote_asset_identity_version: str
    directory_observed_at: datetime
    source_id: str
    source_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProductResearchScope:
    directory_id: str
    directory_observed_at: datetime
    approved_assets: tuple[AssetId, ...]
    instruments: tuple[ResolvedProductInstrument, ...]
    economic_identity_confirmed: bool = True


def _contradicted_mapping(mapping: AssetIdentityMapping) -> bool:
    return (mapping.venue, mapping.venue_asset_code, mapping.canonical_asset_id) == (
        "binance",
        "W",
        "BTC",
    )


def mapping_versions(
    state: ProductUniverseState,
) -> dict[AssetId, frozenset[str]]:
    versions: dict[AssetId, set[str]] = {}
    for mapping in state.identity_mappings:
        if _contradicted_mapping(mapping):
            continue
        asset = AssetId(mapping.canonical_asset_id)
        versions.setdefault(asset, set()).add(mapping.asset_identity_version)
        if any(
            (r.venue, r.venue_asset_code) == (mapping.venue, mapping.venue_asset_code)
            for r in state.resolution_reviews
        ):
            versions[asset].add("identity-review-required")
    return {asset: frozenset(values) for asset, values in versions.items()}


def mapping_by_venue_code(
    state: ProductUniverseState,
) -> dict[tuple[str, str], AssetIdentityMapping]:
    blocked = {(item.venue, item.venue_asset_code) for item in state.resolution_reviews}
    return {
        (mapping.venue, mapping.venue_asset_code): mapping
        for mapping in state.identity_mappings
        if not _contradicted_mapping(mapping)
        and (mapping.venue, mapping.venue_asset_code) not in blocked
    }


def resolved_market(
    market: DirectoryMarket,
    *,
    mappings: dict[tuple[str, str], AssetIdentityMapping],
    versions: dict[AssetId, frozenset[str]],
) -> tuple[AssetIdentityMapping, AssetIdentityMapping] | None:
    base = mappings.get((market.venue, market.venue_base_asset))
    quote = mappings.get((market.venue, market.venue_quote_asset))
    if base is None or quote is None:
        return None
    base_asset = AssetId(base.canonical_asset_id)
    quote_asset = AssetId(quote.canonical_asset_id)
    if base_asset == quote_asset:
        return None
    if len(versions.get(base_asset, frozenset())) != 1:
        return None
    if len(versions.get(quote_asset, frozenset())) != 1:
        return None
    return base, quote
