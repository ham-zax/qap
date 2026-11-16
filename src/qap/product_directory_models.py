"""Persistent current-directory schemas, independent of identity and admission."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    PrivateAttr,
    field_validator,
    model_validator,
)

from qap.market.directory import CurrentSpotDirectoryObservation, SpotCurrencyEvidence
from qap.market.microstructure import public_payload_fingerprint

Venue = Literal["binance", "gate"]


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _fingerprint(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(c not in "0123456789abcdef" for c in normalized):
        raise ValueError(f"{field} must be a SHA-256 hex string")
    return normalized


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class DirectorySource(_FrozenModel):
    venue: Venue
    observed_at: datetime
    source_id: str
    source_fingerprint: str

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        return _utc(value, field="observed_at")

    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, value: object) -> str:
        return _text(value, field="source_id")

    @field_validator("source_fingerprint", mode="before")
    @classmethod
    def validate_source_fingerprint(cls, value: object) -> str:
        return _fingerprint(value, field="source_fingerprint")


class DirectoryMarket(_FrozenModel):
    venue: Venue
    venue_symbol: str
    venue_base_asset: str
    venue_quote_asset: str
    status: str
    trading: bool
    base_name: str | None = None
    quote_name: str | None = None
    buy_start: datetime | None = None
    pair_type: str | None = None
    spot_trading_allowed: bool | None = None
    permissions: tuple[str, ...] = ()
    permission_sets: tuple[tuple[str, ...], ...] = ()
    base_currency: SpotCurrencyEvidence | None = None
    quote_currency: SpotCurrencyEvidence | None = None

    @field_validator("buy_start")
    @classmethod
    def validate_buy_start(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _utc(value, field="buy_start")

    @model_validator(mode="after")
    def validate_currencies(self) -> Self:
        if self.venue_base_asset == self.venue_quote_asset:
            raise ValueError("venue base and quote assets must be distinct")
        for code, currency in (
            (self.venue_base_asset, self.base_currency),
            (self.venue_quote_asset, self.quote_currency),
        ):
            if currency is not None and currency.venue_asset_code != code:
                raise ValueError("currency evidence must match venue asset code")
        return self

    @field_validator(
        "venue_symbol",
        "venue_base_asset",
        "venue_quote_asset",
        mode="before",
    )
    @classmethod
    def normalize_venue_code(cls, value: object) -> str:
        return _text(value, field="venue market value").upper()

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> str:
        return _text(value, field="status")


class DirectoryRefreshResult(_FrozenModel):
    venue: Venue
    attempted_at: datetime
    status: Literal["refreshed", "stale", "unavailable"]
    error: str | None = None

    @field_validator("attempted_at")
    @classmethod
    def validate_attempted_at(cls, value: datetime) -> datetime:
        return _utc(value, field="attempted_at")

    @model_validator(mode="after")
    def validate_error(self) -> Self:
        if (self.status == "refreshed") != (self.error is None):
            raise ValueError("only failed refreshes must have an error")
        return self


class ProductMarketDirectory(_FrozenModel):
    schema_version: Literal[
        "qap.product.market-directory.v1", "qap.product.market-directory.v2"
    ] = "qap.product.market-directory.v2"
    sources: tuple[DirectorySource, ...]
    markets: tuple[DirectoryMarket, ...]
    refresh_results: tuple[DirectoryRefreshResult, ...] = ()
    _directory_id_cache: tuple[tuple[object, ...], str] | None = PrivateAttr(
        default=None
    )

    @model_validator(mode="after")
    def validate_directory(self) -> Self:
        source_venues = tuple(source.venue for source in self.sources)
        if not source_venues or len(source_venues) != len(set(source_venues)):
            raise ValueError("directory requires unique observed venues")
        if self.schema_version.endswith(".v1") and set(source_venues) != {
            "binance",
            "gate",
        }:
            raise ValueError("v1 directory requires one Binance and one Gate source")
        market_keys = tuple(
            (market.venue, market.venue_symbol) for market in self.markets
        )
        if len(market_keys) != len(set(market_keys)):
            raise ValueError("directory markets must be unique by venue and symbol")
        if any(market.venue not in set(source_venues) for market in self.markets):
            raise ValueError("directory markets must reference an observed venue")
        refresh_venues = tuple(result.venue for result in self.refresh_results)
        if len(refresh_venues) != len(set(refresh_venues)):
            raise ValueError("directory refresh results must be unique by venue")
        for result in self.refresh_results:
            if (result.status == "unavailable") == (result.venue in source_venues):
                raise ValueError("refresh status must match available venue sources")
        return self

    @classmethod
    def from_observations(
        cls,
        observations: tuple[CurrentSpotDirectoryObservation, ...],
    ) -> Self:
        sources = tuple(
            sorted(
                (
                    DirectorySource(
                        venue=cast(Venue, observation.venue),
                        observed_at=observation.observed_at,
                        source_id=observation.source_id,
                        source_fingerprint=observation.source_fingerprint,
                    )
                    for observation in observations
                ),
                key=lambda source: source.venue,
            )
        )
        markets = tuple(
            sorted(
                (
                    DirectoryMarket.model_validate(asdict(market))
                    for observation in observations
                    for market in observation.markets
                ),
                key=lambda market: (market.venue, market.venue_symbol),
            )
        )
        return cls(sources=sources, markets=markets)

    @property
    def observed_at(self) -> datetime:
        return max(source.observed_at for source in self.sources)

    @property
    def directory_id(self) -> str:
        state = (
            self.schema_version,
            self.sources,
            self.markets,
            () if self.schema_version.endswith(".v1") else self.refresh_results,
        )
        cached = self._directory_id_cache
        if (
            cached is not None
            and cached[0][0] == state[0]
            and cached[0][1] is state[1]
            and cached[0][2] is state[2]
            and cached[0][3] is state[3]
        ):
            return cached[1]
        payload = self.model_dump(mode="json")
        if self.schema_version.endswith(".v1"):
            # Defaulted v2 fields must not change historical v1 lineage hashes.
            payload = {
                "schema_version": self.schema_version,
                "sources": [source.model_dump(mode="json") for source in self.sources],
                "markets": [
                    market.model_dump(
                        mode="json",
                        include={
                            "venue",
                            "venue_symbol",
                            "venue_base_asset",
                            "venue_quote_asset",
                            "status",
                            "trading",
                        },
                    )
                    for market in self.markets
                ],
            }
        digest = public_payload_fingerprint(payload)
        self._directory_id_cache = (state, digest)
        return digest
