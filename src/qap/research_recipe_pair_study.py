"""Pair Study binding and support truth for Product pair recipes."""

from __future__ import annotations

from pathlib import Path

from qap.experiment.research_recipe import (
    ResearchGenerationBindingV1,
    ResearchRecipeV1,
    SupportReasonCategory,
    SupportReasonCode,
    SupportReasonV1,
)
from qap.portfolio import AssetId, PairOrientation
from qap.product_current_approved import current_approved_claim_identity
from qap.product_current_approved_policy import semantic_hash
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.product_market_data_models import MarketDataGenerationProvenance
from qap.product_pair_study import ProductPairStudy, ProductPairStudyError
from qap.product_pair_study_models import PairStudyContext
from qap.product_research_authority import ProductResearchAuthority
from qap.research_recipe_capabilities import reason
from qap.scanner.protocol import ScannerHorizon

_PAIR_STUDY_BINDING_VERSION = "qap.product.pair-study-recipe-binding.v1"
_BRIDGE = AssetId("USDT")


def pair_study_readiness_id(context: PairStudyContext) -> str:
    """Identify the exact selected Pair Study data/economic binding."""

    left = context.data.asset_a_path
    right = context.data.asset_b_path
    if context.data.status != "ready" or left is None or right is None:
        raise ValueError("Pair Study must be ready before recipe binding")
    direct = context.data.direct_market
    return semantic_hash(
        {
            "version": _PAIR_STUDY_BINDING_VERSION,
            "directory_id": context.directory_id,
            "asset_a": context.question.asset_a,
            "asset_b": context.question.asset_b,
            "orientation": context.question.orientation,
            "horizon": context.question.horizon,
            "venue": context.question.venue,
            "interval": context.question.interval,
            "safe_cutoff": (
                None
                if context.question.safe_cutoff is None
                else context.question.safe_cutoff.isoformat()
            ),
            "relationship_generations": [
                [left.dataset_id, left.semantic_fingerprint],
                [right.dataset_id, right.semantic_fingerprint],
            ],
            "direct_status": direct.status,
            "direct_generation": (
                None
                if direct.generation is None
                else [
                    direct.generation.dataset_id,
                    direct.generation.semantic_fingerprint,
                ]
            ),
        }
    )


def _append(
    reasons: list[SupportReasonV1],
    code: SupportReasonCode,
    category: SupportReasonCategory,
    component: str,
    detail: str,
) -> None:
    reasons.append(reason(code, category, component, detail))


