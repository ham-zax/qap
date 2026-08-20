"""Read-only Product defaults over existing research-recipe and readiness authority."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pydantic import JsonValue

from qap.experiment.manifest import DataRole, DataWindowSpec
from qap.experiment.research_recipe import (
    FidelityIntent,
    ResearchBenchmarkV1,
    ResearchComponentV1,
    ResearchDataBindingV1,
    ResearchExecutionV1,
    ResearchGenerationBindingV1,
    ResearchObject,
    ResearchRecipeDraftV1,
    ResearchSourceV1,
    ResearchVariantV1,
    SelectionProtocolV1,
    SupportReasonCode,
)
from qap.portfolio._decimal import divide
from qap.product_current_approved_models import (
    CurrentApprovedReadiness,
    GenerationBinding,
    ResearchPathReadiness,
)
from qap.product_current_approved_policy import (
    current_approved_scanner_protocol,
    semantic_hash,
)
from qap.product_market_data_generation import resolve_immutable_generation
from qap.research_recipe_entry import ResearchRecipeService
from qap.scanner.protocol import ScannerHorizon, ScannerProtocol, TemplateId

DEFAULT_PRODUCT_RECIPE_VERSION = "qap.product.default-research-recipe.v1"


@dataclass(frozen=True, slots=True)
class ProductRecipeDraftIssue:
    code: SupportReasonCode
    component: str
    detail: str


class ProductRecipeDraftUnavailable(RuntimeError):
    def __init__(self, issue: ProductRecipeDraftIssue) -> None:
        super().__init__(issue.detail)
        self.issue = issue


def _issue(
    code: SupportReasonCode,
    component: str,
    detail: str,
) -> ProductRecipeDraftUnavailable:
    return ProductRecipeDraftUnavailable(
        ProductRecipeDraftIssue(code=code, component=component, detail=detail)
    )


def _asset_row(current: CurrentApprovedReadiness, asset_id: str):
    return next(
        (item for item in current.assets if item.canonical_asset_id == asset_id),
        None,
    )


def _require_assets_ready(
    current: CurrentApprovedReadiness,
    assets: tuple[str, ...],
) -> None:
    for asset_id in assets:
        row = _asset_row(current, asset_id)
        if row is None or not row.approved:
            raise _issue(
                SupportReasonCode.REQUIRES_OPERATOR_ASSET_APPROVAL,
                f"assets.{asset_id}",
                (
                    f"{asset_id} must be approved for Product research before its "
                    "exact recipe can be frozen."
                ),
            )
        if row.identity_state != "resolved":
            raise _issue(
                SupportReasonCode.REQUIRES_MISSING_IDENTITY_CONFIRMATION,
                f"assets.{asset_id}",
                (
                    f"{asset_id} needs one-time identity confirmation before its exact "
                    "recipe can be frozen."
                ),
            )
        if not row.ready:
            raise _issue(
                SupportReasonCode.REQUIRES_MARKET_DATA,
                f"assets.{asset_id}",
                f"{asset_id} needs Product market data for this timeframe.",
            )


def _generation(
    items: tuple[GenerationBinding, ...],
    interval: str,
) -> GenerationBinding | None:
    return next((item for item in items if item.interval == interval), None)


def _path(
    current: CurrentApprovedReadiness,
    *,
    asset_id: str,
    venue: str,
    interval: str,
) -> tuple[ResearchPathReadiness, GenerationBinding] | None:
    asset = _asset_row(current, asset_id)
    if asset is None:
        return None
    for path in asset.paths:
        generation = _generation(path.generations, interval)
        if path.ready and path.venue == venue and generation is not None:
            return path, generation
    return None


def _price_at(series: object, evaluation_start: datetime) -> Decimal:
    bars = getattr(series, "bars", ())
    matches = tuple(
        bar
        for bar in bars
        if getattr(bar, "bar_end_exclusive", None) == evaluation_start
    )
    if len(matches) != 1:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "data",
            (
                "The exact evaluation-start price required by the Product recipe is "
                "unavailable."
            ),
        )
    price = Decimal(str(matches[0].close))
    if not price.is_finite() or price <= 0:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "data",
            (
                "The exact evaluation-start price required by the Product recipe is "
                "invalid."
            ),
        )
    return price


def _family_id(
    *,
    research_object: ResearchObject,
    assets: tuple[str, ...],
    horizon: ScannerHorizon,
    readiness_id: str,
) -> str:
    identity = semantic_hash(
        {
            "version": DEFAULT_PRODUCT_RECIPE_VERSION,
            "research_object": research_object.value,
            "assets": list(assets),
            "horizon": horizon.value,
            "readiness_id": readiness_id,
        }
    )
    return f"product-{research_object.value}-{identity[:32]}"


def _data_windows(current: CurrentApprovedReadiness, horizon: ScannerHorizon):
    if current.safe_cutoff is None:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "data",
            "No backend-safe data cutoff is available for this timeframe yet.",
        )
    protocol = current_approved_scanner_protocol(current.ready_venues)
    rule = protocol.horizon(horizon)
    interval = rule.graph_interval
    window_bars = rule.window_bars(TemplateId.BASE, interval)
    evaluation_end = current.safe_cutoff
    evaluation_start = evaluation_end - rule.evaluation_window
    data_start = evaluation_start - window_bars * interval.duration
    minimum_observations = max(
        3,
        math.ceil(window_bars * protocol.minimum_pair_coverage),
    )
    return (
        protocol,
        interval,
        window_bars,
        minimum_observations,
        data_start,
        evaluation_start,
        evaluation_end,
    )


def _benchmarks(protocol: ScannerProtocol) -> ResearchBenchmarkV1:
    return ResearchBenchmarkV1(
        relationship_alpha_claim=True,
        primary_incremental_benchmark=protocol.primary_control.control_id,
        controls=(
            {
                "kind": "band_partial",
                "control_id": protocol.primary_control.control_id,
                "band_width": str(protocol.primary_control.band_width),
                "partial_correction_fraction": str(
                    protocol.primary_control.partial_correction_fraction
                ),
            },
        ),
        primary_metric="primary_control_relative_terminal_wealth",
        success_threshold="0",
    )


def _pair_draft(
    service: ResearchRecipeService,
    *,
    assets: tuple[str, str],
    horizon: ScannerHorizon,
    current: CurrentApprovedReadiness,
) -> ResearchRecipeDraftV1:
    _require_assets_ready(current, assets)
    (
        protocol,
        interval,
        window_bars,
        minimum_observations,
        data_start,
        evaluation_start,
        evaluation_end,
    ) = _data_windows(current, horizon)
    direct = next(
        (
            item
            for item in current.direct_markets
            if item.status == "ready"
            and {item.asset_a, item.asset_b} == set(assets)
            and _generation(item.generations, interval.label) is not None
        ),
        None,
    )
    if direct is None:
        raise _issue(
            SupportReasonCode.REQUIRES_REAL_DIRECT_MARKET,
            "execution",
            "This pair needs one ready real direct market for deep economic replay.",
        )
    execution_generation = _generation(direct.generations, interval.label)
    assert execution_generation is not None
    evidence: list[GenerationBinding] = []
    for asset_id in assets:
        match = _path(
            current,
            asset_id=asset_id,
            venue=direct.venue,
            interval=interval.label,
        )
        if match is None:
            raise _issue(
                SupportReasonCode.REQUIRES_MARKET_DATA,
                f"assets.{asset_id}",
                (
                    f"{asset_id} lacks a ready {direct.venue} path for this Product "
                    "timeframe."
                ),
            )
        evidence.append(match[1])
    if service.data_root is None:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "data",
            "Product market-data storage is not configured.",
        )
    provenance, series = resolve_immutable_generation(
        service.data_root,
        dataset_id=execution_generation.dataset_id,
        semantic_fingerprint=execution_generation.semantic_fingerprint,
    )
    price = _price_at(series, evaluation_start)
    half = protocol.normalization.total_direct_quote_value / Decimal("2")
    starting_quantities = {
        provenance.base_asset: str(divide(half, price)),
        provenance.quote_asset: str(half),
    }
    policy_config: dict[str, JsonValue] = {
        "base_asset": assets[0],
        "quote_asset": assets[1],
        "neutral_weights": {assets[0]: "0.5", assets[1]: "0.5"},
        "neutral_threshold": str(protocol.neutral_threshold),
        "enter_threshold": str(protocol.entry_threshold),
        "maximum_tilt": str(protocol.maximum_tilt),
        "neutral_mode": "neutral_target",
    }
    variants = tuple(
        ResearchVariantV1(
            variant_id=variant_id,
            relationship=ResearchComponentV1(
                component_id=relationship_id,
                config={
                    "base_asset": assets[0],
                    "quote_asset": assets[1],
                    "window_bars": window_bars,
                    "min_observations": minimum_observations,
                },
            ),
            decision_rule=ResearchComponentV1(
                component_id="evidence_tilt",
                config=policy_config,
            ),
            allocation=ResearchComponentV1(component_id="long_only_relative_tilt"),
        )
        for variant_id, relationship_id in (
            ("log-ratio-base", "rolling_log_ratio_zscore"),
            ("residual-base", "residual_mean_reversion"),
        )
    )
    bindings = tuple(
        ResearchGenerationBindingV1(
            dataset_id=item.dataset_id,
            semantic_fingerprint=item.semantic_fingerprint,
            purpose="evidence",
        )
        for item in evidence
    ) + (
        ResearchGenerationBindingV1(
            dataset_id=execution_generation.dataset_id,
            semantic_fingerprint=execution_generation.semantic_fingerprint,
            purpose="execution",
        ),
    )
    return ResearchRecipeDraftV1(
        research_family_id=_family_id(
            research_object=ResearchObject.PAIR,
            assets=assets,
            horizon=horizon,
            readiness_id=current.readiness_id,
        ),
        research_object=ResearchObject.PAIR.value,
        assets=assets,
        variants=variants,
        selection=SelectionProtocolV1(kind="precommitted_variants"),
        execution=ResearchExecutionV1(
            mode="direct",
            numeraire_asset=provenance.quote_asset,
            fee_bps=str(protocol.cost_policy.fee_bps),
            slippage_bps=str(protocol.cost_policy.slippage_bps),
            minimum_rebalance_notional=str(
                protocol.normalization.minimum_rebalance_notional
            ),
            base_step=(
                None
                if protocol.normalization.base_step is None
                else str(protocol.normalization.base_step)
            ),
            adverse_cost_scenario={
                "fee_bps": str(protocol.cost_policy.adverse_fee_bps),
                "slippage_bps": str(protocol.cost_policy.adverse_slippage_bps),
            },
        ),
        benchmarks=_benchmarks(protocol),
        data=ResearchDataBindingV1(
            authority="current_approved",
            claim_identity=current.claim_identity,
            horizon=horizon.value,
            readiness_id=current.readiness_id,
            data_role=DataRole.DEVELOPMENT,
            interval=interval.label,
            data_window=DataWindowSpec(start=data_start, end=evaluation_end),
            evaluation_window=DataWindowSpec(
                start=evaluation_start,
                end=evaluation_end,
            ),
            generations=bindings,
            analysis_anchor=provenance.quote_asset,
            starting_quantities=starting_quantities,
        ),
        fidelity_intent=FidelityIntent.NATIVE_QAP,
        source=ResearchSourceV1(
            source_id=DEFAULT_PRODUCT_RECIPE_VERSION,
            metadata={"horizon": horizon.value, "template": "base"},
        ),
    )


def _equal_weights(assets: tuple[str, ...]) -> dict[str, JsonValue]:
    unit = Decimal("1") / Decimal(len(assets))
    weights: dict[str, JsonValue] = {}
    allocated = Decimal("0")
    for asset_id in assets[:-1]:
        weights[asset_id] = str(unit)
        allocated += unit
    weights[assets[-1]] = str(Decimal("1") - allocated)
    return weights


def _fixed_basket_draft(
    service: ResearchRecipeService,
    *,
    assets: tuple[str, ...],
    horizon: ScannerHorizon,
    current: CurrentApprovedReadiness,
) -> ResearchRecipeDraftV1:
    _require_assets_ready(current, assets)
    (
        protocol,
        interval,
        window_bars,
        _minimum_observations,
        data_start,
        evaluation_start,
        evaluation_end,
    ) = _data_windows(current, horizon)
    venue = next(
        (
            candidate
            for candidate in current.ready_venues
            if all(
                _path(
                    current,
                    asset_id=asset_id,
                    venue=candidate,
                    interval=interval.label,
                )
                is not None
                for asset_id in assets
            )
        ),
        None,
    )
    if venue is None:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "execution",
            (
                "The selected basket needs one supported venue path for every asset at "
                "this timeframe."
            ),
        )
    matches = tuple(
        _path(
            current,
            asset_id=asset_id,
            venue=venue,
            interval=interval.label,
        )
        for asset_id in assets
    )
    if service.data_root is None:
        raise _issue(
            SupportReasonCode.REQUIRES_MARKET_DATA,
            "data",
            "Product market-data storage is not configured.",
        )
    total = protocol.normalization.total_direct_quote_value
    per_asset = total / Decimal(len(assets))
    starting_quantities: dict[str, str] = {}
    bindings: list[ResearchGenerationBindingV1] = []
    for asset_id, match in zip(assets, matches, strict=True):
        assert match is not None
        _path_row, generation = match
        provenance, series = resolve_immutable_generation(
            service.data_root,
            dataset_id=generation.dataset_id,
            semantic_fingerprint=generation.semantic_fingerprint,
        )
        if provenance.base_asset != asset_id or provenance.quote_asset != "USDT":
            raise _issue(
                SupportReasonCode.REQUIRES_MARKET_DATA,
                f"assets.{asset_id}",
                (
                    "The selected Product path does not match the expected asset/USDT "
                    "bridge semantics."
                ),
            )
        price = _price_at(series, evaluation_start)
        starting_quantities[asset_id] = str(divide(per_asset, price))
        bindings.append(
            ResearchGenerationBindingV1(
                dataset_id=generation.dataset_id,
                semantic_fingerprint=generation.semantic_fingerprint,
                purpose="execution",
            )
        )
    return ResearchRecipeDraftV1(
        research_family_id=_family_id(
            research_object=ResearchObject.FIXED_BASKET,
            assets=assets,
            horizon=horizon,
            readiness_id=current.readiness_id,
        ),
        research_object=ResearchObject.FIXED_BASKET.value,
        assets=assets,
        variants=(
            ResearchVariantV1(
                variant_id="cross-sectional-base",
                relationship=ResearchComponentV1(
                    component_id="cross_sectional_relative_log_return",
                    config={"window_returns": window_bars},
                ),
                decision_rule=ResearchComponentV1(
                    component_id="cross_sectional_tilt",
                    config={
                        "neutral_weights": _equal_weights(assets),
                        "maximum_tilt": str(protocol.maximum_tilt),
                    },
                ),
                allocation=ResearchComponentV1(component_id="long_only_relative_tilt"),
            ),
        ),
        selection=SelectionProtocolV1(
            kind="fixed", selected_variant_id="cross-sectional-base"
        ),
        execution=ResearchExecutionV1(
            mode="multi_asset_bridge",
            bridge_asset="USDT",
            numeraire_asset="USDT",
            fee_bps=str(protocol.cost_policy.fee_bps),
            slippage_bps=str(protocol.cost_policy.slippage_bps),
            minimum_rebalance_notional=str(
                protocol.normalization.minimum_rebalance_notional
            ),
            adverse_cost_scenario={
                "fee_bps": str(protocol.cost_policy.adverse_fee_bps),
                "slippage_bps": str(protocol.cost_policy.adverse_slippage_bps),
            },
        ),
        benchmarks=_benchmarks(protocol),
        data=ResearchDataBindingV1(
            authority="current_approved",
            claim_identity=current.claim_identity,
            horizon=horizon.value,
            readiness_id=current.readiness_id,
            data_role=DataRole.DEVELOPMENT,
            interval=interval.label,
            data_window=DataWindowSpec(start=data_start, end=evaluation_end),
            evaluation_window=DataWindowSpec(
                start=evaluation_start,
                end=evaluation_end,
            ),
            generations=tuple(bindings),
            analysis_anchor="USDT",
            starting_quantities=starting_quantities,
        ),
        fidelity_intent=FidelityIntent.NATIVE_QAP,
        source=ResearchSourceV1(
            source_id=DEFAULT_PRODUCT_RECIPE_VERSION,
            metadata={"horizon": horizon.value, "template": "base"},
        ),
    )


def default_product_recipe_draft(
    service: ResearchRecipeService,
    *,
    research_object: ResearchObject,
    assets: tuple[str, ...],
    horizon: ScannerHorizon,
) -> ResearchRecipeDraftV1:
    """Freeze one backend-owned Product starting recipe over current exact readiness."""

    if research_object is ResearchObject.PAIR and len(assets) != 2:
        raise _issue(
            SupportReasonCode.UNSUPPORTED_RESEARCH_OBJECT,
            "assets",
            "Pair Research requires exactly two selected assets.",
        )
    if research_object is ResearchObject.FIXED_BASKET and len(assets) < 2:
        raise _issue(
            SupportReasonCode.UNSUPPORTED_RESEARCH_OBJECT,
            "assets",
            "Fixed-basket research requires at least two selected assets.",
        )
    current = service.current_approved.readiness(horizon)
    if research_object is ResearchObject.PAIR:
        return _pair_draft(
            service,
            assets=(assets[0], assets[1]),
            horizon=horizon,
            current=current,
        )
    return _fixed_basket_draft(
        service,
        assets=assets,
        horizon=horizon,
        current=current,
    )


__all__ = [
    "DEFAULT_PRODUCT_RECIPE_VERSION",
    "ProductRecipeDraftIssue",
    "ProductRecipeDraftUnavailable",
    "default_product_recipe_draft",
]
