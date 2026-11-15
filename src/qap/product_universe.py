"""Workspace-scoped current market directory, identity mapping, and asset admission."""

from __future__ import annotations

import fcntl
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import cast

from pydantic import (
    BaseModel,
    ValidationError,
)

from qap.asset_registry import RegistryRefreshResult, RegistrySnapshot
from qap.asset_registry_coingecko import CoinGeckoRegistry, RegistryCacheError
from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.market.adapters.gate_public import GatePublicAdapter, GatePublicDataError
from qap.market.instruments import VenueInstrument
from qap.portfolio import AssetId
from qap.product_coin_search import ResearchCoin, coins, search_coins
from qap.product_directory_models import (
    DirectoryMarket as DirectoryMarket,
)
from qap.product_directory_models import (
    DirectoryRefreshResult,
    DirectorySource,
    ProductMarketDirectory,
)
from qap.product_identity_policy import accept_evidence
from qap.product_universe_cache import SHARED_UNIVERSE_CACHE, VersionedFileCache
from qap.product_universe_models import (
    AssetIdentityMapping as AssetIdentityMapping,
)
from qap.product_universe_models import (
    DataState as DataState,
)
from qap.product_universe_models import (
    IdentityReason as IdentityReason,
)
from qap.product_universe_models import (
    IdentityReview as IdentityReview,
)
from qap.product_universe_models import (
    IdentityState as IdentityState,
)
from qap.product_universe_models import (
    ProductDirectoryRefreshError as ProductDirectoryRefreshError,
)
from qap.product_universe_models import (
    ProductResearchScope as ProductResearchScope,
)
from qap.product_universe_models import (
    ProductUniverseError as ProductUniverseError,
)
from qap.product_universe_models import (
    ProductUniverseState as ProductUniverseState,
)
from qap.product_universe_models import (
    ResearchUniverseAsset as ResearchUniverseAsset,
)
from qap.product_universe_models import (
    ResearchUniverseProjection as ResearchUniverseProjection,
)
from qap.product_universe_models import (
    ResearchUniverseVenue as ResearchUniverseVenue,
)
from qap.product_universe_models import (
    ResolvedProductInstrument as ResolvedProductInstrument,
)
from qap.product_universe_models import (
    Venue as Venue,
)
from qap.product_universe_models import (
    mapping_by_venue_code,
    mapping_versions,
    resolved_market,
    universe_utc,
)


