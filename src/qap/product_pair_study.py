"""Backend-owned Pair Study reads over exact immutable Product market data."""

from __future__ import annotations

import math
from datetime import datetime

from qap.market import (
    BarAlignmentError,
    BarInterval,
    ValidatedBarSeries,
    align_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.product_market_data import ProductMarketData
from qap.product_pair_study_data import PairStudyDataReader, ProductPairStudyError
from qap.product_pair_study_models import (
    LoadedPairStudyGeneration,
    PairStudyAnalysisLens,
    PairStudyContext,
    PairStudyData,
    PairStudyDirectMarket,
    PairStudyEconomicExpression,
    PairStudyQuestion,
    PairStudyReason,
    PairStudyReferenceSeries,
    PairStudyRelationship,
    PairStudySelection,
    PairStudySeries,
    ReadyPairStudy,
    project_observation,
    project_points,
)
from qap.product_research_authority import ProductResearchAuthority
from qap.product_universe import ProductUniverse, ResolvedProductInstrument
from qap.relationship import (
    NormalizationScale,
    RelationshipDataError,
    build_anchor_lens,
    build_log_ratio_series,
    build_normalized_path,
    build_ratio_series,
    rolling_residual_observation,
)
from qap.relationship.models import rolling_log_ratio_observation
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, TemplateId


class ProductPairStudy:
    """Compose one manual pair question without constructing an executable recipe."""

    def __init__(
        self,
        universe: ProductUniverse,
        market_data: ProductMarketData,
        authority: ProductResearchAuthority,
    ) -> None:
        self._data = PairStudyDataReader(universe, market_data)
        self._authority = authority

    def _selection(
        self,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
        orientation: PairOrientation,
        horizon: ScannerHorizon,
        venue: str | None,
        analysis_reference: AssetId | None,
    ) -> PairStudySelection:
        return self._data.selection(
            asset_a=asset_a,
            asset_b=asset_b,
            orientation=orientation,
            horizon=horizon,
            venue=venue,
            analysis_reference=analysis_reference,
        )

    def _load_generation(
        self,
        instrument: ResolvedProductInstrument,
        interval: BarInterval,
    ) -> LoadedPairStudyGeneration | None:
        return self._data.load_generation(instrument, interval)

    def _trim(
        self,
        loaded: LoadedPairStudyGeneration,
        *,
        start: datetime,
        end_exclusive: datetime,
    ) -> ValidatedBarSeries:
        return self._data.trim(loaded, start=start, end_exclusive=end_exclusive)

    def _question(
        self,
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyQuestion:
        return self._data.question(selection, safe_cutoff=safe_cutoff)

    def _ready_pair(self, selection: PairStudySelection) -> ReadyPairStudy | None:
        return self._data.ready_pair(selection)

    def _direct_market(
        self,
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyDirectMarket:
        return self._data.direct_market(selection, safe_cutoff=safe_cutoff)

    def _analysis_lens(
        self,
        selection: PairStudySelection,
        *,
        safe_cutoff: datetime | None,
    ) -> PairStudyAnalysisLens | None:
        return self._data.analysis_lens(selection, safe_cutoff=safe_cutoff)

    @staticmethod
    def _relationship(ready: ReadyPairStudy) -> PairStudyRelationship:
        selection = ready.selection
        safe_cutoff = ready.question.safe_cutoff
        assert safe_cutoff is not None
        try:
            ratio = build_ratio_series(
                ready.aligned,
                orientation=selection.orientation,
                source_fingerprints=ready.source_fingerprints,
                as_of=safe_cutoff,
            )
            log_ratio = build_log_ratio_series(
                ready.aligned,
                orientation=selection.orientation,
                source_fingerprints=ready.source_fingerprints,
                as_of=safe_cutoff,
            )
            normalized_base = build_normalized_path(
                ready.aligned,
                asset=selection.orientation.base,
                scale=NormalizationScale.ONE,
                source_fingerprint=ready.source_fingerprints[
                    selection.orientation.base
                ],
                as_of=safe_cutoff,
            )
            normalized_quote = build_normalized_path(
                ready.aligned,
                asset=selection.orientation.quote,
                scale=NormalizationScale.ONE,
                source_fingerprint=ready.source_fingerprints[
                    selection.orientation.quote
                ],
                as_of=safe_cutoff,
            )
            rule = SCANNER_V1_SLICE1.horizon(selection.horizon)
            window_bars = rule.window_bars(TemplateId.BASE, selection.interval)
            minimum = max(
                3,
                math.ceil(window_bars * SCANNER_V1_SLICE1.minimum_pair_coverage),
            )
            log_observation = rolling_log_ratio_observation(
                log_ratio,
                window_bars=window_bars,
                min_observations=minimum,
                as_of=safe_cutoff,
            )
            residual_observation = rolling_residual_observation(
                ready.aligned,
                orientation=selection.orientation,
                source_fingerprints=ready.source_fingerprints,
                window_bars=window_bars,
                min_observations=minimum,
                as_of=safe_cutoff,
            )
        except (KeyError, RelationshipDataError, ValueError) as exc:
            raise ProductPairStudyError(
                "Pair Study relationship evidence could not be computed."
            ) from exc
        return PairStudyRelationship(
            raw_ratio_current=ratio.values[-1],
            log_ratio_current=log_ratio.values[-1],
            normalized_base_current=normalized_base.values[-1],
            normalized_quote_current=normalized_quote.values[-1],
            rolling_log_ratio=project_observation(log_observation),
            residual_ols=project_observation(residual_observation),
        )

    def context(
        self,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
        orientation: PairOrientation,
        horizon: ScannerHorizon,
        venue: str | None = None,
        analysis_reference: AssetId | None = None,
    ) -> PairStudyContext:
        selection = self._selection(
            asset_a=asset_a,
            asset_b=asset_b,
            orientation=orientation,
            horizon=horizon,
            venue=venue,
            analysis_reference=analysis_reference,
        )
        ready = self._ready_pair(selection)
        direct = self._direct_market(
            selection,
            safe_cutoff=None if ready is None else ready.question.safe_cutoff,
        )
        if ready is None:
            reasons = tuple(
                reason
                for instrument, asset in (
                    (selection.asset_a_instrument, selection.asset_a),
                    (selection.asset_b_instrument, selection.asset_b),
                )
                for reason in (
                    PairStudyReason(
                        code=f"{asset.key.lower()}_path_needs_data",
                        message=(
                            f"{asset.key}/USDT needs immutable data for this timeframe."
                        ),
                    ),
                )
                if self._load_generation(instrument, selection.interval) is None
            )
            if not reasons:
                reasons = (
                    PairStudyReason(
                        code="pair_paths_need_common_window",
                        message=(
                            "Selected paths need a common immutable history window."
                        ),
                    ),
                )
            question = self._question(selection, safe_cutoff=None)
            analysis_lens = self._analysis_lens(selection, safe_cutoff=None)
            data = PairStudyData(
                status="needs_setup",
                reasons=reasons,
                asset_a_path=None,
                asset_b_path=None,
                direct_market=direct,
            )
            relationship = None
        else:
            question = ready.question
            analysis_lens = self._analysis_lens(
                selection,
                safe_cutoff=ready.question.safe_cutoff,
            )
            data = PairStudyData(
                status="ready",
                reasons=(),
                asset_a_path=ready.asset_a.ref,
                asset_b_path=ready.asset_b.ref,
                direct_market=direct,
            )
            relationship = self._relationship(ready)
        bridge_status = (
            "unavailable"
            if data.status != "ready"
            else (
                "ready"
                if self._authority.allows_transient_bridge(AssetId("USDT"))
                else "needs_transient_authority"
            )
        )
        economic_reasons: list[PairStudyReason] = []
        if direct.status != "ready":
            economic_reasons.append(
                PairStudyReason(
                    code="direct_market_not_ready",
                    message=(
                        "Relationship evidence does not need a direct market; direct "
                        "economic replay does."
                    ),
                )
            )
        if direct.status != "ready" and bridge_status == "needs_transient_authority":
            economic_reasons.append(
                PairStudyReason(
                    code="transient_usdt_authority_required",
                    message=(
                        "Two-leg replay uses the real selected asset/USDT paths but "
                        "requires explicit temporary USDT research authority."
                    ),
                )
            )
        elif direct.status != "ready" and bridge_status == "unavailable":
            economic_reasons.append(
                PairStudyReason(
                    code="two_leg_bridge_paths_not_ready",
                    message="Two-leg replay requires both selected Pair Study paths.",
                )
            )
        return PairStudyContext(
            question=question,
            data=data,
            relationship=relationship,
            analysis_lens=analysis_lens,
            economic_expression=PairStudyEconomicExpression(
                direct_status=direct.status,
                bridge_status=bridge_status,
                default_recipe_declarable=data.status == "ready",
                reasons=tuple(economic_reasons),
            ),
            directory_id=selection.scope.directory_id,
        )

    def series(
        self,
        *,
        asset_a: AssetId,
        asset_b: AssetId,
        orientation: PairOrientation,
        horizon: ScannerHorizon,
        venue: str | None = None,
        analysis_reference: AssetId | None = None,
    ) -> PairStudySeries:
        selection = self._selection(
            asset_a=asset_a,
            asset_b=asset_b,
            orientation=orientation,
            horizon=horizon,
            venue=venue,
            analysis_reference=analysis_reference,
        )
        ready = self._ready_pair(selection)
        if ready is None:
            raise ProductPairStudyError(
                "Pair Study series requires prepared exact same-venue immutable data."
            )
        safe_cutoff = ready.question.safe_cutoff
        assert safe_cutoff is not None
        try:
            ratio = build_ratio_series(
                ready.aligned,
                orientation=selection.orientation,
                source_fingerprints=ready.source_fingerprints,
                as_of=safe_cutoff,
            )
            log_ratio = build_log_ratio_series(
                ready.aligned,
                orientation=selection.orientation,
                source_fingerprints=ready.source_fingerprints,
                as_of=safe_cutoff,
            )
            normalized_base = build_normalized_path(
                ready.aligned,
                asset=selection.orientation.base,
                scale=NormalizationScale.ONE,
                source_fingerprint=ready.source_fingerprints[
                    selection.orientation.base
                ],
                as_of=safe_cutoff,
            )
            normalized_quote = build_normalized_path(
                ready.aligned,
                asset=selection.orientation.quote,
                scale=NormalizationScale.ONE,
                source_fingerprint=ready.source_fingerprints[
                    selection.orientation.quote
                ],
                as_of=safe_cutoff,
            )
        except (KeyError, RelationshipDataError, ValueError) as exc:
            raise ProductPairStudyError(
                "Pair Study series could not be computed from exact immutable inputs."
            ) from exc

        reference_series: PairStudyReferenceSeries | None = None
        if selection.reference_asset is not None:
            reference = self._analysis_lens(selection, safe_cutoff=safe_cutoff)
            if reference is not None and reference.status == "ready":
                assert selection.reference_instrument is not None
                loaded = self._load_generation(
                    selection.reference_instrument,
                    selection.interval,
                )
                assert loaded is not None
                start = safe_cutoff - selection.lookback
                reference_bars = self._trim(
                    loaded,
                    start=start,
                    end_exclusive=safe_cutoff,
                )
                try:
                    aligned = align_bar_series(
                        (
                            self._trim(
                                ready.asset_a,
                                start=start,
                                end_exclusive=safe_cutoff,
                            ),
                            self._trim(
                                ready.asset_b,
                                start=start,
                                end_exclusive=safe_cutoff,
                            ),
                            reference_bars,
                        )
                    )
                    fingerprints = {
                        **ready.source_fingerprints,
                        selection.reference_asset: loaded.ref.semantic_fingerprint,
                    }
                    lens = build_anchor_lens(
                        aligned,
                        orientation=selection.orientation,
                        anchor=selection.reference_asset,
                        source_fingerprints=fingerprints,
                        as_of=safe_cutoff,
                    )
                except (
                    BarAlignmentError,
                    KeyError,
                    RelationshipDataError,
                    ValueError,
                ) as exc:
                    raise ProductPairStudyError(
                        "Analysis-reference series could not be aligned."
                    ) from exc
                reference_series = PairStudyReferenceSeries(
                    asset=selection.reference_asset.key,
                    generation=loaded.ref,
                    base_to_reference=project_points(
                        lens.timestamps,
                        tuple(float(value) for value in lens.base_to_anchor),
                        interval=lens.interval,
                    ),
                    quote_to_reference=project_points(
                        lens.timestamps,
                        tuple(float(value) for value in lens.quote_to_anchor),
                        interval=lens.interval,
                    ),
                    base_to_reference_log=project_points(
                        lens.timestamps,
                        tuple(float(value) for value in lens.base_to_anchor_log),
                        interval=lens.interval,
                    ),
                    quote_to_reference_log=project_points(
                        lens.timestamps,
                        tuple(float(value) for value in lens.quote_to_anchor_log),
                        interval=lens.interval,
                    ),
                )
        return PairStudySeries(
            question=ready.question,
            asset_a_path=ready.asset_a.ref,
            asset_b_path=ready.asset_b.ref,
            base_source_fingerprint=ratio.base_source_fingerprint,
            quote_source_fingerprint=ratio.quote_source_fingerprint,
            ratio=project_points(
                ratio.timestamps, ratio.values, interval=ratio.interval
            ),
            log_ratio=project_points(
                log_ratio.timestamps,
                log_ratio.values,
                interval=log_ratio.interval,
            ),
            normalized_base=project_points(
                normalized_base.timestamps,
                normalized_base.values,
                interval=normalized_base.interval,
            ),
            normalized_quote=project_points(
                normalized_quote.timestamps,
                normalized_quote.values,
                interval=normalized_quote.interval,
            ),
            analysis_reference=reference_series,
        )


__all__ = ["ProductPairStudy", "ProductPairStudyError"]
