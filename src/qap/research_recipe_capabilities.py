"""Explicit versioned capability metadata and compositional support resolution."""

from __future__ import annotations

from qap.experiment.research_recipe import (
    CapabilityKind,
    CapabilityMetadataV1,
    FidelityIntent,
    ResearchObject,
    ResearchRecipeV1,
    SupportAuthority,
    SupportCapability,
    SupportFidelity,
    SupportReadiness,
    SupportReasonCategory,
    SupportReasonCode,
    SupportReasonV1,
    SupportStructure,
)

CAPABILITY_CATALOG_VERSION = "qap.research-capabilities.v1"


def _capability(
    kind: CapabilityKind,
    component_id: str,
    capability: SupportCapability,
    *,
    objects: tuple[ResearchObject, ...] = (
        ResearchObject.PAIR,
        ResearchObject.FIXED_BASKET,
    ),
    owner: str | None = None,
    allocation: str | None = None,
    reason: SupportReasonCode | None = None,
    authority_reason: SupportReasonCode | None = None,
    nearest: str | None = None,
) -> CapabilityMetadataV1:
    return CapabilityMetadataV1(
        kind=kind,
        component_id=component_id,
        capability=capability,
        allowed_research_objects=objects,
        canonical_owner=owner,
        allocation_semantics=allocation,
        reason_code=reason,
        authority_reason=authority_reason,
        nearest_capability=nearest,
    )


CAPABILITY_CATALOG: tuple[CapabilityMetadataV1, ...] = (
    _capability(
        CapabilityKind.RELATIONSHIP,
        "none",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.runner.validate_strategy_policy",
    ),
    _capability(
        CapabilityKind.RELATIONSHIP,
        "rolling_log_ratio_zscore",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
    ),
    _capability(
        CapabilityKind.RELATIONSHIP,
        "residual_mean_reversion",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
    ),
    _capability(
        CapabilityKind.RELATIONSHIP,
        "cross_sectional_relative_log_return",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
    ),
    _capability(
        CapabilityKind.RELATIONSHIP,
        "student_t_copula",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.KNOWN_METHOD_NOT_IMPLEMENTED,
        nearest="residual_mean_reversion",
    ),
    _capability(
        CapabilityKind.DECISION_RULE,
        "evidence_tilt",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
        allocation="long_only_relative_tilt",
    ),
    _capability(
        CapabilityKind.DECISION_RULE,
        "slow_momentum_tilt",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
        allocation="long_only_relative_tilt",
    ),
    _capability(
        CapabilityKind.DECISION_RULE,
        "cross_sectional_tilt",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.model_policies.compose_model_strategy_policy",
        allocation="long_only_relative_tilt",
    ),
    _capability(
        CapabilityKind.DECISION_RULE,
        "scheduled_target",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.runner.validate_strategy_policy",
        allocation="scheduled_target",
    ),
    _capability(
        CapabilityKind.DECISION_RULE,
        "basket_graph",
        SupportCapability.EXECUTABLE,
        objects=(ResearchObject.FIXED_BASKET,),
        owner="qap.experiment.basket_policy.compose_basket_strategy_policy",
        allocation="basket_graph",
    ),
    _capability(
        CapabilityKind.ALLOCATION,
        "long_only_relative_tilt",
        SupportCapability.EXECUTABLE,
        owner="qap.portfolio.AllocationTarget",
    ),
    _capability(
        CapabilityKind.ALLOCATION,
        "scheduled_target",
        SupportCapability.EXECUTABLE,
        owner="qap.policy.ScheduledTargetPolicy",
    ),
    _capability(
        CapabilityKind.ALLOCATION,
        "basket_graph",
        SupportCapability.EXECUTABLE,
        objects=(ResearchObject.FIXED_BASKET,),
        owner="qap.experiment.basket_policy.compose_basket_strategy_policy",
    ),
    _capability(
        CapabilityKind.ALLOCATION,
        "long_short_spread",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.KNOWN_METHOD_NOT_IMPLEMENTED,
        authority_reason=SupportReasonCode.REQUIRES_SHORT_POSITION,
        nearest="long_only_relative_tilt",
    ),
    _capability(CapabilityKind.RISK_OVERLAY, "none", SupportCapability.EXECUTABLE),
    _capability(
        CapabilityKind.RISK_OVERLAY,
        "volatility_filter",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.REQUIRES_UNIMPLEMENTED_RISK_OVERLAY,
    ),
    _capability(
        CapabilityKind.RISK_OVERLAY,
        "adaptive_trailing_stop",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.REQUIRES_UNIMPLEMENTED_RISK_OVERLAY,
    ),
    _capability(CapabilityKind.SELECTION, "fixed", SupportCapability.EXECUTABLE),
    _capability(
        CapabilityKind.SELECTION,
        "precommitted_variants",
        SupportCapability.EXECUTABLE,
    ),
    _capability(
        CapabilityKind.SELECTION,
        "grid_search",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.REQUIRES_UNIMPLEMENTED_PARAMETER_SELECTION,
    ),
    _capability(
        CapabilityKind.SELECTION,
        "walk_forward",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.REQUIRES_UNIMPLEMENTED_WALK_FORWARD_PROTOCOL,
    ),
    _capability(
        CapabilityKind.EXECUTION,
        "direct",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.manifest.ExecutionSpec",
    ),
    _capability(
        CapabilityKind.EXECUTION,
        "multi_asset_bridge",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.manifest.ExecutionSpec",
    ),
    _capability(
        CapabilityKind.EXECUTION,
        "derivative",
        SupportCapability.UNIMPLEMENTED,
        reason=SupportReasonCode.KNOWN_METHOD_NOT_IMPLEMENTED,
        authority_reason=SupportReasonCode.REQUIRES_DERIVATIVE,
    ),
    _capability(
        CapabilityKind.CONTROL,
        "periodic_fixed_weight",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.control_specs.PeriodicFixedWeightControlSpec",
    ),
    _capability(
        CapabilityKind.CONTROL,
        "band_partial",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.control_specs.BandPartialControlSpec",
    ),
    _capability(
        CapabilityKind.CONTROL,
        "contribution_aware_band",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.control_specs.ContributionAwareBandControlSpec",
    ),
    _capability(
        CapabilityKind.CONTROL,
        "pair_blind_relative_momentum",
        SupportCapability.EXECUTABLE,
        owner="qap.experiment.control_specs.PairBlindRelativeMomentumControlSpec",
    ),
)

