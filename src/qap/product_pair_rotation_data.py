"""Binance pair-data preparation and resampling for the Pair Rotation Lab MVP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from qap.market import (
    BarInterval,
    ValidatedBarSeries,
    fingerprint_bar_series,
)
from qap.market.adapters.gate_historical import (
    GateHistoricalAdapter,
    GateHistoricalDataError,
)
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_binance import (
    BinanceHistoricalAcquirer,
    BinanceHistoricalAcquisitionError,
)
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.product_market_data_models import (
    CurrentMarketDataGeneration,
    MarketDataDerivation,
    MarketDataGenerationInput,
    MarketDataGenerationProvenance,
    MarketDataParentGeneration,
    ProductMarketDataProjection,
)
from qap.product_market_data_prepare import (
    ProductMarketDataPreparation,
    ProductMarketDataPreparationError,
    product_dataset_id,
)
from qap.product_pair_rotation_markets import direct_instrument
from qap.product_pair_rotation_resample import (
    derived_needs_update,
    extend_derived_15m,
    floor_to_interval,
)
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ProductUniverseError,
    ResolvedProductInstrument,
)

_DERIVED_INTERVALS = (BarInterval("1h"), BarInterval("4h"), BarInterval("1d"))
_RESAMPLE_IMPLEMENTATION = "qap.product.pair-rotation-resample.v1"

ProgressCallback = Callable[[str, int, int], None]


def _require_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise ProductMarketDataPreparationError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ProductMarketDataPreparationError(f"{field} must be UTC-aware")
    return value.astimezone(UTC)


def _eligible_pair(
    scope: ProductResearchScope,
) -> tuple[ResolvedProductInstrument, ResolvedProductInstrument]:
    if len(scope.instruments) != 2:
        raise ProductMarketDataPreparationError(
            "Pair rotation requires a scope with exactly 2 instruments, "
            f"found {len(scope.instruments)}."
        )
    for item in scope.instruments:
        if item.instrument.venue != "binance":
            raise ProductMarketDataPreparationError(
                "Pair rotation requires exactly 2 Binance instruments."
            )
        if item.instrument.quote.key != "USDT":
            raise ProductMarketDataPreparationError(
                "Pair rotation requires exactly 2 Binance USDT instruments."
            )
    first, second = scope.instruments
    if first.instrument.base == second.instrument.base:
        raise ProductMarketDataPreparationError(
            "Pair rotation requires 2 distinct Binance USDT base assets."
        )
    if first.instrument.venue_symbol == second.instrument.venue_symbol:
        raise ProductMarketDataPreparationError(
            "Pair rotation requires 2 distinct Binance venue symbols."
        )
    return first, second


class PairRotationData:
    """Prepare immutable 15m history plus derived 1h/4h/1d for one pair."""

    def __init__(
        self, universe: ProductUniverse, market_data: ProductMarketData
    ) -> None:
        self._universe = universe
        self._market_data = market_data
        self._preparation = ProductMarketDataPreparation(universe, market_data)

    def prepare(
        self,
        scope: ProductResearchScope,
        *,
        now: datetime | None = None,
        lookback_days: int = 365,
        progress: ProgressCallback | None = None,
        binance: BinanceHistoricalAcquirer | None = None,
        base_interval: str = "15m",
        include_execution: bool = False,
    ) -> ProductMarketDataProjection:
        first, second = _eligible_pair(scope)
        base = BarInterval(base_interval)
        if base.label not in {"15m", "1m"}:
            raise ProductMarketDataPreparationError("Prepare 15m or 1m source bars.")
        derived_intervals = _DERIVED_INTERVALS if base.label == "15m" else ()
        extra = direct_instrument(self._universe, scope) if include_execution else None
        instruments = (first, second) if extra is None else (first, second, extra)
        scope = replace(scope, instruments=instruments)
        if type(lookback_days) is bool or type(lookback_days) is not int:
            raise ProductMarketDataPreparationError("lookback_days must be an int")
        if lookback_days < 1:
            raise ProductMarketDataPreparationError("lookback_days must be positive")
        lookback_count = lookback_days
        effective_now = _require_utc(
            datetime.now(UTC) if now is None else now, field="now"
        )
        cutoff = floor_to_interval(effective_now, base)
        day_anchor = cutoff - timedelta(days=lookback_count)
        start = datetime(day_anchor.year, day_anchor.month, day_anchor.day, tzinfo=UTC)
        if start >= cutoff:
            raise ProductMarketDataPreparationError("Pair rotation window is empty.")

        total = len(instruments) * (1 + len(derived_intervals))
        if progress is not None:
            progress("prepare", 0, total)

        try:
            self._market_data.start_maintenance("refresh_market_data")
        except ProductMarketDataError as exc:
            raise ProductMarketDataPreparationError(str(exc)) from exc

        owned_binance: BinanceHistoricalAcquirer | None = None
        active_binance = binance
        gate: GateHistoricalAdapter | None = None
        done = 0
        try:
            all_dataset_ids = frozenset(
                product_dataset_id(instrument, interval)
                for instrument in instruments
                for interval in (base, *derived_intervals)
            )
            current_by_id = {
                item.dataset_id: item
                for item in self._market_data.projection(
                    dataset_ids=all_dataset_ids
                ).generations
            }
            if active_binance is None:
                owned_binance = BinanceHistoricalAcquirer()
                active_binance = owned_binance
            gate = GateHistoricalAdapter()
            for instrument in instruments:
                dataset_15m = product_dataset_id(instrument, base)
                try:
                    current = current_by_id.get(dataset_15m)
                    generation = self._preparation.extended_generation(
                        scope=scope,
                        instrument=instrument,
                        dataset_id=dataset_15m,
                        interval=base,
                        start=start,
                        end_exclusive=cutoff,
                        current=current,
                        binance=active_binance,
                        gate=gate,
                    )
                    if generation is not None:
                        provenance = self._market_data.publish_generation(
                            scope, generation
                        )
                        current_by_id[dataset_15m] = CurrentMarketDataGeneration(
                            dataset_id=provenance.dataset_id,
                            relative_path=provenance.relative_path,
                            venue=provenance.venue,
                            venue_symbol=provenance.venue_symbol,
                            base_asset=provenance.base_asset,
                            quote_asset=provenance.quote_asset,
                            interval=provenance.interval,
                            semantic_fingerprint=provenance.semantic_fingerprint,
                            coverage_start=provenance.coverage_start,
                            coverage_end_exclusive=provenance.coverage_end_exclusive,
                            provenance_status="complete",
                            provenance_relative_path=None,
                            issue=None,
                        )
                except (
                    BinanceHistoricalAcquisitionError,
                    GateHistoricalDataError,
                    ProductMarketDataPreparationError,
                    ProductUniverseError,
                    ProductMarketDataError,
                    ProductGenerationReadError,
                    ValueError,
                ) as exc:
                    reason = str(exc).strip() or type(exc).__name__
                    raise ProductMarketDataPreparationError(reason) from exc
                done += 1
                if progress is not None:
                    progress(
                        f"{instrument.instrument.venue_symbol} {base.label}",
                        done,
                        total,
                    )

            for instrument in instruments:
                try:
                    parent_dataset = product_dataset_id(instrument, base)
                    parent_current = current_by_id.get(parent_dataset)
                    if (
                        parent_current is None
                        or parent_current.provenance_status != "complete"
                        or parent_current.coverage_start is None
                        or parent_current.coverage_end_exclusive is None
                    ):
                        raise ProductMarketDataPreparationError(
                            "Binance 15m history is missing for "
                            f"{instrument.instrument.venue_symbol}."
                        )
                    if (
                        parent_current.coverage_start > start
                        or parent_current.coverage_end_exclusive < cutoff
                    ):
                        raise ProductMarketDataPreparationError(
                            "Binance 15m history does not cover the pair window for "
                            f"{instrument.instrument.venue_symbol}."
                        )
                    data_root = self._market_data.market_data_root
                    if data_root is None:
                        raise ProductMarketDataPreparationError(
                            "Market data root is not configured."
                        )
                    parent_loaded: (
                        tuple[MarketDataGenerationProvenance, ValidatedBarSeries] | None
                    ) = None
                    for target in derived_intervals:
                        derived_dataset = product_dataset_id(instrument, target)
                        existing = current_by_id.get(derived_dataset)
                        if derived_needs_update(
                            existing, target, start=start, cutoff=cutoff
                        ):
                            if parent_loaded is None:
                                parent_loaded = resolve_immutable_generation(
                                    data_root,
                                    dataset_id=parent_current.dataset_id,
                                    semantic_fingerprint=parent_current.semantic_fingerprint,
                                )
                            parent_provenance, parent_series = parent_loaded
                            derived = extend_derived_15m(
                                parent_series,
                                target,
                                start=start,
                                cutoff=cutoff,
                                existing=existing,
                                data_root=data_root,
                            )
                            if derived is not None:
                                fingerprint = fingerprint_bar_series(derived)
                                if (
                                    existing is not None
                                    and existing.provenance_status == "complete"
                                    and existing.coverage_start
                                    == derived.bars[0].candle_open_time
                                    and existing.coverage_end_exclusive
                                    == derived.bars[-1].bar_end_exclusive
                                    and existing.semantic_fingerprint == fingerprint
                                ):
                                    pass
                                else:
                                    derived_input = MarketDataGenerationInput(
                                        dataset_id=derived_dataset,
                                        resolved_instrument=instrument,
                                        series=derived,
                                        acquisition_implementation=(
                                            _RESAMPLE_IMPLEMENTATION
                                        ),
                                        upstream_sources=(
                                            parent_provenance.upstream_sources
                                        ),
                                        derivation=MarketDataDerivation(
                                            derivation_id=_RESAMPLE_IMPLEMENTATION,
                                            parents=(
                                                MarketDataParentGeneration(
                                                    dataset_id=parent_current.dataset_id,
                                                    relative_path=(
                                                        parent_current.relative_path
                                                    ),
                                                    semantic_fingerprint=(
                                                        parent_current.semantic_fingerprint
                                                    ),
                                                ),
                                            ),
                                        ),
                                    )
                                    self._market_data.publish_generation(
                                        scope, derived_input
                                    )
                        done += 1
                        if progress is not None:
                            progress(
                                f"{instrument.instrument.venue_symbol} {target.label}",
                                done,
                                total,
                            )
                except ProductMarketDataPreparationError:
                    raise
                except (
                    BinanceHistoricalAcquisitionError,
                    GateHistoricalDataError,
                    ProductMarketDataError,
                    ProductUniverseError,
                    ProductGenerationReadError,
                    ValueError,
                ) as exc:
                    reason = str(exc).strip() or type(exc).__name__
                    raise ProductMarketDataPreparationError(reason) from exc
        except ProductMarketDataPreparationError as exc:
            reason = str(exc).strip() or type(exc).__name__
            try:
                self._market_data.fail_maintenance(reason)
            except ProductMarketDataError:
                pass
            raise
        except Exception as exc:
            reason = str(exc).strip() or type(exc).__name__
            try:
                self._market_data.fail_maintenance(reason)
            except ProductMarketDataError:
                pass
            raise ProductMarketDataPreparationError(reason) from exc
        else:
            try:
                self._market_data.finish_maintenance()
            except ProductMarketDataError as exc:
                raise ProductMarketDataPreparationError(str(exc)) from exc
        finally:
            if gate is not None:
                gate.close()
            if owned_binance is not None:
                owned_binance.close()
        pair_dataset_ids = frozenset(
            product_dataset_id(instrument, interval)
            for instrument in instruments
            for interval in (base, *derived_intervals)
        )
        try:
            return self._market_data.projection(dataset_ids=pair_dataset_ids)
        except ProductMarketDataError as exc:
            raise ProductMarketDataPreparationError(str(exc)) from exc


__all__ = ["PairRotationData"]
