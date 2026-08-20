"""Existing scanner-owned basket authority checks for research recipes."""

from pydantic import ValidationError

from qap.experiment.basket_manifest import validate_basket_manifest_contract
from qap.experiment.manifest import BenchmarkSpec
from qap.experiment.research_recipe import (
    ResearchRecipeV1,
    SupportReasonCategory,
    SupportReasonCode,
    SupportReasonV1,
)
from qap.research_recipe_capabilities import reason


def validate_basket_authority(
    recipe: ResearchRecipeV1,
    reasons: list[SupportReasonV1],
) -> None:
    basket_variants = tuple(
        variant
        for variant in recipe.variants
        if variant.decision_rule.component_id == "basket_graph"
    )
    if not basket_variants:
        return
    try:
        benchmark = BenchmarkSpec.model_validate(
            {
                "relationship_alpha_claim": recipe.benchmarks.relationship_alpha_claim,
                "primary_incremental_benchmark": (
                    recipe.benchmarks.primary_incremental_benchmark
                ),
                "controls": list(recipe.benchmarks.controls),
            }
        )
    except ValidationError as exc:
        reasons.append(
            reason(
                SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                SupportReasonCategory.STRUCTURE,
                "benchmarks",
                str(exc),
            )
        )
        return
    for variant in basket_variants:
        try:
            validate_basket_manifest_contract(
                policy_component_id=variant.decision_rule.component_id,
                policy_config=variant.decision_rule.config,
                interval=recipe.data.interval,
                relationship_component_id=variant.relationship.component_id,
                relationship_config=variant.relationship.config,
                execution_mode=recipe.execution.mode,
                data_role=recipe.data.data_role.value,
                has_adverse_cost=recipe.execution.adverse_cost_scenario is not None,
                relationship_alpha_claim=recipe.benchmarks.relationship_alpha_claim,
                primary_incremental_benchmark=(
                    recipe.benchmarks.primary_incremental_benchmark
                ),
                controls=benchmark.controls,
            )
        except ValueError as exc:
            reasons.append(
                reason(
                    SupportReasonCode.METHOD_NOT_ADMITTED_FOR_REPLAY,
                    SupportReasonCategory.CAPABILITY,
                    f"variants.{variant.variant_id}.decision_rule",
                    str(exc),
                )
            )
    reasons.append(
        reason(
            SupportReasonCode.METHOD_HAS_NO_CURRENT_DATA_CONTRACT,
            SupportReasonCategory.READINESS,
            "data",
            (
                "basket_graph remains scanner-derived; arbitrary fixed-basket "
                "declarations cannot replace its BasketDefinition replay contract."
            ),
            nearest="qap.experiment.basket_scanner_adapter.prepare_basket_replay_manifest",
        )
    )


__all__ = ["validate_basket_authority"]
