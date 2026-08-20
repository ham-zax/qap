"""Pure ResearchRecipeV1 compilation into existing ExperimentManifest authority."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pydantic import JsonValue

from qap.experiment.data import load_experiment_data
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.research_recipe import ResearchRecipeV1
from qap.experiment.runner import validate_strategy_policy
from qap.product_market_data_generation import resolve_immutable_generation

RECIPE_COMPILER_VERSION = "qap.research-recipe-compiler.v1"


def compile_research_recipe(
    recipe: ResearchRecipeV1,
    *,
    data_root: str | Path,
) -> tuple[ExperimentManifest, ...]:
    """Compile exact supported variants and revalidate them through current owners."""

    if any(
        variant.decision_rule.component_id == "basket_graph"
        for variant in recipe.variants
    ):
        raise ValueError(
            "basket_graph requires the existing scanner-derived BasketDefinition "
            "replay contract"
        )
    root = Path(data_root).resolve()
    resolved = tuple(
        (
            binding,
            *resolve_immutable_generation(
                root,
                dataset_id=binding.dataset_id,
                semantic_fingerprint=binding.semantic_fingerprint,
            ),
        )
        for binding in recipe.data.generations
    )
    instruments = [
        {
            "instrument_id": binding.dataset_id,
            "venue": provenance.venue,
            "venue_symbol": provenance.venue_symbol,
            "base_asset": provenance.base_asset,
            "quote_asset": provenance.quote_asset,
        }
        for binding, provenance, _series in resolved
    ]
    data_sources = [
        {
            "dataset_id": binding.dataset_id,
            "instrument_id": binding.dataset_id,
            "relative_path": provenance.relative_path,
            "expected_semantic_fingerprint": binding.semantic_fingerprint,
        }
        for binding, provenance, _series in resolved
    ]
    evidence_ids = tuple(
        binding.dataset_id
        for binding, _provenance, _series in resolved
        if binding.purpose == "evidence"
    )
    execution_ids = tuple(
        binding.dataset_id
        for binding, _provenance, _series in resolved
        if binding.purpose == "execution"
    )
    relationship_ids: tuple[str, ...] = ()
    if (
        recipe.research_object.value == "pair"
        and recipe.execution.mode == "multi_asset_bridge"
    ):
        execution_rows = tuple(
            (binding, provenance)
            for binding, provenance, _series in resolved
            if binding.purpose == "execution"
        )
        bridge = recipe.execution.bridge_asset
        if bridge is None or len(execution_rows) != 2:
            raise ValueError(
                "pair multi_asset_bridge requires exactly two execution generations"
            )
        if len({provenance.venue for _binding, provenance in execution_rows}) != 1:
            raise ValueError("pair bridge execution generations must share one venue")
        if {provenance.base_asset for _binding, provenance in execution_rows} != set(
            recipe.assets
        ) or any(
            provenance.quote_asset != bridge for _binding, provenance in execution_rows
        ):
            raise ValueError(
                "pair bridge execution generations must be exact asset/bridge legs"
            )
        relationship_ids = tuple(
            binding.dataset_id for binding, _provenance in execution_rows
        )
    manifests: list[ExperimentManifest] = []
    for variant in recipe.variants:
        relationship_config = dict(variant.relationship.config)
        if (
            variant.relationship.component_id
            in {
                "rolling_log_ratio_zscore",
                "residual_mean_reversion",
            }
            and evidence_ids
        ):
            declared = relationship_config.get("evidence_instrument_ids")
            expected = cast(JsonValue, list(evidence_ids))
            if declared is not None and declared != expected:
                raise ValueError(
                    "relationship evidence_instrument_ids do not match exact data "
                    "binding"
                )
            relationship_config["evidence_instrument_ids"] = expected
        execution: dict[str, object] = {
            "mode": recipe.execution.mode,
            "market_metadata_mode": recipe.execution.market_metadata_mode,
            "numeraire_asset": recipe.execution.numeraire_asset,
            "fee_bps": recipe.execution.fee_bps,
            "slippage_bps": recipe.execution.slippage_bps,
            "minimum_rebalance_notional": recipe.execution.minimum_rebalance_notional,
            "base_step": recipe.execution.base_step,
            "adverse_cost_scenario": recipe.execution.adverse_cost_scenario,
        }
        if recipe.execution.mode == "direct":
            if len(execution_ids) != 1:
                raise ValueError("direct execution requires one execution generation")
            execution["execution_instrument_id"] = execution_ids[0]
        elif recipe.execution.mode == "multi_asset_bridge":
            execution["execution_instrument_ids"] = list(execution_ids)
            execution["bridge_asset"] = recipe.execution.bridge_asset
        manifest = ExperimentManifest.model_validate(
            {
                "schema_version": "qap.experiment.manifest.v1",
                "experiment_name": (
                    f"recipe-{recipe.recipe_sha256[:12]}-{variant.variant_id}"
                ),
                "description": (
                    "ResearchRecipeV1 compiled variant "
                    f"{variant.variant_id}; recipe={recipe.recipe_sha256}."
                ),
                "research_family_id": recipe.research_family_id,
                "parent_run_id": None,
                "basket": list(recipe.assets),
                "starting_quantities": recipe.data.starting_quantities,
                "universe_mode": "declared_fixed_basket",
                "analysis_anchor": recipe.data.analysis_anchor,
                "instruments": instruments,
                "evidence_instrument_ids": list(evidence_ids),
                "relationship_instrument_ids": list(relationship_ids),
                "interval": recipe.data.interval,
                "data_window": recipe.data.data_window.model_dump(mode="json"),
                "evaluation_window": (
                    None
                    if recipe.data.evaluation_window is None
                    else recipe.data.evaluation_window.model_dump(mode="json")
                ),
                "data_sources": data_sources,
                "relationship": {
                    "component_id": variant.relationship.component_id,
                    "config": relationship_config,
                },
                "policy": {
                    "component_id": variant.decision_rule.component_id,
                    "config": variant.decision_rule.config,
                },
                "execution": execution,
                "external_flows": [],
                "benchmarks": {
                    "relationship_alpha_claim": (
                        recipe.benchmarks.relationship_alpha_claim
                    ),
                    "primary_incremental_benchmark": (
                        recipe.benchmarks.primary_incremental_benchmark
                    ),
                    "controls": list(recipe.benchmarks.controls),
                },
                "data_role": recipe.data.data_role.value,
                "primary_metric": recipe.benchmarks.primary_metric,
                "success_threshold": recipe.benchmarks.success_threshold,
                "random_seed": variant.random_seed,
            }
        )
        loaded = load_experiment_data(manifest, data_root=root)
        validate_strategy_policy(manifest, loaded)
        manifests.append(manifest)
    return tuple(manifests)


__all__ = ["RECIPE_COMPILER_VERSION", "compile_research_recipe"]