class ProductUniverse:
    """Single workspace owner for current directory, mappings, and admission."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.root = self.workspace_root / "product"
        self.state_path = self.root / "research-universe.json"
        self.directory_path = self.root / "market-directory.json"
        self._thread_lock = Lock()
        self._cache: VersionedFileCache = SHARED_UNIVERSE_CACHE

    @contextmanager
    def _state_guard(self) -> Generator[None]:
        # API and worker processes share one state; serialize read/modify/write.
        with self._thread_lock:
            self.root.mkdir(parents=True, exist_ok=True)
            with (self.root / "universe.lock").open("a+b") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle, fcntl.LOCK_UN)

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
            return self._cache.get(
                self.state_path, ProductUniverseState.model_validate_json
            )
        except (OSError, ValidationError) as exc:
            raise ProductUniverseError("Research Universe state is invalid.") from exc

    def read_directory(self) -> ProductMarketDirectory | None:
        if not self.directory_path.is_file():
            return None
        try:
            return self._cache.get(
                self.directory_path, ProductMarketDirectory.model_validate_json
            )
        except (OSError, ValidationError) as exc:
            raise ProductUniverseError(
                "Current market directory state is invalid."
            ) from exc

    def registry_snapshot(self) -> RegistrySnapshot | None:
        reg_path = self.root / "asset-registry.json"
        if not reg_path.is_file():
            return None
        try:
            return self._cache.get_via(
                reg_path, lambda p: CoinGeckoRegistry(p).snapshot()
            )
        except OSError, RegistryCacheError:
            return None

    def refresh_identity_evidence(self) -> RegistryRefreshResult:
        reg_path = self.root / "asset-registry.json"
        result = CoinGeckoRegistry(reg_path).refresh()
        self._cache.drop(reg_path)
        self.apply_policy_bindings(result.snapshot)
        return result

    def apply_policy_bindings(
        self,
        snapshot: RegistrySnapshot | None = None,
    ) -> ProductUniverseState:
        with self._state_guard():
            state = self.read_state()
            directory = self.read_directory()
            if directory is None:
                return state
            evidence = self.registry_snapshot() if snapshot is None else snapshot
            next_state = accept_evidence(
                state, directory, evidence, now=datetime.now(UTC)
            )
            if next_state != state:
                self._write_model(self.state_path, next_state)
                self._cache.drop(self.state_path)
            return next_state

    def search(
        self,
        query: str = "",
        *,
        limit: int = 50,
        venue: Venue | None = None,
    ) -> tuple[ResearchCoin, ...]:
        """Search atomic cached snapshots without waiting on refresh writers."""
        if not 1 <= limit <= 1000:
            raise ProductUniverseError("Search limit must be between 1 and 1000.")
        rows = coins(self.read_directory(), self.registry_snapshot(), self.read_state())
        return search_coins(rows, query, limit, venue=venue)

    def research_scope(
        self, listing_ids: tuple[str, str], *, refresh_bindings: bool = True
    ) -> ProductResearchScope:
        """Eligible venue-local research needs no portfolio admission (approved Q9)."""
        if refresh_bindings:
            self.apply_policy_bindings()
        directory = self.read_directory()
        if directory is None:
            raise ProductUniverseError(
                "Current market directory has not been refreshed."
            )
        state = self.read_state()
        rows = coins(directory, self.registry_snapshot(), state)
        selected = tuple(
            next((row for row in rows if row.listing_id == key), None)
            for key in listing_ids
        )
        if listing_ids[0] == listing_ids[1] or any(row is None for row in selected):
            raise ProductUniverseError("Choose two distinct eligible spot listings.")
        instruments: list[ResolvedProductInstrument] = []
        venues: set[str] = set()
        for row in selected:
            assert row is not None
            if not row.trading:
                raise ProductUniverseError("Selected listing is not currently trading.")
            venues.add(row.venue)
            source = next(
                source for source in directory.sources if source.venue == row.venue
            )
            # Unresolved listings use an explicit local coordinate, never a
            # guessed cross-venue economic identity. Their call remains blocked.
            asset = AssetId(
                row.canonical_asset_id or f"VENUE:{row.venue}:{row.venue_asset_code}"
            )
            instruments.append(
                ResolvedProductInstrument(
                    instrument=VenueInstrument(
                        venue=row.venue,
                        venue_symbol=row.venue_symbol,
                        base=asset,
                        quote=AssetId("USDT"),
                    ),
                    base_asset_identity_version=row.identity_version,
                    quote_asset_identity_version="usdt-policy-v1",
                    directory_observed_at=source.observed_at,
                    source_id=source.source_id,
                    source_fingerprint=source.source_fingerprint,
                )
            )
        if len(venues) != 1:
            raise ProductUniverseError("The two coins must have a common venue.")
        if instruments[0].instrument.base == instruments[1].instrument.base:
            raise ProductUniverseError("The two listings represent the same asset.")
        return ProductResearchScope(
            directory_id=directory.directory_id,
            directory_observed_at=directory.observed_at,
            approved_assets=tuple(AssetId(key) for key in state.approved_asset_ids),
            instruments=tuple(instruments),
            economic_identity_confirmed=all(
                row is not None and row.call_available for row in selected
            ),
        )

    def refresh_directory(self) -> ProductMarketDirectory:
        """Publish each venue immediately; keep exact last-good evidence on outage."""

        with self._state_guard():
            # Validate before acquisition so corrupt persisted truth is never replaced.
            directory = self.read_directory()
            sources = (
                {} if directory is None else {s.venue: s for s in directory.sources}
            )
            markets = () if directory is None else directory.markets
            results = (
                {}
                if directory is None
                else {result.venue: result for result in directory.refresh_results}
            )
            for venue, adapter_type in (
                ("binance", BinancePublicAdapter),
                ("gate", GatePublicAdapter),
            ):
                venue = cast(Venue, venue)
                attempted_at = datetime.now(UTC)
                try:
                    with adapter_type() as adapter:
                        observation = adapter.fetch_spot_directory()
                    current = ProductMarketDirectory.from_observations((observation,))
                    sources[venue] = current.sources[0]
                    markets = (
                        tuple(m for m in markets if m.venue != venue) + current.markets
                    )
                    result = DirectoryRefreshResult(
                        venue=venue, attempted_at=attempted_at, status="refreshed"
                    )
                except (BinancePublicDataError, GatePublicDataError) as exc:
                    result = DirectoryRefreshResult(
                        venue=venue,
                        attempted_at=attempted_at,
                        status="stale" if venue in sources else "unavailable",
                        error=str(exc),
                    )
                results[venue] = result
                if sources:
                    directory = ProductMarketDirectory(
                        sources=tuple(sorted(sources.values(), key=lambda s: s.venue)),
                        markets=tuple(
                            sorted(markets, key=lambda m: (m.venue, m.venue_symbol))
                        ),
                        refresh_results=tuple(
                            sorted(results.values(), key=lambda r: r.venue)
                        ),
                    )
                    self._write_model(self.directory_path, directory)
                    self._cache.drop(self.directory_path)
            if directory is None:
                raise ProductDirectoryRefreshError(
                    "Current public Spot markets could not be refreshed: "
                    + "; ".join(f"{r.venue}: {r.error}" for r in results.values())
                )
        self.apply_policy_bindings()
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
        if (mapping.venue, mapping.venue_asset_code, mapping.canonical_asset_id) == (
            "binance",
            "W",
            "BTC",
        ):
            raise ProductUniverseError("Wormhole cannot be bound to Bitcoin.")
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

        with self._state_guard():
            state = self.read_state()
            retained = tuple(
                item
                for item in state.identity_mappings
                if (item.venue, item.venue_asset_code)
                != (mapping.venue, mapping.venue_asset_code)
            )
            next_state = state.model_copy(
                update={
                    "schema_version": "qap.product.research-universe.v2",
                    "updated_at": timestamp,
                    "identity_mappings": tuple(
                        sorted(
                            (*retained, mapping),
                            key=lambda item: (item.venue, item.venue_asset_code),
                        )
                    ),
                    "resolution_reviews": tuple(
                        item
                        for item in state.resolution_reviews
                        if (item.venue, item.venue_asset_code)
                        != (mapping.venue, mapping.venue_asset_code)
                    ),
                }
            )
            self._write_model(self.state_path, next_state)
            self._cache.drop(self.state_path)
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
            else universe_utc(updated_at, field="updated_at")
        )
        with self._state_guard():
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
            next_state = state.model_copy(
                update={
                    "schema_version": "qap.product.research-universe.v2",
                    "updated_at": timestamp,
                    "approved_asset_ids": tuple(
                        item.key for item in sorted(approved_assets)
                    ),
                    "pending_admission_asset_ids": tuple(
                        key
                        for key in state.pending_admission_asset_ids
                        if key != asset.key or not approved
                    ),
                }
            )
            self._write_model(self.state_path, next_state)
            self._cache.drop(self.state_path)
            return next_state

    def projection(self) -> ResearchUniverseProjection:
        """Project current Product truth without claiming research readiness."""

        state = self.read_state()
        directory = self.read_directory()
        mappings = mapping_by_venue_code(state)
        versions = mapping_versions(state)
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
            resolved = resolved_market(
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
                    venue_asset_code=market.venue_base_asset,
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
            directory_refreshes=() if directory is None else directory.refresh_results,
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
        mappings = mapping_by_venue_code(state)
        versions = mapping_versions(state)
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
            resolved = resolved_market(
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
    "ProductDirectoryRefreshError",
    "ProductResearchScope",
    "ProductUniverse",
    "ProductUniverseError",
    "ResearchUniverseAsset",
    "ResearchUniverseProjection",
    "ResearchUniverseVenue",
    "ResolvedProductInstrument",
    "Venue",
]