_CATALOG = {(item.kind, item.component_id): item for item in CAPABILITY_CATALOG}


def reason(
    code: SupportReasonCode,
    category: SupportReasonCategory,
    component: str,
    detail: str,
    *,
    nearest: str | None = None,
) -> SupportReasonV1:
    return SupportReasonV1(
        code=code,
        category=category,
        component=component,
        detail=detail,
        nearest_capability=nearest,
    )


def dedupe(reasons: list[SupportReasonV1]) -> tuple[SupportReasonV1, ...]:
    seen: set[tuple[SupportReasonCode, str, str]] = set()
    result: list[SupportReasonV1] = []
    for item in reasons:
        key = (item.code, item.component, item.detail)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def capability_axis(reasons: tuple[SupportReasonV1, ...]) -> SupportCapability:
    if any(item.code is SupportReasonCode.UNKNOWN_METHOD for item in reasons):
        return SupportCapability.UNKNOWN
    if any(
        item.category is SupportReasonCategory.CAPABILITY
        and item.code
        in {
            SupportReasonCode.KNOWN_METHOD_NOT_IMPLEMENTED,
            SupportReasonCode.METHOD_NOT_ADMITTED_FOR_REPLAY,
            SupportReasonCode.REQUIRES_UNIMPLEMENTED_RISK_OVERLAY,
            SupportReasonCode.REQUIRES_UNIMPLEMENTED_PARAMETER_SELECTION,
            SupportReasonCode.REQUIRES_UNIMPLEMENTED_WALK_FORWARD_PROTOCOL,
            SupportReasonCode.REQUIRES_UNAVAILABLE_NUMERICAL_BACKEND,
        }
        for item in reasons
    ):
        return SupportCapability.UNIMPLEMENTED
    return SupportCapability.EXECUTABLE


def authority_axis(reasons: tuple[SupportReasonV1, ...]) -> SupportAuthority:
    if any(
        item.code is SupportReasonCode.CURRENT_CLAIM_INCOMPATIBLE for item in reasons
    ):
        return SupportAuthority.CLAIM_INCOMPATIBLE
    if any(item.category is SupportReasonCategory.AUTHORITY for item in reasons):
        return SupportAuthority.CONSTITUTION_BLOCKED
    return SupportAuthority.ALLOWED


def structure_axis(reasons: tuple[SupportReasonV1, ...]) -> SupportStructure:
    return (
        SupportStructure.INVALID
        if any(
            item.category
            in {SupportReasonCategory.STRUCTURE, SupportReasonCategory.LINEAGE}
            for item in reasons
        )
        else SupportStructure.VALID
    )


def readiness_axis(reasons: tuple[SupportReasonV1, ...]) -> SupportReadiness:
    return (
        SupportReadiness.NEEDS_SETUP
        if any(item.category is SupportReasonCategory.READINESS for item in reasons)
        else SupportReadiness.READY
    )


