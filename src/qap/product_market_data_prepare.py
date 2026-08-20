"""Product-level historical market-data preparation and refresh orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from qap.market import (
    BarInterval,
    MarketBar,
    MarketDataStorageError,
    ValidatedBarSeries,
    read_parquet_bar_series,
    validate_bar_series,
)
from qap.market.adapters.gate_historical import (
    GateHistoricalAdapter,
    GateHistoricalDataError,
)
from qap.portfolio import AssetId
from qap.product_gate_market_data import (
    acquire_gate_historical_generation_input,
    gate_dataset_id,
)
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_binance import (
    BinanceHistoricalAcquirer,
    BinanceHistoricalAcquisitionError,
)
from qap.product_market_data_models import (
    CurrentMarketDataGeneration,
    MarketDataDerivation,
    MarketDataGenerationInput,
    MarketDataParentGeneration,
    ProductMarketDataProjection,
)
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ProductUniverseError,
    ResolvedProductInstrument,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon

MaintenanceKind = Literal["prepare_market_data", "refresh_market_data"]
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_EXTENSION_IMPLEMENTATION = "qap.product.market-data-current-generation-extension.v1"


class ProductMarketDataPreparationError(RuntimeError):
    """Raised when Product preparation cannot complete its requested market data."""


@dataclass(frozen=True, slots=True)
class ProductMarketDataRequirement:
    interval: BarInterval
    lookback: timedelta


def market_data_requirements(
    horizons: tuple[ScannerHorizon, ...],
) -> tuple[ProductMarketDataRequirement, ...]:
    """Derive Product data requirements from the authoritative Scanner-V1 protocol."""

    if not horizons:
        raise ValueError("at least one scanner horizon is required")
    if len(set(horizons)) != len(horizons):
        raise ValueError("scanner horizons must not contain duplicates")

    by_interval: dict[BarInterval, timedelta] = {}
    for horizon in horizons:
        rule = SCANNER_V1_SLICE1.horizon(horizon)
        model_lookback = rule.evaluation_window + max(
            duration for _template, duration in rule.template_windows
        )
        by_interval[rule.graph_interval] = max(
            by_interval.get(rule.graph_interval, timedelta(0)),
            rule.graph_window,
        )
        for resolution in rule.model_resolutions:
            by_interval[resolution] = max(
                by_interval.get(resolution, timedelta(0)),
                model_lookback,
            )

    return tuple(
        ProductMarketDataRequirement(interval=interval, lookback=lookback)
        for interval, lookback in sorted(
            by_interval.items(), key=lambda item: item[0].duration
        )
    )


def _aligned_completed_end(
    observed_at: datetime,
    interval: BarInterval,
    *,
    now: datetime,
) -> datetime:
    boundary = min(observed_at, now)
    elapsed = boundary - _EPOCH
    steps = elapsed // interval.duration
    return _EPOCH + steps * interval.duration


def _binance_dataset_id(
    instrument: ResolvedProductInstrument,
    interval: BarInterval,
) -> str:
    venue_instrument = instrument.instrument
    if venue_instrument.venue != "binance":
        raise ValueError("Binance dataset identity requires a binance instrument")
    return ":".join(
        (
            "binance-spot",
            venue_instrument.venue_symbol,
            instrument.base_asset_identity_version,
            instrument.quote_asset_identity_version,
            interval.label,
        )
    )


def product_dataset_id(
    instrument: ResolvedProductInstrument,
    interval: BarInterval,
) -> str:
    if instrument.instrument.venue == "binance":
        return _binance_dataset_id(instrument, interval)
    if instrument.instrument.venue == "gate":
        return gate_dataset_id(instrument, interval)
    raise ProductMarketDataPreparationError(
        f"Unsupported Product market-data venue: {instrument.instrument.venue}"
    )


def _current_generations(
    projection: ProductMarketDataProjection,
) -> dict[str, CurrentMarketDataGeneration]:
    return {item.dataset_id: item for item in projection.generations}


class ProductMarketDataPreparation:
    """Drive bounded Product preparation across the explicit resolved M2 scope."""

    def __init__(
        self,
        universe: ProductUniverse,
        market_data: ProductMarketData,
    ) -> None:
        self._universe = universe
        self._market_data = market_data

    def _read_current_series(
        self,
        current: CurrentMarketDataGeneration,
    ) -> ValidatedBarSeries:
        root = self._market_data.market_data_root
        if root is None:
            raise ProductMarketDataError("Market data root is not configured.")
        try:
            return read_parquet_bar_series(root / current.relative_path)
        except (MarketDataStorageError, OSError, ValueError) as exc:
            raise ProductMarketDataPreparationError(
                f"Current market-data generation is unavailable: {current.dataset_id}"
            ) from exc

    @staticmethod
    def _acquire_segment(
        *,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
        binance: BinanceHistoricalAcquirer,
        gate: GateHistoricalAdapter,
    ) -> MarketDataGenerationInput:
        venue = instrument.instrument.venue
        if venue == "binance":
            return binance.acquire_generation_input(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=start,
                end_exclusive=end_exclusive,
            )
        if venue == "gate":
            return acquire_gate_historical_generation_input(
                adapter=gate,
                scope=scope,
                resolved_instrument=instrument,
                interval=interval,
                start=start,
                end_exclusive=end_exclusive,
            )
        raise ProductMarketDataPreparationError(
            f"Unsupported Product market-data venue: {venue}"
        )

    def _extended_generation(
        self,
        *,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
        current: CurrentMarketDataGeneration | None,
        binance: BinanceHistoricalAcquirer,
        gate: GateHistoricalAdapter,
    ) -> MarketDataGenerationInput | None:
        if current is None:
            return self._acquire_segment(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=start,
                end_exclusive=end_exclusive,
                binance=binance,
                gate=gate,
            )

        current_start = current.coverage_start
        current_end = current.coverage_end_exclusive
        if (
            current.provenance_status != "complete"
            or current_start is None
            or current_end is None
        ):
            return self._acquire_segment(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=start,
                end_exclusive=end_exclusive,
                binance=binance,
                gate=gate,
            )

        if current_start <= start and current_end >= end_exclusive:
            return None

        overlaps_or_touches = start <= current_end and end_exclusive >= current_start
        if not overlaps_or_touches:
            return self._acquire_segment(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=start,
                end_exclusive=end_exclusive,
                binance=binance,
                gate=gate,
            )

        parent_series = self._read_current_series(current)
        if (
            parent_series.instrument != instrument.instrument
            or parent_series.interval != interval
        ):
            raise ProductMarketDataPreparationError(
                f"Current generation identity changed unexpectedly: {dataset_id}"
            )

        head: MarketDataGenerationInput | None = None
        tail: MarketDataGenerationInput | None = None
        if start < current_start:
            head = self._acquire_segment(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=start,
                end_exclusive=current_start,
                binance=binance,
                gate=gate,
            )
        if end_exclusive > current_end:
            tail = self._acquire_segment(
                scope=scope,
                instrument=instrument,
                dataset_id=dataset_id,
                interval=interval,
                start=current_end,
                end_exclusive=end_exclusive,
                binance=binance,
                gate=gate,
            )

        additions = tuple(item for item in (head, tail) if item is not None)
        if not additions:
            return None

        bars: list[MarketBar] = []
        if head is not None:
            bars.extend(head.series.bars)
        bars.extend(parent_series.bars)
        if tail is not None:
            bars.extend(tail.series.bars)
        try:
            combined = validate_bar_series(tuple(bars))
        except (TypeError, ValueError) as exc:
            raise ProductMarketDataPreparationError(
                f"Extended generation is not contiguous: {dataset_id}"
            ) from exc

        return MarketDataGenerationInput(
            dataset_id=dataset_id,
            resolved_instrument=instrument,
            series=combined,
            acquisition_implementation=_EXTENSION_IMPLEMENTATION,
            upstream_sources=tuple(
                source for addition in additions for source in addition.upstream_sources
            ),
            derivation=MarketDataDerivation(
                derivation_id=_EXTENSION_IMPLEMENTATION,
                parents=(
                    MarketDataParentGeneration(
                        dataset_id=current.dataset_id,
                        relative_path=current.relative_path,
                        semantic_fingerprint=current.semantic_fingerprint,
                    ),
                ),
            ),
        )

    def _run(
        self,
        kind: MaintenanceKind,
        horizons: tuple[ScannerHorizon, ...],
        *,
        asset_ids: tuple[AssetId, ...] | None = None,
        analysis_reference_ids: tuple[AssetId, ...] = (),
    ) -> ProductMarketDataProjection:
        if self._market_data.market_data_root is None:
            raise ProductMarketDataError("Market data root is not configured.")

        requirements = market_data_requirements(horizons)
        scope = self._universe.resolved_scope(
            asset_ids=asset_ids,
            analysis_reference_ids=analysis_reference_ids,
        )
        if not scope.instruments:
            raise ProductMarketDataPreparationError(
                "Research Universe has no resolved approved/current instruments."
            )

        operation_now = datetime.now(UTC)
        longest_interval = max(
            requirements,
            key=lambda item: item.interval.duration,
        ).interval
        shared_end_by_venue: dict[str, datetime] = {}
        if asset_ids is not None:
            for venue in {item.instrument.venue for item in scope.instruments}:
                observed_at = min(
                    item.directory_observed_at
                    for item in scope.instruments
                    if item.instrument.venue == venue
                )
                shared_end_by_venue[venue] = _aligned_completed_end(
                    observed_at,
                    longest_interval,
                    now=operation_now,
                )
        self._market_data.start_maintenance(kind)
        try:
            current_by_id = _current_generations(self._market_data.projection())
            with (
                BinanceHistoricalAcquirer() as binance,
                GateHistoricalAdapter() as gate,
            ):
                for instrument in scope.instruments:
                    observed_at = min(
                        scope.directory_observed_at,
                        instrument.directory_observed_at,
                    )
                    shared_end = shared_end_by_venue.get(
                        instrument.instrument.venue,
                        _aligned_completed_end(
                            observed_at,
                            longest_interval,
                            now=operation_now,
                        ),
                    )
                    for requirement in requirements:
                        end_exclusive = shared_end
                        start = end_exclusive - requirement.lookback
                        dataset_id = product_dataset_id(
                            instrument, requirement.interval
                        )
                        generation = self._extended_generation(
                            scope=scope,
                            instrument=instrument,
                            dataset_id=dataset_id,
                            interval=requirement.interval,
                            start=start,
                            end_exclusive=end_exclusive,
                            current=current_by_id.get(dataset_id),
                            binance=binance,
                            gate=gate,
                        )
                        if generation is not None:
                            self._market_data.publish_generation(scope, generation)
        except (
            BinanceHistoricalAcquisitionError,
            GateHistoricalDataError,
            ProductMarketDataPreparationError,
            ProductUniverseError,
            ProductMarketDataError,
        ) as exc:
            reason = str(exc).strip() or type(exc).__name__
            self._market_data.fail_maintenance(reason)
            if isinstance(exc, (ProductUniverseError, ProductMarketDataError)):
                raise
            raise ProductMarketDataPreparationError(reason) from exc
        except Exception as exc:
            reason = str(exc).strip() or type(exc).__name__
            self._market_data.fail_maintenance(reason)
            raise
        else:
            self._market_data.finish_maintenance()
        return self._market_data.projection()

    def prepare(
        self,
        horizons: tuple[ScannerHorizon, ...],
        *,
        asset_ids: tuple[AssetId, ...] | None = None,
        analysis_reference_ids: tuple[AssetId, ...] = (),
    ) -> ProductMarketDataProjection:
        return self._run(
            "prepare_market_data",
            horizons,
            asset_ids=asset_ids,
            analysis_reference_ids=analysis_reference_ids,
        )

    def projection(self) -> ProductMarketDataProjection:
        return self._market_data.projection()

    def refresh(
        self,
        horizons: tuple[ScannerHorizon, ...],
        *,
        asset_ids: tuple[AssetId, ...] | None = None,
        analysis_reference_ids: tuple[AssetId, ...] = (),
    ) -> ProductMarketDataProjection:
        return self._run(
            "refresh_market_data",
            horizons,
            asset_ids=asset_ids,
            analysis_reference_ids=analysis_reference_ids,
        )


__all__ = [
    "ProductMarketDataPreparation",
    "ProductMarketDataPreparationError",
    "ProductMarketDataRequirement",
    "market_data_requirements",
    "product_dataset_id",
]
