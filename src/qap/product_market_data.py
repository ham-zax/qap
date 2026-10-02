"""Product-owned immutable market-data generations and provenance."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from threading import Lock

from pydantic import BaseModel, ValidationError

from qap.market import (
    MarketDataStorageError,
    fingerprint_bar_series,
    read_parquet_bar_series,
    write_parquet_bar_series,
)
from qap.product_identity_retirement import (
    IdentityRetirementPlan,
    contained_file,
    preview_retirement,
)
from qap.product_maintenance import (
    MaintenanceKind,
    MarketDataMaintenanceState,
    MarketDataMaintenanceStore,
    ProductMaintenanceError,
)
from qap.product_market_data_generation import (
    generation_relative_path as _generation_relative_path,
)
from qap.product_market_data_generation import (
    provenance_relative_path as _provenance_relative_path,
)
from qap.product_market_data_models import (
    CurrentMarketDataGeneration,
    MarketDataDerivation,
    MarketDataGenerationInput,
    MarketDataGenerationProvenance,
    MarketDataParentGeneration,
    MarketDataUpstreamSource,
    ProductMarketDataProjection,
    ProvenanceStatus,
    validated_text,
    validated_utc,
)
from qap.product_universe import ProductResearchScope
from qap.scanner.catalog import (
    ScannerCatalog,
    ScannerCatalogError,
    ScannerSourceSpec,
    load_scanner_catalog,
    resolve_catalog_source,
)

_LIFECYCLE_PATH = PurePosixPath("product-market-data/lifecycle.jsonl")


class ProductMarketDataError(RuntimeError):
    """Raised when Product market-data state cannot be published or read safely."""


class ProductMarketData:
    """Workspace owner for Product market-data generations and maintenance state."""

    def __init__(self, workspace_root: Path, market_data_root: Path | None) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.market_data_root = (
            None
            if market_data_root is None
            else market_data_root.expanduser().resolve()
        )
        self._maintenance = MarketDataMaintenanceStore(self.workspace_root)
        self._lock = Lock()

    def _require_data_root(self) -> Path:
        if self.market_data_root is None:
            raise ProductMarketDataError("Market-data root is not configured.")
        return self.market_data_root

    def identity_retirement_preview(self) -> IdentityRetirementPlan:
        """Inventory contradicted W→BTC generations and saved dependencies."""
        try:
            return preview_retirement(self._require_data_root(), self.workspace_root)
        except (OSError, ValueError, ScannerCatalogError) as exc:
            raise ProductMarketDataError(
                "Identity retirement inventory failed."
            ) from exc

    def retire_identity_data(self, plan: IdentityRetirementPlan) -> None:
        """Apply an unchanged, dependency-free preview through the data owner."""
        data_root = self._require_data_root()
        self.start_maintenance("refresh_market_data")
        try:
            with self._lock:
                current = self.identity_retirement_preview()
                if current != plan:
                    raise ProductMarketDataError(
                        "Retirement preview is stale; preview again."
                    )
                if plan.dependencies:
                    raise ProductMarketDataError(
                        "Saved research depends on contaminated data."
                    )
                if not plan.generations:
                    self.finish_maintenance()
                    return
                audit = (
                    self.workspace_root
                    / "product/identity-retirements"
                    / (f"{plan.fingerprint}.json")
                )
                if audit.is_file():
                    if audit.read_text().strip() != plan.model_dump_json(indent=2):
                        raise ProductMarketDataError(
                            "Retirement audit differs from preview."
                        )
                else:
                    self._write_model_create_only(audit, plan)
                catalog = self._current_catalog(data_root)
                if catalog is not None:
                    removed = {item.relative_path for item in plan.generations}
                    retained = tuple(
                        item
                        for item in catalog.sources
                        if item.relative_path not in removed
                    )
                    if retained:
                        next_catalog = ScannerCatalog.model_validate(
                            catalog.model_copy(
                                update={"sources": retained}
                            ).model_dump()
                        )
                        self._write_catalog(data_root / "catalog.json", next_catalog)
                    else:
                        (data_root / "catalog.json").unlink()
                # Revoke catalog authority before removing verified, unreferenced bytes.
                for relative, _ in plan.file_hashes:
                    contained_file(data_root, relative).unlink()
            self.finish_maintenance()
        except Exception as exc:
            self.fail_maintenance(str(exc).strip() or type(exc).__name__)
            raise

    @staticmethod
    def _write_model_create_only(path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = (model.model_dump_json(indent=2) + "\n").encode("utf-8")
        try:
            with path.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise ProductMarketDataError(
                f"Immutable artifact already exists: {path}"
            ) from exc

    @staticmethod
    def _write_catalog(path: Path, catalog: ScannerCatalog) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
        payload = (catalog.model_dump_json(indent=2) + "\n").encode("utf-8")
        try:
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _ensure_lifecycle_file(data_root: Path, relative_path: str) -> None:
        path = data_root / relative_path
        if path.is_file():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as handle:
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            if not path.is_file():
                raise

    def _current_catalog(self, data_root: Path) -> ScannerCatalog | None:
        if not (data_root / "catalog.json").is_file():
            return None
        try:
            return load_scanner_catalog(data_root)
        except ScannerCatalogError as exc:
            raise ProductMarketDataError(
                "Current market-data catalog is invalid."
            ) from exc

    @staticmethod
    def _next_catalog(
        current: ScannerCatalog | None,
        source: ScannerSourceSpec,
    ) -> ScannerCatalog:
        lifecycle_path = (
            _LIFECYCLE_PATH.as_posix()
            if current is None
            else current.lifecycle_evidence_relative_path
        )
        existing = (
            None
            if current is None
            else next(
                (
                    item
                    for item in current.sources
                    if item.dataset_id == source.dataset_id
                ),
                None,
            )
        )
        replacement = source
        if existing is not None:
            existing_identity = (
                existing.venue,
                existing.venue_symbol,
                existing.base_asset,
                existing.quote_asset,
                existing.interval,
            )
            next_identity = (
                source.venue,
                source.venue_symbol,
                source.base_asset,
                source.quote_asset,
                source.interval,
            )
            if existing_identity != next_identity:
                raise ProductMarketDataError(
                    "Logical dataset identity cannot change across generations."
                )
            replacement = source.model_copy(
                update={
                    "lifecycle_evidence_ids": existing.lifecycle_evidence_ids,
                    "direct_pair_dataset_ids": existing.direct_pair_dataset_ids,
                }
            )
        retained = (
            ()
            if current is None
            else tuple(
                item for item in current.sources if item.dataset_id != source.dataset_id
            )
        )
        return ScannerCatalog(
            schema_version="qap.scanner.catalog.v1",
            lifecycle_evidence_relative_path=lifecycle_path,
            sources=tuple(
                sorted((*retained, replacement), key=lambda item: item.dataset_id)
            ),
        )

    @staticmethod
    def _read_provenance(path: Path) -> MarketDataGenerationProvenance:
        try:
            return MarketDataGenerationProvenance.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            raise ProductMarketDataError(
                "Market-data generation provenance is invalid."
            ) from exc

    @staticmethod
    def _validate_derivation_parents(
        data_root: Path,
        derivation: MarketDataDerivation | None,
    ) -> None:
        if derivation is None:
            return
        root = data_root.resolve()
        for parent in derivation.parents:
            try:
                path = (root / parent.relative_path).resolve(strict=True)
                path.relative_to(root)
                series = read_parquet_bar_series(path)
            except (MarketDataStorageError, OSError, ValueError) as exc:
                raise ProductMarketDataError(
                    "Derived generation parent is unavailable or invalid."
                ) from exc
            if fingerprint_bar_series(series) != parent.semantic_fingerprint:
                raise ProductMarketDataError(
                    "Derived generation parent fingerprint does not match."
                )

    def publish_generation(
        self,
        scope: ProductResearchScope,
        generation: MarketDataGenerationInput,
        *,
        published_at: datetime | None = None,
    ) -> MarketDataGenerationProvenance:
        """Publish one immutable generation, then advance its logical pointer."""

        data_root = self._require_data_root()
        if generation.resolved_instrument not in scope.instruments:
            raise ProductMarketDataError(
                "Generation instrument is not in the resolved Product scope."
            )
        if generation.series.instrument != generation.resolved_instrument.instrument:
            raise ProductMarketDataError(
                "Generation series does not match the resolved Product instrument."
            )
        if not generation.upstream_sources:
            raise ProductMarketDataError(
                "Generation requires upstream acquisition provenance."
            )

        dataset_id = validated_text(generation.dataset_id, field="dataset_id")
        acquisition_implementation = validated_text(
            generation.acquisition_implementation,
            field="acquisition_implementation",
        )
        fingerprint = fingerprint_bar_series(generation.series)
        relative_path = _generation_relative_path(dataset_id, fingerprint)
        provenance_relative_path = _provenance_relative_path(relative_path)
        generation_path = data_root / relative_path
        provenance_path = data_root / provenance_relative_path
        resolved = generation.resolved_instrument
        series = generation.series
        timestamp = (
            datetime.now(UTC)
            if published_at is None
            else validated_utc(published_at, field="published_at")
        )
        provenance = MarketDataGenerationProvenance(
            dataset_id=dataset_id,
            relative_path=relative_path,
            venue=series.instrument.venue,
            venue_symbol=series.instrument.venue_symbol,
            base_asset=series.instrument.base.key,
            quote_asset=series.instrument.quote.key,
            interval=series.interval.label,
            base_asset_identity_version=resolved.base_asset_identity_version,
            quote_asset_identity_version=resolved.quote_asset_identity_version,
            scope_directory_id=scope.directory_id,
            scope_directory_observed_at=scope.directory_observed_at,
            directory_source_id=resolved.source_id,
            directory_source_fingerprint=resolved.source_fingerprint,
            coverage_start=series.bars[0].candle_open_time,
            coverage_end_exclusive=series.bars[-1].bar_end_exclusive,
            acquisition_implementation=acquisition_implementation,
            upstream_sources=generation.upstream_sources,
            derivation=generation.derivation,
            semantic_fingerprint=fingerprint,
            published_at=timestamp,
        )
        source = ScannerSourceSpec(
            dataset_id=dataset_id,
            relative_path=relative_path,
            venue=series.instrument.venue,
            venue_symbol=series.instrument.venue_symbol,
            base_asset=series.instrument.base.key,
            quote_asset=series.instrument.quote.key,
            interval=series.interval.label,
            expected_semantic_fingerprint=fingerprint,
        )

        self._validate_derivation_parents(data_root, generation.derivation)

        with self._lock:
            current = self._current_catalog(data_root)
            next_catalog = self._next_catalog(current, source)
            self._ensure_lifecycle_file(
                data_root,
                next_catalog.lifecycle_evidence_relative_path,
            )
            wrote_generation = False
            wrote_provenance = False
            try:
                stored_fingerprint = write_parquet_bar_series(generation_path, series)
                wrote_generation = True
                if stored_fingerprint != fingerprint:
                    raise ProductMarketDataError(
                        "Stored generation fingerprint changed during publication."
                    )
                self._write_model_create_only(provenance_path, provenance)
                wrote_provenance = True

                reread = read_parquet_bar_series(generation_path)
                if fingerprint_bar_series(reread) != fingerprint:
                    raise ProductMarketDataError(
                        "Published generation failed semantic readback."
                    )
                if self._read_provenance(provenance_path) != provenance:
                    raise ProductMarketDataError(
                        "Published generation provenance failed readback."
                    )
                admitted = resolve_catalog_source(
                    next_catalog,
                    dataset_id=dataset_id,
                    data_root=data_root,
                )
                if admitted.source_artifact_fingerprint != fingerprint:
                    raise ProductMarketDataError("Generation failed catalog admission.")
                self._write_catalog(data_root / "catalog.json", next_catalog)
            except (
                MarketDataStorageError,
                OSError,
                ProductMarketDataError,
                ScannerCatalogError,
                ValueError,
            ) as exc:
                if wrote_provenance:
                    provenance_path.unlink(missing_ok=True)
                if wrote_generation:
                    generation_path.unlink(missing_ok=True)
                if isinstance(exc, ProductMarketDataError):
                    raise
                raise ProductMarketDataError(
                    "Market-data generation publication failed."
                ) from exc
        return provenance

    def projection(self) -> ProductMarketDataProjection:
        """Return current generation integrity and coverage without M4 policy."""

        maintenance = self.maintenance_state()
        if (
            self.market_data_root is None
            or not (self.market_data_root / "catalog.json").is_file()
        ):
            return ProductMarketDataProjection(generations=(), maintenance=maintenance)
        data_root = self.market_data_root
        catalog = self._current_catalog(data_root)
        assert catalog is not None
        rows: list[CurrentMarketDataGeneration] = []
        for source in sorted(catalog.sources, key=lambda item: item.dataset_id):
            provenance_relative_path = _provenance_relative_path(source.relative_path)
            provenance_path = data_root / provenance_relative_path
            try:
                resolved = resolve_catalog_source(
                    catalog,
                    dataset_id=source.dataset_id,
                    data_root=data_root,
                )
            except ScannerCatalogError:
                rows.append(
                    CurrentMarketDataGeneration(
                        dataset_id=source.dataset_id,
                        relative_path=source.relative_path,
                        venue=source.venue,
                        venue_symbol=source.venue_symbol,
                        base_asset=source.base_asset,
                        quote_asset=source.quote_asset,
                        interval=source.interval,
                        semantic_fingerprint=source.expected_semantic_fingerprint,
                        coverage_start=None,
                        coverage_end_exclusive=None,
                        provenance_status="invalid",
                        provenance_relative_path=(
                            provenance_relative_path
                            if provenance_path.is_file()
                            else None
                        ),
                        issue="generation_invalid",
                    )
                )
                continue

            if not provenance_path.is_file():
                provenance_status: ProvenanceStatus = "missing"
                issue = "provenance_missing"
            else:
                try:
                    provenance = self._read_provenance(provenance_path)
                    expected = (
                        provenance.dataset_id == source.dataset_id
                        and provenance.relative_path == source.relative_path
                        and provenance.venue == source.venue
                        and provenance.venue_symbol == source.venue_symbol
                        and provenance.base_asset == source.base_asset
                        and provenance.quote_asset == source.quote_asset
                        and provenance.interval == source.interval
                        and provenance.semantic_fingerprint
                        == source.expected_semantic_fingerprint
                        and provenance.coverage_start
                        == resolved.series.bars[0].candle_open_time
                        and provenance.coverage_end_exclusive
                        == resolved.series.bars[-1].bar_end_exclusive
                    )
                    if not expected:
                        raise ProductMarketDataError(
                            "Generation provenance does not match current source."
                        )
                    provenance_status = "complete"
                    issue = None
                except ProductMarketDataError:
                    provenance_status = "invalid"
                    issue = "provenance_invalid"
            rows.append(
                CurrentMarketDataGeneration(
                    dataset_id=source.dataset_id,
                    relative_path=source.relative_path,
                    venue=source.venue,
                    venue_symbol=source.venue_symbol,
                    base_asset=source.base_asset,
                    quote_asset=source.quote_asset,
                    interval=source.interval,
                    semantic_fingerprint=source.expected_semantic_fingerprint,
                    coverage_start=resolved.series.bars[0].candle_open_time,
                    coverage_end_exclusive=resolved.series.bars[-1].bar_end_exclusive,
                    provenance_status=provenance_status,
                    provenance_relative_path=(
                        provenance_relative_path if provenance_path.is_file() else None
                    ),
                    issue=issue,
                )
            )
        return ProductMarketDataProjection(
            generations=tuple(rows), maintenance=maintenance
        )

    def maintenance_state(self) -> MarketDataMaintenanceState:
        try:
            return self._maintenance.read()
        except ProductMaintenanceError as exc:
            raise ProductMarketDataError(
                "Market-data maintenance state is invalid."
            ) from exc

    def start_maintenance(
        self,
        kind: MaintenanceKind,
        *,
        started_at: datetime | None = None,
    ) -> MarketDataMaintenanceState:
        try:
            return self._maintenance.start(kind, started_at=started_at)
        except ProductMaintenanceError as exc:
            raise ProductMarketDataError(str(exc)) from exc

    def finish_maintenance(self) -> MarketDataMaintenanceState:
        try:
            return self._maintenance.finish()
        except ProductMaintenanceError as exc:
            raise ProductMarketDataError(str(exc)) from exc

    def fail_maintenance(
        self,
        reason: str,
        *,
        finished_at: datetime | None = None,
    ) -> MarketDataMaintenanceState:
        try:
            return self._maintenance.fail(reason, finished_at=finished_at)
        except ProductMaintenanceError as exc:
            raise ProductMarketDataError(str(exc)) from exc


__all__ = [
    "CurrentMarketDataGeneration",
    "MaintenanceKind",
    "MarketDataDerivation",
    "MarketDataGenerationInput",
    "MarketDataGenerationProvenance",
    "MarketDataMaintenanceState",
    "MarketDataParentGeneration",
    "MarketDataUpstreamSource",
    "ProductMarketData",
    "ProductMarketDataError",
    "ProductMarketDataProjection",
]