def fidelity(
    recipe: ResearchRecipeV1,
    *,
    capability: SupportCapability,
    authority: SupportAuthority,
    reasons: list[SupportReasonV1],
) -> SupportFidelity:
    if recipe.fidelity_intent is FidelityIntent.NATIVE_QAP:
        return SupportFidelity.NATIVE
    if recipe.fidelity_intent is FidelityIntent.ADAPTATION:
        return SupportFidelity.ADAPTATION_REQUIRED
    if (
        capability is SupportCapability.EXECUTABLE
        and authority is SupportAuthority.ALLOWED
    ):
        return SupportFidelity.FAITHFUL_REPLICATION
    reasons.append(
        reason(
            SupportReasonCode.CANNOT_CLAIM_FAITHFUL_REPLICATION,
            SupportReasonCategory.FIDELITY,
            "fidelity_intent",
            (
                "The declared external methodology cannot be reproduced without "
                "semantic substitution."
            ),
        )
    )
    if any(item.nearest_capability for item in reasons):
        reasons.append(
            reason(
                SupportReasonCode.ADAPTATION_AVAILABLE,
                SupportReasonCategory.FIDELITY,
                "fidelity_intent",
                (
                    "A separately declared QAP adaptation may be possible, but it "
                    "is not the same methodology."
                ),
            )
        )
    return SupportFidelity.ADAPTATION_REQUIRED


def resolve_capability_reasons(
    recipe: ResearchRecipeV1,
) -> list[SupportReasonV1]:
    reasons: list[SupportReasonV1] = []
    declarations: list[tuple[CapabilityKind, str, str]] = []
    for variant in recipe.variants:
        prefix = f"variants.{variant.variant_id}"
        declarations.extend(
            (
                (
                    CapabilityKind.RELATIONSHIP,
                    variant.relationship.component_id,
                    f"{prefix}.relationship",
                ),
                (
                    CapabilityKind.DECISION_RULE,
                    variant.decision_rule.component_id,
                    f"{prefix}.decision_rule",
                ),
                (
                    CapabilityKind.ALLOCATION,
                    variant.allocation.component_id,
                    f"{prefix}.allocation",
                ),
            )
        )
        declarations.extend(
            (
                CapabilityKind.RISK_OVERLAY,
                overlay.component_id,
                f"{prefix}.risk_overlays",
            )
            for overlay in variant.risk_overlays
        )
    declarations.append((CapabilityKind.SELECTION, recipe.selection.kind, "selection"))
    declarations.append((CapabilityKind.EXECUTION, recipe.execution.mode, "execution"))
    for position, control in enumerate(recipe.benchmarks.controls):
        control_kind = control.get("kind")
        declarations.append(
            (
                CapabilityKind.CONTROL,
                control_kind if isinstance(control_kind, str) else "",
                f"benchmarks.controls[{position}]",
            )
        )

    for kind, component_id, path in declarations:
        metadata = _CATALOG.get((kind, component_id))
        if metadata is None:
            reasons.append(
                reason(
                    SupportReasonCode.UNKNOWN_METHOD,
                    SupportReasonCategory.CAPABILITY,
                    path,
                    f"Unknown {kind.value} component: {component_id or '<missing>'}.",
                )
            )
            continue
        if recipe.research_object not in metadata.allowed_research_objects:
            reasons.append(
                reason(
                    SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                    SupportReasonCategory.STRUCTURE,
                    path,
                    (
                        f"{component_id} is not admitted for "
                        f"{recipe.research_object.value} recipes."
                    ),
                    nearest=metadata.nearest_capability,
                )
            )
        if metadata.capability is not SupportCapability.EXECUTABLE:
            reasons.append(
                reason(
                    metadata.reason_code
                    or SupportReasonCode.KNOWN_METHOD_NOT_IMPLEMENTED,
                    SupportReasonCategory.CAPABILITY,
                    path,
                    f"{component_id} is known but not executable by current QAP.",
                    nearest=metadata.nearest_capability,
                )
            )
        if metadata.authority_reason is not None:
            reasons.append(
                reason(
                    metadata.authority_reason,
                    SupportReasonCategory.AUTHORITY,
                    path,
                    f"{component_id} requires behavior outside current QAP authority.",
                    nearest=metadata.nearest_capability,
                )
            )

    for variant in recipe.variants:
        metadata = _CATALOG.get(
            (CapabilityKind.DECISION_RULE, variant.decision_rule.component_id)
        )
        if (
            metadata is not None
            and metadata.allocation_semantics is not None
            and metadata.allocation_semantics != variant.allocation.component_id
        ):
            reasons.append(
                reason(
                    SupportReasonCode.INCOMPATIBLE_COMPONENT_COMBINATION,
                    SupportReasonCategory.STRUCTURE,
                    f"variants.{variant.variant_id}.allocation",
                    (
                        "Declared allocation semantics do not match the admitted "
                        "decision rule."
                    ),
                )
            )
    return reasons


__all__ = [
    "CAPABILITY_CATALOG",
    "CAPABILITY_CATALOG_VERSION",
    "authority_axis",
    "capability_axis",
    "dedupe",
    "fidelity",
    "readiness_axis",
    "reason",
    "resolve_capability_reasons",
    "structure_axis",
]
