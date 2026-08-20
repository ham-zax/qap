"""Outer composition root for research recipe preflight and execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from qap.experiment.artifacts import RunArtifactPaths, run_experiment_to_artifacts
from qap.experiment.basket_manifest import validate_basket_manifest_contract
from qap.experiment.data import ExperimentSetupError
from qap.experiment.manifest import BenchmarkSpec, DataRole, ExperimentManifest
from qap.experiment.provenance import manifest_sha256
from qap.experiment.research_recipe import (
    FidelityIntent,
    ResearchObject,
    ResearchRecipeCheckV1,
    ResearchRecipeCompilationV1,
    ResearchRecipeDraftV1,
    ResearchRecipeV1,
    SupportAuthority,
    SupportCapability,
    SupportFidelity,
    SupportReadiness,
    SupportReasonCategory,
    SupportReasonCode,
    SupportReasonV1,
    SupportReportV1,
    SupportStructure,
    canonical_variant_bytes,
)
from qap.experiment.research_recipe_artifacts import (
    ResearchRecipeArtifactError,
    find_research_recipe_compilation,
    write_research_recipe_compilation,
)
from qap.product_current_approved import (
    CurrentApprovedResearch,
    CurrentApprovedResearchError,
    current_approved_claim_identity,
)
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    resolve_immutable_generation,
)
from qap.research_recipe_capabilities import (
    CAPABILITY_CATALOG,
    CAPABILITY_CATALOG_VERSION,
    authority_axis,
    capability_axis,
    dedupe,
    fidelity,
    readiness_axis,
    reason,
    resolve_capability_reasons,
    structure_axis,
)
from qap.research_recipe_compiler import (
    RECIPE_COMPILER_VERSION,
    compile_research_recipe,
)
from qap.scanner.protocol import ScannerHorizon


class ResearchRecipeError(RuntimeError):
    """Raised when a recipe cannot run through current QAP authority."""


@dataclass(frozen=True, slots=True)
class ResearchRecipeExecutionResult:
    compilation_sha256: str
    run_paths: tuple[RunArtifactPaths, ...]

    @property
    def run_ids(self) -> tuple[str, ...]:
        return tuple(path.run_id for path in self.run_paths)


class ResearchRecipeService:
    """Check exact recipes and hand runnable manifests to the existing runner."""

    def __init__(
        self,
        *,
        run_root: str | Path,
        data_root: str | Path | None,
        repository_root: str | Path | None,
        current_approved: CurrentApprovedResearch,
    ) -> None:
        self.run_root = Path(run_root).resolve()
        self.data_root = None if data_root is None else Path(data_root).resolve()
        self.repository_root = (
            None if repository_root is None else Path(repository_root).resolve()
        )
        self.current_approved = current_approved

    def check_draft(self, draft: ResearchRecipeDraftV1) -> ResearchRecipeCheckV1:
        """Canonicalize one draft and return compositional support truth."""

        try:
            research_object = ResearchObject(draft.research_object)
        except ValueError:
            unsupported = reason(
                SupportReasonCode.UNSUPPORTED_RESEARCH_OBJECT,
                SupportReasonCategory.STRUCTURE,
                "research_object",
                "Executable recipes are limited to pair or fixed_basket.",
            )
            return ResearchRecipeCheckV1(
                recipe=None,
                support=SupportReportV1(
                    structure=SupportStructure.INVALID,
                    capability=SupportCapability.UNKNOWN,
                    authority=SupportAuthority.ALLOWED,
                    readiness=SupportReadiness.NEEDS_SETUP,
                    fidelity=SupportFidelity.NOT_APPLICABLE,
                    runnable=False,
                    reasons=(unsupported,),
                ),
            )
        payload = draft.model_dump(mode="python")
        payload["schema_version"] = "qap.research.recipe.v1"
        payload["research_object"] = research_object
        try:
            recipe = ResearchRecipeV1.model_validate(payload)
        except ValidationError as exc:
            invalid = reason(
                SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                SupportReasonCategory.STRUCTURE,
                "recipe",
                str(exc),
            )
            return ResearchRecipeCheckV1(
                recipe=None,
                support=SupportReportV1(
                    structure=SupportStructure.INVALID,
                    capability=SupportCapability.UNKNOWN,
                    authority=SupportAuthority.ALLOWED,
                    readiness=SupportReadiness.NEEDS_SETUP,
                    fidelity=SupportFidelity.NOT_APPLICABLE,
                    runnable=False,
                    reasons=(invalid,),
                ),
            )
        support, _ = self._evaluate(recipe)
        return ResearchRecipeCheckV1(recipe=recipe, support=support)

    def check_recipe(self, recipe: ResearchRecipeV1) -> SupportReportV1:
        """Revalidate one exact recipe without persisting or reserving anything."""

        support, _ = self._evaluate(recipe)
        return support

    def execute(self, recipe: ResearchRecipeV1) -> ResearchRecipeExecutionResult:
        """Persist immutable compilation lineage, then delegate ordinary manifests."""

        support, manifests = self._evaluate(recipe)
        if not support.runnable or manifests is None:
            codes = ", ".join(item.code.value for item in support.reasons)
            raise ResearchRecipeError(f"research recipe is not runnable: {codes}")
        if self.data_root is None or self.repository_root is None:
            raise ResearchRecipeError("recipe execution roots are not configured")
        compilation = ResearchRecipeCompilationV1(
            recipe_sha256=recipe.recipe_sha256,
            research_family_id=recipe.research_family_id,
            compiler_version=RECIPE_COMPILER_VERSION,
            capability_catalog_version=CAPABILITY_CATALOG_VERSION,
            ordered_compiled_manifest_sha256=tuple(
                manifest_sha256(manifest) for manifest in manifests
            ),
        )
        write_research_recipe_compilation(
            run_root=self.run_root,
            recipe=recipe,
            compilation=compilation,
            manifests=manifests,
        )
        run_paths = tuple(
            run_experiment_to_artifacts(
                manifest,
                data_root=self.data_root,
                repository_root=self.repository_root,
                run_root=self.run_root,
            )
            for manifest in manifests
        )
        return ResearchRecipeExecutionResult(
            compilation_sha256=compilation.compilation_sha256,
            run_paths=run_paths,
        )

    def _evaluate(
        self,
        recipe: ResearchRecipeV1,
    ) -> tuple[SupportReportV1, tuple[ExperimentManifest, ...] | None]:
        reasons = resolve_capability_reasons(recipe)
        self._validate_basket_authority(recipe, reasons)
        self._validate_final_oos_selection(recipe, reasons)
        self._validate_readiness(recipe, reasons)

        frozen = dedupe(reasons)
        structure = structure_axis(frozen)
        capability = capability_axis(frozen)
        authority = authority_axis(frozen)
        fidelity_value = fidelity(
            recipe,
            capability=capability,
            authority=authority,
            reasons=reasons,
        )
        frozen = dedupe(reasons)
        structure = structure_axis(frozen)
        capability = capability_axis(frozen)
        authority = authority_axis(frozen)
        readiness = readiness_axis(frozen)
        manifests: tuple[ExperimentManifest, ...] | None = None
        if self._can_compile(
            recipe,
            structure=structure,
            capability=capability,
            authority=authority,
            readiness=readiness,
            fidelity_value=fidelity_value,
        ):
            try:
                if self.data_root is None:
                    raise ProductGenerationReadError(
                        "Market-data root is not configured."
                    )
                manifests = compile_research_recipe(recipe, data_root=self.data_root)
            except (
                ExperimentSetupError,
                ProductGenerationReadError,
                ValidationError,
                ValueError,
            ) as exc:
                reasons.append(
                    reason(
                        SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                        SupportReasonCategory.STRUCTURE,
                        "compiler",
                        str(exc),
                    )
                )
                manifests = None
        frozen = dedupe(reasons)
        structure = structure_axis(frozen)
        capability = capability_axis(frozen)
        authority = authority_axis(frozen)
        readiness = readiness_axis(frozen)
        runnable = manifests is not None and self._can_compile(
            recipe,
            structure=structure,
            capability=capability,
            authority=authority,
            readiness=readiness,
            fidelity_value=fidelity_value,
        )
        suggestions = tuple(
            dict.fromkeys(
                f"Nearest current QAP capability: {item.nearest_capability}"
                for item in frozen
                if item.nearest_capability is not None
            )
        )
        return (
            SupportReportV1(
                structure=structure,
                capability=capability,
                authority=authority,
                readiness=readiness,
                fidelity=fidelity_value,
                runnable=runnable,
                reasons=frozen,
                suggestions=suggestions,
            ),
            manifests,
        )

    @staticmethod
    def _can_compile(
        recipe: ResearchRecipeV1,
        *,
        structure: SupportStructure,
        capability: SupportCapability,
        authority: SupportAuthority,
        readiness: SupportReadiness,
        fidelity_value: SupportFidelity,
    ) -> bool:
        return (
            structure is SupportStructure.VALID
            and capability is SupportCapability.EXECUTABLE
            and authority is SupportAuthority.ALLOWED
            and readiness is SupportReadiness.READY
            and (
                fidelity_value is not SupportFidelity.ADAPTATION_REQUIRED
                or recipe.fidelity_intent is FidelityIntent.ADAPTATION
            )
        )

    def _validate_basket_authority(
        self,
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
                    "relationship_alpha_claim": (
                        recipe.benchmarks.relationship_alpha_claim
                    ),
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
                nearest=(
                    "qap.experiment.basket_scanner_adapter."
                    "prepare_basket_replay_manifest"
                ),
            )
        )

    def _validate_final_oos_selection(
        self,
        recipe: ResearchRecipeV1,
        reasons: list[SupportReasonV1],
    ) -> None:
        if recipe.data.data_role is not DataRole.FINAL_OOS:
            if recipe.selected_from_compilation_sha256 is not None:
                reasons.append(
                    reason(
                        SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                        SupportReasonCategory.STRUCTURE,
                        "selected_from_compilation_sha256",
                        (
                            "Prior-compilation selection lineage is reserved for "
                            "final_oos recipes."
                        ),
                    )
                )
            return
        selected_id = recipe.selection.selected_variant_id
        if (
            len(recipe.variants) != 1
            or recipe.selection.kind != "fixed"
            or selected_id != recipe.variants[0].variant_id
        ):
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_REQUIRES_SINGLE_PRECOMMITTED_VARIANT,
                    SupportReasonCategory.LINEAGE,
                    "selection",
                    (
                        "final_oos requires one already-selected fixed variant and "
                        "no holdout-time search or sibling comparison."
                    ),
                )
            )
        reference = recipe.selected_from_compilation_sha256
        if reference is None:
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_REQUIRES_FROZEN_FAMILY_SELECTION,
                    SupportReasonCategory.LINEAGE,
                    "selected_from_compilation_sha256",
                    (
                        "final_oos requires an immutable prior exploratory/development "
                        "compilation reference."
                    ),
                )
            )
            return
        try:
            prior = find_research_recipe_compilation(self.run_root, reference)
        except ResearchRecipeArtifactError as exc:
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_REQUIRES_FROZEN_FAMILY_SELECTION,
                    SupportReasonCategory.LINEAGE,
                    "selected_from_compilation_sha256",
                    str(exc),
                )
            )
            return
        if prior is None or prior.recipe.data.data_role not in {
            DataRole.EXPLORATORY,
            DataRole.DEVELOPMENT,
        }:
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_REQUIRES_FROZEN_FAMILY_SELECTION,
                    SupportReasonCategory.LINEAGE,
                    "selected_from_compilation_sha256",
                    (
                        "Referenced compilation is not an immutable "
                        "exploratory/development selection source."
                    ),
                )
            )
            return
        if prior.recipe.research_family_id != recipe.research_family_id:
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_FAMILY_MISMATCH,
                    SupportReasonCategory.LINEAGE,
                    "research_family_id",
                    (
                        "final_oos must reuse the research family from the referenced "
                        "compilation."
                    ),
                )
            )
        selected_variant = recipe.variants[0] if len(recipe.variants) == 1 else None
        if selected_variant is None or not any(
            canonical_variant_bytes(candidate)
            == canonical_variant_bytes(selected_variant)
            for candidate in prior.recipe.variants
        ):
            reasons.append(
                reason(
                    SupportReasonCode.FINAL_OOS_REQUIRES_FROZEN_FAMILY_SELECTION,
                    SupportReasonCategory.LINEAGE,
                    "selection.selected_variant_id",
                    (
                        "The selected final_oos variant was not predeclared in the "
                        "referenced compilation."
                    ),
                )
            )

    def _validate_readiness(
        self,
        recipe: ResearchRecipeV1,
        reasons: list[SupportReasonV1],
    ) -> None:
        if recipe.data.authority == "strict_pit":
            reasons.append(
                reason(
                    SupportReasonCode.STRICT_PIT_EVIDENCE_REQUIRED,
                    SupportReasonCategory.READINESS,
                    "data.authority",
                    (
                        "Strict historical PIT evidence remains under existing "
                        "scanner/PIT authority and is not reconstructed by the recipe "
                        "compiler."
                    ),
                )
            )
            return
        if recipe.data.claim_identity != current_approved_claim_identity():
            reasons.append(
                reason(
                    SupportReasonCode.CURRENT_CLAIM_INCOMPATIBLE,
                    SupportReasonCategory.READINESS,
                    "data.claim_identity",
                    (
                        "Recipe claim identity does not match current-approved Product "
                        "research authority."
                    ),
                )
            )
        if recipe.data.horizon is None or recipe.data.readiness_id is None:
            reasons.append(
                reason(
                    SupportReasonCode.REQUIRES_MARKET_DATA,
                    SupportReasonCategory.READINESS,
                    "data",
                    (
                        "Current-approved recipes require a frozen horizon and "
                        "readiness identity."
                    ),
                )
            )
            return
        try:
            current = self.current_approved.readiness(
                ScannerHorizon(recipe.data.horizon)
            )
        except CurrentApprovedResearchError as exc:
            reasons.append(
                reason(
                    SupportReasonCode.REQUIRES_MARKET_DATA,
                    SupportReasonCategory.READINESS,
                    "data",
                    str(exc),
                )
            )
            return
        if current.readiness_id != recipe.data.readiness_id:
            reasons.append(
                reason(
                    SupportReasonCode.REQUIRES_MARKET_DATA,
                    SupportReasonCategory.READINESS,
                    "data.readiness_id",
                    (
                        "Current-approved readiness changed after the exact recipe was "
                        "frozen."
                    ),
                )
            )
        assets = {item.canonical_asset_id: item for item in current.assets}
        for asset_id in recipe.assets:
            asset = assets.get(asset_id)
            if asset is None or not asset.approved:
                reasons.append(
                    reason(
                        SupportReasonCode.REQUIRES_OPERATOR_ASSET_APPROVAL,
                        SupportReasonCategory.READINESS,
                        f"assets.{asset_id}",
                        (
                            "Recipe asset is outside the current operator-approved "
                            "research scope."
                        ),
                    )
                )
                continue
            if asset.identity_state != "resolved":
                reasons.append(
                    reason(
                        SupportReasonCode.REQUIRES_MISSING_IDENTITY_CONFIRMATION,
                        SupportReasonCategory.READINESS,
                        f"assets.{asset_id}",
                        "Recipe asset identity is not explicitly resolved.",
                    )
                )
            if not asset.ready:
                reasons.append(
                    reason(
                        SupportReasonCode.REQUIRES_MARKET_DATA,
                        SupportReasonCategory.READINESS,
                        f"assets.{asset_id}",
                        "Recipe asset is not ready on the current-approved data scope.",
                    )
                )
        available = {
            (
                generation.dataset_id,
                generation.semantic_fingerprint,
                generation.interval,
            )
            for asset in current.assets
            for path in asset.paths
            for generation in path.generations
        } | {
            (
                generation.dataset_id,
                generation.semantic_fingerprint,
                generation.interval,
            )
            for direct in current.direct_markets
            for generation in direct.generations
        }
        for binding in recipe.data.generations:
            if (
                binding.dataset_id,
                binding.semantic_fingerprint,
                recipe.data.interval,
            ) not in available:
                reasons.append(
                    reason(
                        SupportReasonCode.REQUIRES_MARKET_DATA,
                        SupportReasonCategory.READINESS,
                        f"data.generations.{binding.dataset_id}",
                        (
                            "Exact immutable generation is not part of current frozen "
                            "Product readiness."
                        ),
                    )
                )
        if self.data_root is None:
            reasons.append(
                reason(
                    SupportReasonCode.REQUIRES_MARKET_DATA,
                    SupportReasonCategory.READINESS,
                    "data",
                    "Market-data root is not configured.",
                )
            )
        else:
            for binding in recipe.data.generations:
                try:
                    provenance, _ = resolve_immutable_generation(
                        self.data_root,
                        dataset_id=binding.dataset_id,
                        semantic_fingerprint=binding.semantic_fingerprint,
                    )
                    if provenance.interval != recipe.data.interval:
                        raise ProductGenerationReadError(
                            "Immutable generation interval does not match recipe "
                            "interval."
                        )
                except ProductGenerationReadError as exc:
                    reasons.append(
                        reason(
                            SupportReasonCode.REQUIRES_MARKET_DATA,
                            SupportReasonCategory.READINESS,
                            f"data.generations.{binding.dataset_id}",
                            str(exc),
                        )
                    )
        execution = tuple(
            item for item in recipe.data.generations if item.purpose == "execution"
        )
        if recipe.execution.mode == "direct":
            direct_ready = len(execution) == 1 and any(
                direct.status == "ready"
                and {direct.asset_a, direct.asset_b} == set(recipe.assets)
                and any(
                    generation.dataset_id == execution[0].dataset_id
                    and generation.semantic_fingerprint
                    == execution[0].semantic_fingerprint
                    and generation.interval == recipe.data.interval
                    for generation in direct.generations
                )
                for direct in current.direct_markets
            )
            if not direct_ready:
                reasons.append(
                    reason(
                        SupportReasonCode.REQUIRES_REAL_DIRECT_MARKET,
                        SupportReasonCategory.READINESS,
                        "execution",
                        "Direct execution requires one ready direct-market generation.",
                    )
                )
        elif recipe.execution.mode == "multi_asset_bridge" and not execution:
            reasons.append(
                reason(
                    SupportReasonCode.REQUIRES_MARKET_DATA,
                    SupportReasonCategory.READINESS,
                    "execution",
                    "Bridge execution requires exact immutable execution generations.",
                )
            )


__all__ = [
    "CAPABILITY_CATALOG",
    "CAPABILITY_CATALOG_VERSION",
    "RECIPE_COMPILER_VERSION",
    "ResearchRecipeError",
    "ResearchRecipeExecutionResult",
    "ResearchRecipeService",
]
