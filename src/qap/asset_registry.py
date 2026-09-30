"""Replaceable, read-only registry evidence contracts; no accepted asset state."""

from datetime import datetime
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import Venue

RefreshFailure = Literal[
    "rate_limited",
    "http_error",
    "timeout",
    "network_error",
    "malformed_response",
    "budget_exhausted",
]


def _aware_utc(value: datetime) -> datetime:
    offset = value.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("registry timestamps must be timezone-aware UTC")
    return value


class RegistryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RegistryCoin(RegistryModel):
    coin_id: str = Field(min_length=1)
    symbol: str
    name: str = Field(min_length=1)
    platforms: tuple[tuple[str, str], ...] = ()
    # Registry-supplied classes; empty for sources that do not provide any.
    categories: tuple[str, ...] = ()
    # Explicit, provenance-backed relationship; name similarity is insufficient.
    representation_of: str | None = None

    @property
    def identity_version(self) -> str:
        return "registry-v1-" + public_payload_fingerprint(
            {"coin_id": self.coin_id, "platforms": sorted(self.platforms)}
        )


class RegistryTicker(RegistryModel):
    venue: Venue
    base: str
    target: str
    coin_id: str
    stale: bool = False
    anomalous: bool = False


class RegistrySource(RegistryModel):
    """One recorded request: what was asked, when, and what came back."""

    url: str
    request_fingerprint: str
    payload_fingerprint: str
    retrieved_at: datetime

    @field_validator("retrieved_at")
    @classmethod
    def validate_retrieved_at(cls, value: datetime) -> datetime:
        return _aware_utc(value)


class RegistrySnapshot(RegistryModel):
    schema_version: Literal["qap.asset-registry.v1"] = "qap.asset-registry.v1"
    registry: str = "coingecko"
    observed_at: datetime
    coins: tuple[RegistryCoin, ...]
    tickers: tuple[RegistryTicker, ...] = ()
    sources: tuple[RegistrySource, ...] = ()
    attribution: str = "Data provided by CoinGecko (https://www.coingecko.com/)"

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        ids = [coin.coin_id for coin in self.coins]
        if len(ids) != len(set(ids)):
            raise ValueError("registry coin IDs must be unique")
        known = set(ids)
        if any(ticker.coin_id not in known for ticker in self.tickers):
            raise ValueError("ticker references an unknown registry coin")
        return self

    @property
    def fingerprint(self) -> str:
        return public_payload_fingerprint(self.model_dump(mode="json"))


class RegistryRefreshResult(RegistryModel):
    """Outage never raises: a failed refresh names its cause and the stale source."""

    status: Literal["refreshed", "cached", "stale", "unavailable"]
    snapshot: RegistrySnapshot | None = None
    failure: RefreshFailure | None = None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if (self.status in {"stale", "unavailable"}) != (self.failure is not None):
            raise ValueError("only stale or unavailable results carry a failure")
        if (self.status == "unavailable") != (self.snapshot is None):
            raise ValueError("only unavailable results lack a snapshot")
        return self


class AssetRegistry(Protocol):
    def snapshot(self) -> RegistrySnapshot | None:
        """Read the last good evidence without network access."""
        ...

    def refresh(self, *, force: bool = False) -> RegistryRefreshResult:
        """Attempt bounded acquisition, retaining last good evidence on failure."""
        ...
