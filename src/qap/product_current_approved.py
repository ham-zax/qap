"""Current-approved retrospective Product research readiness and launch policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from qap.market import BarInterval
from qap.portfolio import AssetId
from qap.product_current_approved_models import (
    CurrentApprovedReadiness,
    DirectMarketReadiness,
    DirectMarketStatus,
    GenerationBinding,
    ReadinessReason,
    ResearchAssetReadiness,
    ResearchPathReadiness,
)
from qap.product_current_approved_policy import (
    CURRENT_APPROVED_RESEARCH_CLAIM_ID,
    CURRENT_APPROVED_RESEARCH_CLAIM_LABEL,
    current_approved_claim_identity,
    current_approved_scanner_protocol,
    semantic_hash,
)
from qap.product_market_data import ProductMarketData
from qap.product_market_data_models import CurrentMarketDataGeneration
from qap.product_market_data_prepare import (
    ProductMarketDataRequirement,
    market_data_requirements,
    product_dataset_id,
)
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ProductUniverseError,
    ResolvedProductInstrument,
)
from qap.scanner.catalog import (
    ScannerCatalogError,
    catalog_semantic_identity,
    load_scanner_catalog,
)
from qap.scanner.current_scope import CurrentApprovedScanScope
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity
from qap.scanner.run import ScanRunResult
from qap.scanner_entry import run_scan_with_qap

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class CurrentApprovedResearchError(RuntimeError):
    """Raised when Product current-approved research cannot launch safely."""


@dataclass(frozen=True, slots=True)
class _CandidatePath:
    instrument: ResolvedProductInstrument
    earliest_cutoff: datetime
    latest_cutoff: datetime
    generations: tuple[GenerationBinding, ...]

    @property
    def asset_id(self) -> str:
        return self.instrument.instrument.base.key

    @property
    def venue(self) -> str:
        return self.instrument.instrument.venue


def _aligned_cutoff(value: datetime, interval: BarInterval) -> datetime:
    return _EPOCH + ((value - _EPOCH) // interval.duration) * interval.duration


def _generation_matches(
    generation: CurrentMarketDataGeneration,
    instrument: ResolvedProductInstrument,
    interval: BarInterval,
) -> bool:
    source = instrument.instrument
    return (
        generation.venue == source.venue
        and generation.venue_symbol == source.venue_symbol
        and generation.base_asset == source.base.key
        and generation.quote_asset == source.quote.key
        and generation.interval == interval.label
        and generation.provenance_status == "complete"
        and generation.coverage_start is not None
        and generation.coverage_end_exclusive is not None
    )


def _candidate_path(
    instrument: ResolvedProductInstrument,
    requirements: tuple[ProductMarketDataRequirement, ...],
    generations: dict[str, CurrentMarketDataGeneration],
) -> tuple[_CandidatePath | None, tuple[ReadinessReason, ...]]:
    bindings: list[GenerationBinding] = []
    earliest = _EPOCH
    latest = instrument.directory_observed_at
    missing: list[str] = []
    for requirement in requirements:
        dataset_id = product_dataset_id(instrument, requirement.interval)
        generation = generations.get(dataset_id)
        if generation is None or not _generation_matches(
            generation, instrument, requirement.interval
        ):
            missing.append(requirement.interval.label)
            continue
        assert generation.coverage_start is not None
        assert generation.coverage_end_exclusive is not None
        earliest = max(earliest, generation.coverage_start + requirement.lookback)
        latest = min(latest, generation.coverage_end_exclusive)
        bindings.append(
            GenerationBinding(
                dataset_id=dataset_id,
                semantic_fingerprint=generation.semantic_fingerprint,
                interval=requirement.interval.label,
            )
        )
    if missing:
        return None, (
            ReadinessReason(
                code="history_missing",
                detail="Missing valid generation(s): " + ", ".join(sorted(missing)),
                blocking=True,
            ),
        )
    coarsest = max(requirements, key=lambda item: item.interval.duration).interval
    latest = _aligned_cutoff(latest, coarsest)
    if earliest > latest:
        return None, (
            ReadinessReason(
                code="history_insufficient",
                detail="Available history does not cover the required trailing window.",
                blocking=True,
            ),
        )
    return (
        _CandidatePath(
            instrument=instrument,
            earliest_cutoff=earliest,
            latest_cutoff=latest,
            generations=tuple(sorted(bindings, key=lambda item: item.interval)),
        ),
        (),
    )


def _active_paths(
    candidates: tuple[_CandidatePath, ...],
) -> tuple[datetime | None, tuple[_CandidatePath, ...], frozenset[str]]:
    by_venue: dict[str, list[_CandidatePath]] = {}
    for path in candidates:
        by_venue.setdefault(path.venue, []).append(path)
    active: set[str] = {venue for venue, paths in by_venue.items() if len(paths) >= 2}
    while active:
        cutoff = min(path.latest_cutoff for venue in active for path in by_venue[venue])
        next_active: set[str] = {
            venue
            for venue in active
            if sum(path.earliest_cutoff <= cutoff for path in by_venue[venue]) >= 2
        }
        if next_active == active:
            ready = tuple(
                path
                for venue in sorted(active)
                for path in by_venue[venue]
                if path.earliest_cutoff <= cutoff
            )
            return cutoff, ready, frozenset(active)
        active = next_active
    return None, (), frozenset()


def _model_requirements(
    horizon: ScannerHorizon,
) -> tuple[ProductMarketDataRequirement, ...]:
    rule = SCANNER_V1_SLICE1.horizon(horizon)
    lookback = rule.evaluation_window + max(
        duration for _template, duration in rule.template_windows
    )
    return tuple(
        ProductMarketDataRequirement(interval=interval, lookback=lookback)
        for interval in rule.model_resolutions
    )


class CurrentApprovedResearch:
    """Compose M2 scope and M3 generations into Product research readiness."""

    def __init__(
        self, universe: ProductUniverse, market_data: ProductMarketData
    ) -> None:
        self._universe = universe
        self._market_data = market_data

    def _catalog_identity(self) -> str | None:
        root = self._market_data.market_data_root
        if root is None or not (root / "catalog.json").is_file():
            return None
        try:
            return catalog_semantic_identity(load_scanner_catalog(root))
        except ScannerCatalogError as exc:
            raise CurrentApprovedResearchError(
                "Current market-data catalog is invalid."
            ) from exc

    def _direct_markets(
        self,
        *,
        scope: ProductResearchScope | None,
        horizon: ScannerHorizon,
        safe_cutoff: datetime | None,
        ready_paths: tuple[_CandidatePath, ...],
        generations: dict[str, CurrentMarketDataGeneration],
    ) -> tuple[DirectMarketReadiness, ...]:
        if scope is None or safe_cutoff is None:
            return ()
        ready_by_venue: dict[str, set[str]] = {}
        for path in ready_paths:
            ready_by_venue.setdefault(path.venue, set()).add(path.asset_id)
        requirements = _model_requirements(horizon)
        direct_rows: list[DirectMarketReadiness] = []
        for venue, assets in sorted(ready_by_venue.items()):
            for left, right in combinations(sorted(assets), 2):
                matches = tuple(
                    item
                    for item in scope.instruments
                    if item.instrument.venue == venue
                    and item.instrument.quote != AssetId("USDT")
                    and {item.instrument.base.key, item.instrument.quote.key}
                    == {left, right}
                )
                if len(matches) != 1:
                    direct_rows.append(
                        DirectMarketReadiness(
                            venue=venue,
                            asset_a=left,
                            asset_b=right,
                            venue_symbol=None,
                            status="unavailable",
                            reasons=(
                                ReadinessReason(
                                    code="direct_market_unavailable",
                                    detail=(
                                        "No unique real same-venue direct Spot market "
                                        "is available."
                                    ),
                                    blocking=False,
                                ),
                            ),
                            generations=(),
                        )
                    )
                    continue
                direct = matches[0]
                bindings: list[GenerationBinding] = []
                status: DirectMarketStatus = "ready"
                reasons: tuple[ReadinessReason, ...] = ()
                for requirement in requirements:
                    dataset_id = product_dataset_id(direct, requirement.interval)
                    generation = generations.get(dataset_id)
                    if generation is None or not _generation_matches(
                        generation, direct, requirement.interval
                    ):
                        status = "history_missing"
                        reasons = (
                            ReadinessReason(
                                code="history_missing",
                                detail=(
                                    "Direct-market historical generation is missing."
                                ),
                                blocking=False,
                            ),
                        )
                        continue
                    bindings.append(
                        GenerationBinding(
                            dataset_id=dataset_id,
                            semantic_fingerprint=generation.semantic_fingerprint,
                            interval=requirement.interval.label,
                        )
                    )
                    assert generation.coverage_start is not None
                    assert generation.coverage_end_exclusive is not None
                    if (
                        generation.coverage_start > safe_cutoff - requirement.lookback
                        or generation.coverage_end_exclusive < safe_cutoff
                    ):
                        if status == "ready":
                            status = "history_insufficient"
                            reasons = (
                                ReadinessReason(
                                    code="history_insufficient",
                                    detail=(
                                        "Direct-market history does not cover the "
                                        "replay window."
                                    ),
                                    blocking=False,
                                ),
                            )
                direct_rows.append(
                    DirectMarketReadiness(
                        venue=venue,
                        asset_a=left,
                        asset_b=right,
                        venue_symbol=direct.instrument.venue_symbol,
                        status=status,
                        reasons=reasons,
                        generations=tuple(bindings),
                    )
                )
        return tuple(direct_rows)

    def readiness(self, horizon: ScannerHorizon) -> CurrentApprovedReadiness:
        universe_projection = self._universe.projection()
        try:
            scope = self._universe.resolved_scope()
        except ProductUniverseError:
            scope = None
        market_data = self._market_data.projection()
        generations = {item.dataset_id: item for item in market_data.generations}
        catalog_identity = self._catalog_identity()
        requirements = market_data_requirements((horizon,))

        usdt_instruments = (
            ()
            if scope is None
            else tuple(
                item
                for item in scope.instruments
                if item.instrument.quote == AssetId("USDT")
                and item.instrument.base in set(scope.approved_assets)
            )
        )
        counts: dict[tuple[str, str], int] = {}
        for instrument in usdt_instruments:
            key = (instrument.instrument.venue, instrument.instrument.base.key)
            counts[key] = counts.get(key, 0) + 1

        candidate_by_symbol: dict[str, _CandidatePath] = {}
        path_reason_by_symbol: dict[str, tuple[ReadinessReason, ...]] = {}
        for instrument in usdt_instruments:
            symbol = (
                f"{instrument.instrument.venue}:{instrument.instrument.venue_symbol}"
            )
            key = (instrument.instrument.venue, instrument.instrument.base.key)
            if counts[key] != 1:
                path_reason_by_symbol[symbol] = (
                    ReadinessReason(
                        code="current_market_unavailable",
                        detail=(
                            "Current venue path is ambiguous for this economic asset."
                        ),
                        blocking=True,
                    ),
                )
                continue
            candidate, reasons = _candidate_path(instrument, requirements, generations)
            if candidate is None:
                path_reason_by_symbol[symbol] = reasons
            else:
                candidate_by_symbol[symbol] = candidate

        safe_cutoff, ready_candidates, active_venues = _active_paths(
            tuple(candidate_by_symbol.values())
        )
        ready_symbols = {
            f"{path.instrument.instrument.venue}:{path.instrument.instrument.venue_symbol}"
            for path in ready_candidates
        }
        path_rows: dict[str, ResearchPathReadiness] = {}
        for symbol, candidate in candidate_by_symbol.items():
            is_ready = symbol in ready_symbols
            if is_ready:
                reasons: tuple[ReadinessReason, ...] = ()
            elif candidate.venue not in active_venues:
                reasons = (
                    ReadinessReason(
                        code="insufficient_ready_scope",
                        detail="Fewer than two ready approved assets share this venue.",
                        blocking=True,
                    ),
                )
            else:
                reasons = (
                    ReadinessReason(
                        code="history_insufficient",
                        detail="History does not reach the shared backend safe cutoff.",
                        blocking=True,
                    ),
                )
            source = candidate.instrument.instrument
            path_rows[symbol] = ResearchPathReadiness(
                canonical_asset_id=source.base.key,
                venue=source.venue,
                venue_symbol=source.venue_symbol,
                ready=is_ready,
                data_through=candidate.latest_cutoff,
                reasons=reasons,
                generations=candidate.generations,
            )
        for instrument in usdt_instruments:
            symbol = (
                f"{instrument.instrument.venue}:{instrument.instrument.venue_symbol}"
            )
            if symbol in path_rows:
                continue
            source = instrument.instrument
            path_rows[symbol] = ResearchPathReadiness(
                canonical_asset_id=source.base.key,
                venue=source.venue,
                venue_symbol=source.venue_symbol,
                ready=False,
                data_through=None,
                reasons=path_reason_by_symbol[symbol],
                generations=(),
            )

        asset_rows: list[ResearchAssetReadiness] = []
        for asset in universe_projection.assets:
            paths = tuple(
                sorted(
                    (
                        item
                        for item in path_rows.values()
                        if item.canonical_asset_id == asset.asset.key
                    ),
                    key=lambda item: (item.venue, item.venue_symbol),
                )
            )
            reasons: tuple[ReadinessReason, ...] = ()
            ready = any(path.ready for path in paths)
            if not asset.approved:
                reasons = (
                    ReadinessReason(
                        code="not_approved",
                        detail="Asset is outside the operator-approved research scope.",
                        blocking=False,
                    ),
                )
                ready = False
            elif asset.identity_state != "resolved":
                reasons = (
                    ReadinessReason(
                        code="identity_review_required",
                        detail=(
                            "Canonical economic-asset identity requires operator "
                            "review."
                        ),
                        blocking=True,
                    ),
                )
                ready = False
            elif not paths:
                reasons = (
                    ReadinessReason(
                        code="current_market_unavailable",
                        detail=(
                            "No current resolved supported Spot USDT path is available."
                        ),
                        blocking=True,
                    ),
                )
            elif not ready:
                reasons = tuple(reason for path in paths for reason in path.reasons)
            asset_rows.append(
                ResearchAssetReadiness(
                    canonical_asset_id=asset.asset.key,
                    approved=asset.approved,
                    identity_state=asset.identity_state,
                    ready=ready,
                    reasons=reasons,
                    paths=paths,
                )
            )

        direct = self._direct_markets(
            scope=scope,
            horizon=horizon,
            safe_cutoff=safe_cutoff,
            ready_paths=ready_candidates,
            generations=generations,
        )
        top_reasons: list[ReadinessReason] = []
        if market_data.maintenance.status == "running":
            top_reasons.append(
                ReadinessReason(
                    code="refresh_running",
                    detail="Market-data preparation or refresh is currently running.",
                    blocking=True,
                )
            )
        elif market_data.maintenance.status == "failed":
            top_reasons.append(
                ReadinessReason(
                    code="refresh_failed",
                    detail=market_data.maintenance.failure_reason
                    or "Market-data refresh failed.",
                    blocking=False,
                )
            )
        if safe_cutoff is None:
            top_reasons.append(
                ReadinessReason(
                    code="insufficient_ready_scope",
                    detail=(
                        "No supported venue has at least two compatible ready approved "
                        "assets."
                    ),
                    blocking=True,
                )
            )

        ready_venues = tuple(sorted(active_venues))
        protocol = current_approved_scanner_protocol(ready_venues)
        approved_count = sum(asset.approved for asset in universe_projection.assets)
        ready_asset_count = sum(asset.ready for asset in asset_rows)
        binding_payload = {
            "binding_version": "qap.product.current-approved-readiness.v1",
            "claim_identity": current_approved_claim_identity(),
            "horizon": horizon.value,
            "directory_id": universe_projection.directory_id,
            "directory_observed_at": (
                None
                if universe_projection.directory_observed_at is None
                else universe_projection.directory_observed_at.isoformat()
            ),
            "approved_assets": sorted(
                asset.canonical_asset_id for asset in asset_rows if asset.approved
            ),
            "catalog_identity": catalog_identity,
            "safe_cutoff": None if safe_cutoff is None else safe_cutoff.isoformat(),
            "ready_paths": [
                {
                    "asset": path.asset_id,
                    "venue": path.venue,
                    "symbol": path.instrument.instrument.venue_symbol,
                    "source_id": path.instrument.source_id,
                    "source_fingerprint": path.instrument.source_fingerprint,
                    "base_identity_version": (
                        path.instrument.base_asset_identity_version
                    ),
                    "quote_identity_version": (
                        path.instrument.quote_asset_identity_version
                    ),
                    "generations": [
                        (item.dataset_id, item.semantic_fingerprint)
                        for item in path.generations
                    ],
                }
                for path in ready_candidates
            ],
            "maintenance": market_data.maintenance.status,
            "protocol_identity": protocol_identity(protocol),
        }
        readiness_id = semantic_hash(binding_payload)
        ready_for_research = (
            safe_cutoff is not None
            and catalog_identity is not None
            and not any(reason.blocking for reason in top_reasons)
        )
        return CurrentApprovedReadiness(
            claim_id=CURRENT_APPROVED_RESEARCH_CLAIM_ID,
            claim_label=CURRENT_APPROVED_RESEARCH_CLAIM_LABEL,
            claim_identity=current_approved_claim_identity(),
            scanner_protocol_id=protocol.protocol_id,
            scanner_protocol_identity=protocol_identity(protocol),
            horizon=horizon,
            readiness_id=readiness_id,
            directory_id=universe_projection.directory_id,
            directory_observed_at=universe_projection.directory_observed_at,
            catalog_identity=catalog_identity,
            safe_cutoff=safe_cutoff,
            approved_asset_count=approved_count,
            ready_asset_count=ready_asset_count,
            ready_path_count=len(ready_candidates),
            ready_venues=ready_venues,
            assets=tuple(asset_rows),
            direct_markets=direct,
            maintenance=market_data.maintenance,
            reasons=tuple(top_reasons),
            ready_for_research=ready_for_research,
        )

    def require_readiness(
        self,
        horizon: ScannerHorizon,
        readiness_id: str,
    ) -> CurrentApprovedReadiness:
        current = self.readiness(horizon)
        if current.readiness_id != readiness_id:
            raise CurrentApprovedResearchError(
                "Research readiness changed; refresh readiness before launching."
            )
        if not current.ready_for_research:
            raise CurrentApprovedResearchError(
                "Current approved scope is not ready for research."
            )
        return current

    def run(
        self,
        *,
        horizon: ScannerHorizon,
        readiness_id: str,
        data_root: str | Path,
        run_root: str | Path,
        repository_root: str | Path,
    ) -> ScanRunResult:
        """Run Product research at the backend-selected safe cutoff."""

        current = self.require_readiness(horizon, readiness_id)
        if current.safe_cutoff is None or current.catalog_identity is None:
            raise CurrentApprovedResearchError("Research readiness is incomplete.")
        protocol = current_approved_scanner_protocol(current.ready_venues)
        assets_by_venue = tuple(
            (
                venue,
                tuple(
                    sorted(
                        {
                            path.canonical_asset_id
                            for asset in current.assets
                            for path in asset.paths
                            if path.ready and path.venue == venue
                        }
                    )
                ),
            )
            for venue in current.ready_venues
        )
        dataset_ids = tuple(
            sorted(
                {
                    generation.dataset_id
                    for generation in (
                        tuple(
                            generation
                            for asset in current.assets
                            for path in asset.paths
                            if path.ready
                            for generation in path.generations
                        )
                        + tuple(
                            generation
                            for direct in current.direct_markets
                            for generation in direct.generations
                        )
                    )
                }
            )
        )
        scanner_scope = CurrentApprovedScanScope(
            research_claim_identity=current.claim_identity,
            scope_identity=current.readiness_id,
            expected_catalog_identity=current.catalog_identity,
            assets_by_venue=assets_by_venue,
            dataset_ids=dataset_ids,
        )
        return run_scan_with_qap(
            as_of=current.safe_cutoff,
            horizons=(horizon,),
            data_root=data_root,
            run_root=run_root,
            repository_root=repository_root,
            protocol=protocol,
            current_approved_scope=scanner_scope,
        )


__all__ = [
    "CURRENT_APPROVED_RESEARCH_CLAIM_ID",
    "CURRENT_APPROVED_RESEARCH_CLAIM_LABEL",
    "CurrentApprovedReadiness",
    "CurrentApprovedResearch",
    "CurrentApprovedResearchError",
    "DirectMarketReadiness",
    "GenerationBinding",
    "ReadinessReason",
    "ResearchAssetReadiness",
    "ResearchPathReadiness",
    "current_approved_claim_identity",
]
