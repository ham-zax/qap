"""Immutable contracts for Product-owned market-data generations."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.market import ValidatedBarSeries
from qap.product_maintenance import MarketDataMaintenanceState
from qap.product_universe import ResolvedProductInstrument

ProvenanceStatus = Literal["complete", "missing", "invalid"]


def validated_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def validated_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _fingerprint(value: object, *, field: str) -> str:
    normalized = validated_text(value, field=field).lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex string")
    return normalized


def safe_relative_path(value: str) -> str:
    normalized = validated_text(value, field="relative_path")
    if "\\" in normalized:
        raise ValueError("relative_path must be a safe relative POSIX path")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("relative_path must be a safe relative POSIX path")
    return path.as_posix()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class MarketDataUpstreamSource(_FrozenModel):
    provider: str
    source_family: str
    source_id: str
    retrieved_at: datetime
    source_fingerprint: str

    @field_validator("provider", "source_family", "source_id", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: object) -> str:
        return validated_text(value, field=getattr(info, "field_name", "source"))

    @field_validator("retrieved_at")
    @classmethod
    def validate_retrieved_at(cls, value: datetime) -> datetime:
        return validated_utc(value, field="retrieved_at")

    @field_validator("source_fingerprint", mode="before")
    @classmethod
    def validate_source_fingerprint(cls, value: object) -> str:
        return _fingerprint(value, field="source_fingerprint")


class MarketDataParentGeneration(_FrozenModel):
    dataset_id: str
    relative_path: str
    semantic_fingerprint: str

    @field_validator("dataset_id", mode="before")
    @classmethod
    def validate_dataset_id(cls, value: object) -> str:
        return validated_text(value, field="dataset_id")

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return safe_relative_path(value)

    @field_validator("semantic_fingerprint", mode="before")
    @classmethod
    def validate_semantic_fingerprint(cls, value: object) -> str:
        return _fingerprint(value, field="semantic_fingerprint")


class MarketDataDerivation(_FrozenModel):
    derivation_id: str
    parents: tuple[MarketDataParentGeneration, ...]

    @field_validator("derivation_id", mode="before")
    @classmethod
    def validate_derivation_id(cls, value: object) -> str:
        return validated_text(value, field="derivation_id")

    @model_validator(mode="after")
    def validate_parents(self) -> Self:
        if not self.parents:
            raise ValueError(
                "derived market data requires at least one parent generation"
            )
        return self


class MarketDataGenerationProvenance(_FrozenModel):
    schema_version: Literal["qap.product.market-data-generation.v1"] = (
        "qap.product.market-data-generation.v1"
    )
    dataset_id: str
    relative_path: str
    venue: str
    venue_symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    base_asset_identity_version: str
    quote_asset_identity_version: str
    scope_directory_id: str
    scope_directory_observed_at: datetime
    directory_source_id: str
    directory_source_fingerprint: str
    coverage_start: datetime
    coverage_end_exclusive: datetime
    acquisition_implementation: str
    upstream_sources: tuple[MarketDataUpstreamSource, ...]
    derivation: MarketDataDerivation | None = None
    semantic_fingerprint: str
    published_at: datetime

    @field_validator(
        "dataset_id",
        "venue",
        "venue_symbol",
        "base_asset",
        "quote_asset",
        "interval",
        "base_asset_identity_version",
        "quote_asset_identity_version",
        "directory_source_id",
        "acquisition_implementation",
        mode="before",
    )
    @classmethod
    def validate_text(cls, value: object, info: object) -> str:
        return validated_text(value, field=getattr(info, "field_name", "value"))

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return safe_relative_path(value)

    @field_validator(
        "scope_directory_id",
        "directory_source_fingerprint",
        "semantic_fingerprint",
        mode="before",
    )
    @classmethod
    def validate_fingerprint(cls, value: object, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator(
        "scope_directory_observed_at",
        "coverage_start",
        "coverage_end_exclusive",
        "published_at",
    )
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return validated_utc(value, field=getattr(info, "field_name", "timestamp"))

    @model_validator(mode="after")
    def validate_generation(self) -> Self:
        if not self.upstream_sources:
            raise ValueError(
                "generation provenance requires at least one upstream source"
            )
        if self.coverage_start >= self.coverage_end_exclusive:
            raise ValueError("generation coverage must have positive duration")
        return self


@dataclass(frozen=True, slots=True)
class MarketDataGenerationInput:
    dataset_id: str
    resolved_instrument: ResolvedProductInstrument
    series: ValidatedBarSeries
    acquisition_implementation: str
    upstream_sources: tuple[MarketDataUpstreamSource, ...]
    derivation: MarketDataDerivation | None = None


@dataclass(frozen=True, slots=True)
class CurrentMarketDataGeneration:
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
    provenance_status: ProvenanceStatus
    provenance_relative_path: str | None
    issue: str | None


@dataclass(frozen=True, slots=True)
class ProductMarketDataProjection:
    generations: tuple[CurrentMarketDataGeneration, ...]
    maintenance: MarketDataMaintenanceState


__all__ = [
    "CurrentMarketDataGeneration",
    "MarketDataDerivation",
    "MarketDataGenerationInput",
    "MarketDataGenerationProvenance",
    "MarketDataParentGeneration",
    "MarketDataUpstreamSource",
    "ProductMarketDataProjection",
    "ProvenanceStatus",
]
