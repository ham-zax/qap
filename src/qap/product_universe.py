"""Workspace-scoped current market directory, identity mapping, and asset admission."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.market.adapters.gate_public import GatePublicAdapter
from qap.market.directory import CurrentSpotDirectoryObservation
from qap.market.instruments import VenueInstrument
from qap.market.microstructure import public_payload_fingerprint
from qap.portfolio import AssetId

Venue = Literal["binance", "gate"]
IdentityState = Literal["resolved", "review_required"]
IdentityReason = Literal["resolved", "mapping_unavailable", "identity_version_conflict"]
DataState = Literal["not_approved", "needs_data"]


class ProductUniverseError(RuntimeError):
    """Raised when Product universe state cannot be read or changed safely."""


def _utc(value: object, *, field: str) -> datetime:
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


def _fingerprint(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex string")
    return normalized


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class AssetIdentityMapping(_FrozenModel):
    venue: Venue
    venue_asset_code: str
    canonical_asset_id: str
    asset_identity_version: str
    confirmed_at: datetime

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
        return _utc(value, field="confirmed_at")


class ProductUniverseState(_FrozenModel):
    schema_version: Literal["qap.product.research-universe.v1"] = (
        "qap.product.research-universe.v1"
    )
    updated_at: datetime | None = None
    approved_asset_ids: tuple[str, ...] = ()
    identity_mappings: tuple[AssetIdentityMapping, ...] = ()

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _utc(value, field="updated_at")

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


class ProductMarketDirectory(_FrozenModel):
    schema_version: Literal["qap.product.market-directory.v1"] = (
        "qap.product.market-directory.v1"
    )
    sources: tuple[DirectorySource, ...]
    markets: tuple[DirectoryMarket, ...]

    @model_validator(mode="after")
    def validate_directory(self) -> Self:
        source_venues = tuple(source.venue for source in self.sources)
        if set(source_venues) != {"binance", "gate"} or len(source_venues) != 2:
            raise ValueError("directory requires one Binance and one Gate source")
        market_keys = tuple(
            (market.venue, market.venue_symbol) for market in self.markets
        )
        if len(market_keys) != len(set(market_keys)):
            raise ValueError("directory markets must be unique by venue and symbol")
        if any(market.venue not in set(source_venues) for market in self.markets):
            raise ValueError("directory markets must reference an observed venue")
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
                    DirectoryMarket(
                        venue=cast(Venue, market.venue),
                        venue_symbol=market.venue_symbol,
                        venue_base_asset=market.venue_base_asset,
                        venue_quote_asset=market.venue_quote_asset,
                        status=market.status,
                        trading=market.trading,
                    )
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
        payload = self.model_dump(mode="json")
        return public_payload_fingerprint(payload)


@dataclass(frozen=True, slots=True)
class ResearchUniverseVenue:
    venue: str
    venue_symbol: str
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


def _mapping_versions(
    state: ProductUniverseState,
) -> dict[AssetId, frozenset[str]]:
    versions: dict[AssetId, set[str]] = {}
    for mapping in state.identity_mappings:
        asset = AssetId(mapping.canonical_asset_id)
        versions.setdefault(asset, set()).add(mapping.asset_identity_version)
    return {asset: frozenset(values) for asset, values in versions.items()}


def _mapping_by_venue_code(
    state: ProductUniverseState,
) -> dict[tuple[str, str], AssetIdentityMapping]:
    return {
        (mapping.venue, mapping.venue_asset_code): mapping
        for mapping in state.identity_mappings
    }


def _resolved_market(
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


class ProductUniverse:
    """Single workspace owner for current directory, mappings, and admission."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.root = self.workspace_root / "product"
        self.state_path = self.root / "research-universe.json"
        self.directory_path = self.root / "market-directory.json"
        self._lock = Lock()

    @staticmethod
    def _write_model(path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
        payload = (model.model_dump_json(indent=2) + "\n").encode("utf-8")
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def read_state(self) -> ProductUniverseState:
        if not self.state_path.is_file():
            return ProductUniverseState()
        try:
            return ProductUniverseState.model_validate_json(
                self.state_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            raise ProductUniverseError("Research Universe state is invalid.") from exc

    def read_directory(self) -> ProductMarketDirectory | None:
        if not self.directory_path.is_file():
            return None
        try:
            return ProductMarketDirectory.model_validate_json(
                self.directory_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            raise ProductUniverseError(
                "Current market directory state is invalid."
            ) from exc

    def refresh_directory(self) -> ProductMarketDirectory:
        """Refresh both supported public venues, publishing only a complete result."""

        with BinancePublicAdapter() as binance:
            binance_observation = binance.fetch_spot_directory()
        with GatePublicAdapter() as gate:
            gate_observation = gate.fetch_spot_directory()
        directory = ProductMarketDirectory.from_observations(
            (binance_observation, gate_observation)
        )
        with self._lock:
            self._write_model(self.directory_path, directory)
        return directory

    def set_identity_mapping(
        self,
        *,
        venue: Venue,
        venue_asset_code: str,
        canonical_asset_id: str,
        asset_identity_version: str,
        confirmed_at: datetime | None = None,
    ) -> ProductUniverseState:
        """Persist one explicit operator-confirmed venue-code identity mapping."""

        timestamp = datetime.now(UTC) if confirmed_at is None else confirmed_at
        mapping = AssetIdentityMapping(
            venue=venue,
            venue_asset_code=venue_asset_code,
            canonical_asset_id=canonical_asset_id,
            asset_identity_version=asset_identity_version,
            confirmed_at=timestamp,
        )
        directory = self.read_directory()
        if directory is None or not any(
            market.venue == mapping.venue
            and mapping.venue_asset_code
            in {market.venue_base_asset, market.venue_quote_asset}
            for market in directory.markets
        ):
            raise ProductUniverseError(
                "Identity mapping requires a currently observed venue asset code."
            )

        with self._lock:
            state = self.read_state()
            retained = tuple(
                item
                for item in state.identity_mappings
                if (item.venue, item.venue_asset_code)
                != (mapping.venue, mapping.venue_asset_code)
            )
            next_state = ProductUniverseState(
                updated_at=timestamp,
                approved_asset_ids=state.approved_asset_ids,
                identity_mappings=tuple(
                    sorted(
                        (*retained, mapping),
                        key=lambda item: (item.venue, item.venue_asset_code),
                    )
                ),
            )
            self._write_model(self.state_path, next_state)
            return next_state

    def set_asset_admission(
        self,
        *,
        canonical_asset_id: str,
        approved: bool,
        updated_at: datetime | None = None,
    ) -> ProductUniverseState:
        """Approve/unapprove one known canonical asset without touching listings."""

        asset = AssetId(canonical_asset_id)
        timestamp = (
            datetime.now(UTC)
            if updated_at is None
            else _utc(updated_at, field="updated_at")
        )
        with self._lock:
            state = self.read_state()
            known_assets = {
                AssetId(mapping.canonical_asset_id)
                for mapping in state.identity_mappings
            }
            if asset not in known_assets and asset not in {
                AssetId(value) for value in state.approved_asset_ids
            }:
                raise ProductUniverseError(
                    "Asset admission requires an explicit canonical identity mapping."
                )
            approved_assets = {AssetId(value) for value in state.approved_asset_ids}
            if approved:
                approved_assets.add(asset)
            else:
                approved_assets.discard(asset)
            next_state = ProductUniverseState(
                updated_at=timestamp,
                approved_asset_ids=tuple(item.key for item in sorted(approved_assets)),
                identity_mappings=state.identity_mappings,
            )
            self._write_model(self.state_path, next_state)
            return next_state

    def projection(self) -> ResearchUniverseProjection:
        """Project current Product truth without claiming research readiness."""

        state = self.read_state()
        directory = self.read_directory()
        mappings = _mapping_by_venue_code(state)
        versions = _mapping_versions(state)
        approved = {AssetId(value) for value in state.approved_asset_ids}
        directory_markets = () if directory is None else directory.markets
        candidate_assets = {
            AssetId(mapping.canonical_asset_id)
            for market in directory_markets
            if market.venue_quote_asset == "USDT"
            for mapping in (mappings.get((market.venue, market.venue_base_asset)),)
            if mapping is not None
        }
        known_assets = candidate_assets | approved

        venue_rows: dict[AssetId, list[ResearchUniverseVenue]] = {}
        for market in directory_markets:
            resolved = _resolved_market(
                market,
                mappings=mappings,
                versions=versions,
            )
            if resolved is None:
                continue
            base_mapping, quote_mapping = resolved
            if AssetId(quote_mapping.canonical_asset_id) != AssetId("USDT"):
                continue
            asset = AssetId(base_mapping.canonical_asset_id)
            venue_rows.setdefault(asset, []).append(
                ResearchUniverseVenue(
                    venue=market.venue,
                    venue_symbol=market.venue_symbol,
                    status=market.status,
                    trading=market.trading,
                )
            )

        assets: list[ResearchUniverseAsset] = []
        for asset in sorted(known_assets):
            asset_versions = versions.get(asset, frozenset())
            if len(asset_versions) == 1:
                identity_state: IdentityState = "resolved"
                identity_reason: IdentityReason = "resolved"
                identity_version = next(iter(asset_versions))
            elif not asset_versions:
                identity_state = "review_required"
                identity_reason = "mapping_unavailable"
                identity_version = None
            else:
                identity_state = "review_required"
                identity_reason = "identity_version_conflict"
                identity_version = None
            approved_state = asset in approved
            data_state: DataState = "needs_data" if approved_state else "not_approved"
            assets.append(
                ResearchUniverseAsset(
                    asset=asset,
                    approved=approved_state,
                    identity_state=identity_state,
                    identity_reason=identity_reason,
                    asset_identity_version=identity_version,
                    data_state=data_state,
                    venues=tuple(
                        sorted(
                            venue_rows.get(asset, ()),
                            key=lambda item: (item.venue, item.venue_symbol),
                        )
                    ),
                )
            )

        unresolved: dict[tuple[str, str], set[str]] = {}
        for market in directory_markets:
            if market.venue_quote_asset != "USDT":
                continue
            for venue_asset_code in (
                market.venue_base_asset,
                market.venue_quote_asset,
            ):
                key = (market.venue, venue_asset_code)
                if key in mappings:
                    continue
                unresolved.setdefault(key, set()).add(market.venue_symbol)
        identity_reviews = tuple(
            IdentityReview(
                venue=venue,
                venue_asset_code=venue_asset_code,
                venue_symbols=tuple(sorted(symbols)),
            )
            for (venue, venue_asset_code), symbols in sorted(unresolved.items())
        )

        return ResearchUniverseProjection(
            directory_id=None if directory is None else directory.directory_id,
            directory_observed_at=None if directory is None else directory.observed_at,
            sources=() if directory is None else directory.sources,
            assets=tuple(assets),
            identity_reviews=identity_reviews,
        )

    def resolved_scope(
        self,
        *,
        asset_ids: tuple[AssetId, ...] | None = None,
        analysis_reference_ids: tuple[AssetId, ...] = (),
    ) -> ProductResearchScope:
        """Return the approved/current scope, optionally bounded to selected assets."""

        state = self.read_state()
        directory = self.read_directory()
        if directory is None:
            raise ProductUniverseError(
                "Current market directory has not been refreshed."
            )
        mappings = _mapping_by_venue_code(state)
        versions = _mapping_versions(state)
        approved = {AssetId(value) for value in state.approved_asset_ids}
        selected = None if asset_ids is None else frozenset(asset_ids)
        references = frozenset(analysis_reference_ids)
        if selected is None and references:
            raise ProductUniverseError("Analysis references require selected assets.")
        if selected is not None:
            assert asset_ids is not None
            if not selected or len(selected) != len(asset_ids):
                raise ProductUniverseError("Selected assets must be unique.")
            if not selected <= approved:
                raise ProductUniverseError("Selected Product assets are not approved.")
            if any(len(versions.get(a, ())) != 1 for a in selected | references):
                raise ProductUniverseError("Selected/reference identity is unresolved.")
        sources = {source.venue: source for source in directory.sources}
        instruments: list[ResolvedProductInstrument] = []
        for market in directory.markets:
            if not market.trading:
                continue
            resolved = _resolved_market(
                market,
                mappings=mappings,
                versions=versions,
            )
            if resolved is None:
                continue
            base_mapping, quote_mapping = resolved
            base_asset = AssetId(base_mapping.canonical_asset_id)
            quote_asset = AssetId(quote_mapping.canonical_asset_id)
            economic = approved if selected is None else selected
            is_usdt = quote_asset.key == "USDT"
            include = base_asset in economic and (is_usdt or quote_asset in economic)
            include |= selected is not None and base_asset in references and is_usdt
            if not include:
                continue
            source = sources[market.venue]
            instruments.append(
                ResolvedProductInstrument(
                    instrument=VenueInstrument(
                        venue=market.venue,
                        venue_symbol=market.venue_symbol,
                        base=base_asset,
                        quote=quote_asset,
                    ),
                    base_asset_identity_version=base_mapping.asset_identity_version,
                    quote_asset_identity_version=quote_mapping.asset_identity_version,
                    directory_observed_at=source.observed_at,
                    source_id=source.source_id,
                    source_fingerprint=source.source_fingerprint,
                )
            )
        return ProductResearchScope(
            directory_id=directory.directory_id,
            directory_observed_at=directory.observed_at,
            approved_assets=tuple(sorted(approved)),
            instruments=tuple(
                sorted(
                    instruments,
                    key=lambda item: (
                        item.instrument.venue,
                        item.instrument.venue_symbol,
                    ),
                )
            ),
        )


__all__ = [
    "AssetIdentityMapping",
    "DataState",
    "DirectorySource",
    "IdentityReason",
    "IdentityReview",
    "IdentityState",
    "ProductMarketDirectory",
    "ProductResearchScope",
    "ProductUniverse",
    "ProductUniverseError",
    "ResearchUniverseAsset",
    "ResearchUniverseProjection",
    "ResearchUniverseVenue",
    "ResolvedProductInstrument",
    "Venue",
]