def validate_pair_study_recipe(
    recipe: ResearchRecipeV1,
    *,
    pair_study: ProductPairStudy,
    authority: ProductResearchAuthority,
    data_root: Path | None,
    reasons: list[SupportReasonV1],
) -> None:
    """Revalidate one Pair Study-bound recipe without universe-wide readiness."""

    if recipe.data.claim_identity != current_approved_claim_identity():
        _append(
            reasons,
            SupportReasonCode.CURRENT_CLAIM_INCOMPATIBLE,
            SupportReasonCategory.READINESS,
            "data.claim_identity",
            (
                "Pair Study recipe claim identity does not match Product research "
                "authority."
            ),
        )
    if recipe.data.horizon is None or recipe.data.readiness_id is None:
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data",
            "Pair Study recipes require an exact horizon and study binding identity.",
        )
        return
    if data_root is None:
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data",
            "Market-data root is not configured.",
        )
        return

    resolved: list[
        tuple[ResearchGenerationBindingV1, MarketDataGenerationProvenance]
    ] = []
    for binding in recipe.data.generations:
        try:
            provenance, _series = resolve_immutable_generation(
                data_root,
                dataset_id=binding.dataset_id,
                semantic_fingerprint=binding.semantic_fingerprint,
            )
        except ProductGenerationReadError as exc:
            _append(
                reasons,
                SupportReasonCode.REQUIRES_MARKET_DATA,
                SupportReasonCategory.READINESS,
                f"data.generations.{binding.dataset_id}",
                str(exc),
            )
            continue
        if provenance.interval != recipe.data.interval:
            _append(
                reasons,
                SupportReasonCode.REQUIRES_MARKET_DATA,
                SupportReasonCategory.READINESS,
                f"data.generations.{binding.dataset_id}",
                "Immutable generation interval does not match the Pair Study recipe.",
            )
        resolved.append((binding, provenance))
    if len(resolved) != len(recipe.data.generations):
        return
    venues = {provenance.venue for _binding, provenance in resolved}
    if len(venues) != 1:
        _append(
            reasons,
            SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
            SupportReasonCategory.STRUCTURE,
            "data.generations",
            "Pair Study recipe generations must come from one selected venue.",
        )
        return
    venue = next(iter(venues))

    try:
        context = pair_study.context(
            asset_a=AssetId(recipe.assets[0]),
            asset_b=AssetId(recipe.assets[1]),
            orientation=PairOrientation(
                base=AssetId(recipe.assets[0]), quote=AssetId(recipe.assets[1])
            ),
            horizon=ScannerHorizon(recipe.data.horizon),
            venue=venue,
        )
    except (ProductPairStudyError, ValueError) as exc:
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data",
            str(exc),
        )
        return
    if context.data.status != "ready":
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data",
            "The exact selected Pair Study is no longer data-ready.",
        )
        return
    if recipe.data.readiness_id != pair_study_readiness_id(context):
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data.readiness_id",
            "Pair Study venue, cutoff, or immutable generation binding changed.",
        )
    cutoff = context.question.safe_cutoff
    if (
        context.question.interval != recipe.data.interval
        or cutoff is None
        or recipe.data.data_window.end != cutoff
        or recipe.data.evaluation_window is None
        or recipe.data.evaluation_window.end != cutoff
    ):
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data",
            "Recipe timeframe and cutoff must remain bound to the selected Pair Study.",
        )

    left = context.data.asset_a_path
    right = context.data.asset_b_path
    assert left is not None and right is not None
    expected_pair = {
        (left.dataset_id, left.semantic_fingerprint),
        (right.dataset_id, right.semantic_fingerprint),
    }
    execution = {
        (binding.dataset_id, binding.semantic_fingerprint)
        for binding in recipe.data.generations
        if binding.purpose == "execution"
    }
    evidence = {
        (binding.dataset_id, binding.semantic_fingerprint)
        for binding in recipe.data.generations
        if binding.purpose == "evidence"
    }

    if recipe.execution.mode == "multi_asset_bridge":
        if recipe.execution.bridge_asset != _BRIDGE.key:
            _append(
                reasons,
                SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                SupportReasonCategory.STRUCTURE,
                "execution.bridge_asset",
                "Canonical Pair Research bridge execution requires USDT.",
            )
        if execution != expected_pair or evidence:
            _append(
                reasons,
                SupportReasonCode.REQUIRES_MARKET_DATA,
                SupportReasonCategory.READINESS,
                "data.generations",
                (
                    "Pair bridge recipe must bind exactly the two selected Pair Study "
                    "legs."
                ),
            )
        if not authority.allows_transient_bridge(_BRIDGE):
            _append(
                reasons,
                SupportReasonCode.REQUIRES_TRANSIENT_BRIDGE_AUTHORITY,
                SupportReasonCategory.AUTHORITY,
                "execution.bridge_asset",
                (
                    "Temporary USDT ownership inside research replay requires one "
                    "explicit persisted operator permission."
                ),
            )
        return

    direct = context.data.direct_market
    expected_direct: set[tuple[str, str]] = (
        set()
        if direct.status != "ready" or direct.generation is None
        else {(direct.generation.dataset_id, direct.generation.semantic_fingerprint)}
    )
    if not expected_direct:
        _append(
            reasons,
            SupportReasonCode.REQUIRES_REAL_DIRECT_MARKET,
            SupportReasonCategory.READINESS,
            "execution",
            (
                "Direct execution requires the selected Pair Study direct market "
                "to be ready."
            ),
        )
    elif execution != expected_direct or evidence != expected_pair:
        _append(
            reasons,
            SupportReasonCode.REQUIRES_MARKET_DATA,
            SupportReasonCategory.READINESS,
            "data.generations",
            (
                "Direct pair recipe no longer matches the exact selected Pair Study "
                "generations."
            ),
        )


__all__ = ["pair_study_readiness_id", "validate_pair_study_recipe"]
