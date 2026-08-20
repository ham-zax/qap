"""Exact immutable Product data binding for Pair Study."""

from datetime import datetime

from qap.market import (
    BarAlignmentError,
    BarInterval,
    ValidatedBarSeries,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.product_market_data_models import CurrentMarketDataGeneration
from qap.product_market_data_prepare import market_data_requirements, product_dataset_id
from qap.product_pair_study_models import (
    LoadedPairStudyGeneration,
    PairStudyAnalysisLens,
    PairStudyDirectMarket,
    PairStudyQuestion,
    PairStudyReason,
    PairStudySelection,
    ReadyPairStudy,
    project_generation,
)
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ProductUniverseError,
    ResolvedProductInstrument,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon

_PAIR_COORDINATE = AssetId("USDT")


class ProductPairStudyError(RuntimeError):
    """Raised when one Pair Study request cannot be represented truthfully."""


class PairStudyDataReader:
    """Resolve one venue-local Pair Study against current immutable Product data."""

    def __init__(
        self, universe: ProductUniverse, market_data: ProductMarketData
    ) -> None:
        self._universe = universe
        self._market_data = market_data

    @staticmethod
    def _path_instrument(
        scope: ProductResearchScope,
        *,
        asset: AssetId,
        venue: str,
    ) -> ResolvedProductInstrument | None:
        return next(
            (
                item
                for item in scope.instruments
                if item.instrument.venue == venue
                and item.instrument.base == asset
                and item.instrument.quote == _PAIR_COORDINATE
            ),
            None,
        )

    @staticmethod
    def _direct_instrument(
        scope: ProductResearchScope,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
        orientation: PairOrientation,
        venue: str,
    ) -> ResolvedProductInstrument | None:
        direct = tuple(
            item
            for item in scope.instruments
            if item.instrument.venue == venue
            and {item.instrument.base, item.instrument.quote} == {asset_a, asset_b}
        )
        if not direct:
            return None
        return next(
            (
                item
                for item in direct
                if item.instrument.base == orientation.base
                and item.instrument.quote == orientation.quote
            ),
            sorted(direct, key=lambda item: item.instrument.venue_symbol)[0],
        )

    @classmethod
    def _available_venues(
        cls,
        scope: ProductResearchScope,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
    ) -> tuple[str, ...]:
        candidates = {
            item.instrument.venue
            for item in scope.instruments
            if item.instrument.base in {asset_a, asset_b}
            and item.instrument.quote == _PAIR_COORDINATE
        }
        return tuple(
            venue
            for venue in SCANNER_V1_SLICE1.venues
            if venue in candidates
            and cls._path_instrument(scope, asset=asset_a, venue=venue) is not None
            and cls._path_instrument(scope, asset=asset_b, venue=venue) is not None
        )

    def selection(
        self,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
        orientation: PairOrientation,
        horizon: ScannerHorizon,
        venue: str | None,
        analysis_reference: AssetId | None,
    ) -> PairStudySelection:
        if asset_a == asset_b:
            raise ProductPairStudyError(
                "Pair Study requires two distinct economic assets."
            )
        if orientation.pair_id != PairOrientation(base=asset_a, quote=asset_b).pair_id:
            raise ProductPairStudyError(
                "Pair Study orientation must contain the selected assets."
            )
        if analysis_reference in {asset_a, asset_b, _PAIR_COORDINATE}:
            raise ProductPairStudyError(
                "Analysis reference must be a distinct third canonical asset."
            )
        references = () if analysis_reference is None else (analysis_reference,)
        try:
            scope = self._universe.resolved_scope(
                asset_ids=(asset_a, asset_b),
                analysis_reference_ids=references,
            )
        except ProductUniverseError as exc:
            raise ProductPairStudyError(str(exc)) from exc
        available = self._available_venues(
            scope,
            asset_a=asset_a,
            asset_b=asset_b,
        )
        if not available:
            raise ProductPairStudyError(
                "No supported venue has both selected asset/USDT paths."
            )
        requested = None if venue is None else venue.strip().lower()
        selected_venue = available[0] if requested is None else requested
        if selected_venue not in available:
            raise ProductPairStudyError(
                "Requested venue does not have both selected asset/USDT paths."
            )
        rule = SCANNER_V1_SLICE1.horizon(horizon)
        interval = rule.graph_interval
        requirement = next(
            item
            for item in market_data_requirements((horizon,))
            if item.interval == interval
        )
        asset_a_instrument = self._path_instrument(
            scope,
            asset=asset_a,
            venue=selected_venue,
        )
        asset_b_instrument = self._path_instrument(
            scope,
            asset=asset_b,
            venue=selected_venue,
        )
        assert asset_a_instrument is not None and asset_b_instrument is not None
        reference_instrument = (
            None
            if analysis_reference is None
            else self._path_instrument(
                scope,
                asset=analysis_reference,
                venue=selected_venue,
            )
        )
        return PairStudySelection(
            scope=scope,
            asset_a=asset_a,
            asset_b=asset_b,
            orientation=orientation,
            horizon=horizon,
            interval=interval,
            lookback=requirement.lookback,
            venue=selected_venue,
            available_venues=available,
            asset_a_instrument=asset_a_instrument,
            asset_b_instrument=asset_b_instrument,
            direct_instrument=self._direct_instrument(
                scope,
                asset_a=asset_a,
                asset_b=asset_b,
                orientation=orientation,
                venue=selected_venue,
            ),
            reference_asset=analysis_reference,
            reference_instrument=reference_instrument,
        )

    def _current_generation(
        self,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
    ) -> CurrentMarketDataGeneration | None:
        dataset_id = product_dataset_id(instrument, interval)
        try:
            projection = self._market_data.projection()
        except ProductMarketDataError as exc:
            raise ProductPairStudyError(str(exc)) from exc
        return next(
            (
                item
                for item in projection.generations
                if item.dataset_id == dataset_id
                and item.provenance_status == "complete"
                and item.coverage_start is not None
                and item.coverage_end_exclusive is not None
            ),
            None,
        )

    def load_generation(
        self,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
    ) -> LoadedPairStudyGeneration | None:
        current = self._current_generation(instrument, interval)
        if current is None or self._market_data.market_data_root is None:
            return None
        try:
            provenance, series = resolve_immutable_generation(
                self._market_data.market_data_root,
                dataset_id=current.dataset_id,
                semantic_fingerprint=current.semantic_fingerprint,
            )
        except ProductGenerationReadError:
            return None
        if series.instrument != instrument.instrument or series.interval != interval:
            return None
        return LoadedPairStudyGeneration(
            ref=project_generation(provenance),
            series=series,
        )

    @staticmethod
    def trim(
        loaded: LoadedPairStudyGeneration,
        *,
        start: datetime,
        end_exclusive: datetime,
    ) -> ValidatedBarSeries:
        bars = tuple(
            bar
            for bar in loaded.series.bars
            if bar.candle_open_time >= start and bar.bar_end_exclusive <= end_exclusive
        )
        if not bars:
            raise ProductPairStudyError(
                "Selected immutable generation does not cover the Pair Study window."
            )
        try:
            return validate_bar_series(bars)
        except (TypeError, ValueError) as exc:
            raise ProductPairStudyError(
                "Selected immutable generation is not contiguous in the study window."
            ) from exc

    @staticmethod
    def question(
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyQuestion:
        pair_id = selection.orientation.pair_id
        return PairStudyQuestion(
            asset_a=selection.asset_a.key,
            asset_b=selection.asset_b.key,
            canonical_pair=(pair_id.first.key, pair_id.second.key),
            orientation=(
                f"{selection.orientation.base.key}/{selection.orientation.quote.key}"
            ),
            horizon=selection.horizon.value,
            venue=selection.venue,
            available_venues=selection.available_venues,
            coordinate_asset=_PAIR_COORDINATE.key,
            interval=selection.interval.label,
            safe_cutoff=safe_cutoff,
        )

    def ready_pair(self, selection: PairStudySelection) -> ReadyPairStudy | None:
        left = self.load_generation(selection.asset_a_instrument, selection.interval)
        right = self.load_generation(selection.asset_b_instrument, selection.interval)
        if left is None or right is None:
            return None
        safe_cutoff = min(
            left.ref.coverage_end_exclusive,
            right.ref.coverage_end_exclusive,
        )
        start = safe_cutoff - selection.lookback
        if left.ref.coverage_start > start or right.ref.coverage_start > start:
            return None
        left_series = self.trim(left, start=start, end_exclusive=safe_cutoff)
        right_series = self.trim(right, start=start, end_exclusive=safe_cutoff)
        try:
            aligned = align_bar_series((left_series, right_series))
        except BarAlignmentError as exc:
            raise ProductPairStudyError(
                "Selected same-venue paths do not share one contiguous index."
            ) from exc
        if aligned.timestamps[-1] + aligned.interval.duration != safe_cutoff:
            raise ProductPairStudyError(
                "Selected Pair Study paths do not reach the common safe cutoff."
            )
        return ReadyPairStudy(
            question=self.question(selection, safe_cutoff=safe_cutoff),
            selection=selection,
            asset_a=left,
            asset_b=right,
            aligned=aligned,
            source_fingerprints={
                selection.asset_a: left.ref.semantic_fingerprint,
                selection.asset_b: right.ref.semantic_fingerprint,
            },
        )

    def direct_market(
        self,
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyDirectMarket:
        direct = selection.direct_instrument
        if direct is None:
            return PairStudyDirectMarket(
                status="unavailable",
                venue=selection.venue,
                venue_symbol=None,
                base_asset=None,
                quote_asset=None,
                generation=None,
            )
        loaded = self.load_generation(direct, selection.interval)
        ready = loaded is not None
        if loaded is not None and safe_cutoff is not None:
            ready = (
                loaded.ref.coverage_start <= safe_cutoff - selection.lookback
                and loaded.ref.coverage_end_exclusive >= safe_cutoff
            )
        return PairStudyDirectMarket(
            status="ready" if ready else "needs_data",
            venue=selection.venue,
            venue_symbol=direct.instrument.venue_symbol,
            base_asset=direct.instrument.base.key,
            quote_asset=direct.instrument.quote.key,
            generation=None if loaded is None else loaded.ref,
        )

    def analysis_lens(
        self,
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyAnalysisLens | None:
        asset = selection.reference_asset
        if asset is None:
            return None
        instrument = selection.reference_instrument
        if instrument is None:
            return PairStudyAnalysisLens(
                asset=asset.key,
                status="unavailable",
                generation=None,
                reason=PairStudyReason(
                    code="analysis_reference_path_unavailable",
                    message=(f"{asset.key}/USDT is unavailable on the selected venue."),
                ),
            )
        loaded = self.load_generation(instrument, selection.interval)
        if loaded is None:
            return PairStudyAnalysisLens(
                asset=asset.key,
                status="needs_data",
                generation=None,
                reason=PairStudyReason(
                    code="analysis_reference_needs_data",
                    message=(
                        f"{asset.key}/USDT needs immutable data for this timeframe."
                    ),
                ),
            )
        if safe_cutoff is not None and (
            loaded.ref.coverage_start > safe_cutoff - selection.lookback
            or loaded.ref.coverage_end_exclusive < safe_cutoff
        ):
            return PairStudyAnalysisLens(
                asset=asset.key,
                status="needs_data",
                generation=loaded.ref,
                reason=PairStudyReason(
                    code="analysis_reference_needs_data",
                    message=(
                        f"{asset.key}/USDT does not cover the current study window."
                    ),
                ),
            )
        return PairStudyAnalysisLens(
            asset=asset.key,
            status="ready",
            generation=loaded.ref,
            reason=None,
        )


__all__ = ["PairStudyDataReader", "ProductPairStudyError"]
