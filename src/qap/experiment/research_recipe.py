"""Typed research recipes, compositional support truth, and exact lineage hashes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, JsonValue, field_validator, model_validator

from qap.experiment.manifest import DataRole, DataWindowSpec
from qap.market import BarInterval
from qap.portfolio import AssetId


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ResearchObject(StrEnum):
    PAIR = "pair"
    FIXED_BASKET = "fixed_basket"


class FidelityIntent(StrEnum):
    NATIVE_QAP = "native_qap"
    FAITHFUL_REPLICATION = "faithful_replication"
    ADAPTATION = "adaptation"


class SupportStructure(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class SupportCapability(StrEnum):
    EXECUTABLE = "executable"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    UNIMPLEMENTED = "unimplemented"
    UNKNOWN = "unknown"


class SupportAuthority(StrEnum):
    ALLOWED = "allowed"
    CONSTITUTION_BLOCKED = "constitution_blocked"
    CLAIM_INCOMPATIBLE = "claim_incompatible"


class SupportReadiness(StrEnum):
    READY = "ready"
    NEEDS_SETUP = "needs_setup"


class SupportFidelity(StrEnum):
    NATIVE = "native"
    FAITHFUL_REPLICATION = "faithful_replication"
    ADAPTATION_REQUIRED = "adaptation_required"
    NOT_APPLICABLE = "not_applicable"


class SupportReasonCode(StrEnum):
    UNKNOWN_METHOD = "unknown_method"
    KNOWN_METHOD_NOT_IMPLEMENTED = "known_method_not_implemented"
    METHOD_NOT_ADMITTED_FOR_REPLAY = "method_not_admitted_for_replay"
    METHOD_HAS_NO_CURRENT_DATA_CONTRACT = "method_has_no_current_data_contract"
    UNSUPPORTED_RESEARCH_OBJECT = "unsupported_research_object"
    INCOMPATIBLE_COMPONENT_COMBINATION = "incompatible_component_combination"
    REQUIRES_SHORT_POSITION = "requires_short_position"
    REQUIRES_LEVERAGE_OR_BORROW = "requires_leverage_or_borrow"
    REQUIRES_DERIVATIVE = "requires_derivative"
    REQUIRES_UNIMPLEMENTED_RISK_OVERLAY = "requires_unimplemented_risk_overlay"
    REQUIRES_UNIMPLEMENTED_PARAMETER_SELECTION = (
        "requires_unimplemented_parameter_selection"
    )
    REQUIRES_UNIMPLEMENTED_WALK_FORWARD_PROTOCOL = (
        "requires_unimplemented_walk_forward_protocol"
    )
    REQUIRES_UNAVAILABLE_NUMERICAL_BACKEND = "requires_unavailable_numerical_backend"
    REQUIRES_MISSING_IDENTITY_CONFIRMATION = "requires_missing_identity_confirmation"
    REQUIRES_OPERATOR_ASSET_APPROVAL = "requires_operator_asset_approval"
    REQUIRES_MARKET_DATA = "requires_market_data"
    REQUIRES_REAL_DIRECT_MARKET = "requires_real_direct_market"
    REQUIRES_TRANSIENT_BRIDGE_AUTHORITY = "requires_transient_bridge_authority"
    CURRENT_CLAIM_INCOMPATIBLE = "current_claim_incompatible"
    STRICT_PIT_EVIDENCE_REQUIRED = "strict_pit_evidence_required"
    CANNOT_CLAIM_FAITHFUL_REPLICATION = "cannot_claim_faithful_replication"
    ADAPTATION_AVAILABLE = "adaptation_available"
    FINAL_OOS_REQUIRES_SINGLE_PRECOMMITTED_VARIANT = (
        "final_oos_requires_single_precommitted_variant"
    )
    FINAL_OOS_REQUIRES_FROZEN_FAMILY_SELECTION = (
        "final_oos_requires_frozen_family_selection"
    )
    FINAL_OOS_FAMILY_MISMATCH = "final_oos_family_mismatch"


class SupportReasonCategory(StrEnum):
    STRUCTURE = "structure"
    CAPABILITY = "capability"
    AUTHORITY = "authority"
    READINESS = "readiness"
    FIDELITY = "fidelity"
    LINEAGE = "lineage"


class CapabilityKind(StrEnum):
    RELATIONSHIP = "relationship"
    DECISION_RULE = "decision_rule"
    ALLOCATION = "allocation"
    RISK_OVERLAY = "risk_overlay"
    SELECTION = "selection"
    EXECUTION = "execution"
    CONTROL = "control"


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _validate_sha256(value: str, *, field: str, allow_empty: bool = False) -> str:
    normalized = value.strip().lower()
    if allow_empty and not normalized:
        return ""
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a 64-character SHA-256 hex")
    return normalized


def _no_float_json(value: JsonValue, *, path: str) -> JsonValue:
    if isinstance(value, float):
        raise ValueError(f"{path} must use exact strings instead of floats")
    if isinstance(value, list):
        return [
            _no_float_json(item, path=f"{path}[{position}]")
            for position, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: _no_float_json(item, path=f"{path}.{key}")
            for key, item in value.items()
        }
    return value


class ResearchComponentV1(_FrozenModel):
    component_id: str
    config: dict[str, JsonValue] = {}

    @field_validator("component_id")
    @classmethod
    def validate_component_id(cls, value: str) -> str:
        if not value:
            raise ValueError("component_id must not be empty")
        return value

    @field_validator("config")
    @classmethod
    def validate_exact_config(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], _no_float_json(value, path="config"))


class ResearchVariantV1(_FrozenModel):
    variant_id: str
    relationship: ResearchComponentV1
    decision_rule: ResearchComponentV1
    allocation: ResearchComponentV1
    risk_overlays: tuple[ResearchComponentV1, ...] = ()
    random_seed: int | None = None

    @field_validator("variant_id")
    @classmethod
    def validate_variant_id(cls, value: str) -> str:
        if not value:
            raise ValueError("variant_id must not be empty")
        return value

    @field_validator("random_seed")
    @classmethod
    def validate_seed(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("random_seed must be non-negative")
        return value


class SelectionProtocolV1(_FrozenModel):
    kind: str
    selected_variant_id: str | None = None

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if not value:
            raise ValueError("selection kind must not be empty")
        return value


class ResearchExecutionV1(_FrozenModel):
    mode: str
    market_metadata_mode: str = "required"
    bridge_asset: str | None = None
    numeraire_asset: str
    fee_bps: str
    slippage_bps: str
    minimum_rebalance_notional: str
    base_step: str | None = None
    adverse_cost_scenario: dict[str, JsonValue] | None = None

    @field_validator("bridge_asset", "numeraire_asset", mode="before")
    @classmethod
    def normalize_assets(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("execution assets must be asset keys")
        return AssetId(value).key

    @field_validator("adverse_cost_scenario")
    @classmethod
    def validate_adverse_cost(
        cls, value: dict[str, JsonValue] | None
    ) -> dict[str, JsonValue] | None:
        if value is None:
            return None
        return cast(
            dict[str, JsonValue],
            _no_float_json(value, path="adverse_cost_scenario"),
        )


class ResearchBenchmarkV1(_FrozenModel):
    relationship_alpha_claim: bool = False
    primary_incremental_benchmark: str | None = None
    controls: tuple[dict[str, JsonValue], ...] = ()
    primary_metric: str
    success_threshold: str

    @field_validator("controls")
    @classmethod
    def validate_controls(
        cls, value: tuple[dict[str, JsonValue], ...]
    ) -> tuple[dict[str, JsonValue], ...]:
        return tuple(
            cast(
                dict[str, JsonValue],
                _no_float_json(control, path=f"controls[{position}]"),
            )
            for position, control in enumerate(value)
        )


class ResearchGenerationBindingV1(_FrozenModel):
    dataset_id: str
    semantic_fingerprint: str
    purpose: Literal["execution", "evidence"]

    @field_validator("dataset_id")
    @classmethod
    def validate_dataset_id(cls, value: str) -> str:
        if not value:
            raise ValueError("dataset_id must not be empty")
        return value

    @field_validator("semantic_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value, field="semantic_fingerprint")


class ResearchDataBindingV1(_FrozenModel):
    authority: Literal["current_approved", "pair_study", "strict_pit"]
    claim_identity: str
    horizon: Literal["short", "medium", "swing"] | None = None
    readiness_id: str | None = None
    data_role: DataRole
    interval: str
    data_window: DataWindowSpec
    evaluation_window: DataWindowSpec | None = None
    generations: tuple[ResearchGenerationBindingV1, ...] = ()
    analysis_anchor: str | None = None
    starting_quantities: dict[str, str]

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        return BarInterval(value).label

    @field_validator("readiness_id")
    @classmethod
    def validate_readiness_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_sha256(value, field="readiness_id")

    @field_validator("analysis_anchor", mode="before")
    @classmethod
    def normalize_anchor(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("analysis_anchor must be an asset key")
        return AssetId(value).key

    @field_validator("starting_quantities", mode="before")
    @classmethod
    def normalize_starting_quantities(cls, value: object) -> dict[str, str]:
        if not isinstance(value, Mapping):
            raise ValueError("starting_quantities must be an object")
        result: dict[str, str] = {}
        for raw_asset, raw_quantity in cast(Mapping[object, object], value).items():
            if not isinstance(raw_asset, str) or not isinstance(raw_quantity, str):
                raise ValueError("starting quantities must use asset-key/string pairs")
            asset = AssetId(raw_asset).key
            quantity = raw_quantity.strip()
            if not quantity:
                raise ValueError("starting quantity strings must not be empty")
            if asset in result:
                raise ValueError("starting quantities contain duplicate asset keys")
            result[asset] = quantity
        return result

    @model_validator(mode="after")
    def validate_generation_ids(self) -> Self:
        ids = tuple(item.dataset_id for item in self.generations)
        if len(set(ids)) != len(ids):
            raise ValueError("generation dataset IDs must be unique")
        return self


class ResearchSourceV1(_FrozenModel):
    source_id: str | None = None
    reference: str | None = None
    metadata: dict[str, JsonValue] = {}

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], _no_float_json(value, path="source.metadata"))


class _ResearchRecipeContent(_FrozenModel):
    research_family_id: str
    assets: tuple[str, ...]
    variants: tuple[ResearchVariantV1, ...]
    selection: SelectionProtocolV1
    execution: ResearchExecutionV1
    benchmarks: ResearchBenchmarkV1
    data: ResearchDataBindingV1
    fidelity_intent: FidelityIntent
    source: ResearchSourceV1 = ResearchSourceV1()
    selected_from_compilation_sha256: str | None = None
    derived_from_recipe_sha256: str | None = None

    @field_validator("research_family_id")
    @classmethod
    def validate_family_id(cls, value: str) -> str:
        if not value:
            raise ValueError("research_family_id must not be empty")
        return value

    @field_validator("assets", mode="before")
    @classmethod
    def normalize_assets(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
            raise ValueError("assets must be a list")
        items = cast(list[object] | tuple[object, ...], value)
        if any(not isinstance(item, str) for item in items):
            raise ValueError("assets must contain asset-key strings")
        normalized = tuple(AssetId(cast(str, item)).key for item in items)
        if not normalized or len(set(normalized)) != len(normalized):
            raise ValueError("assets must be non-empty and unique")
        return normalized

    @field_validator(
        "selected_from_compilation_sha256",
        "derived_from_recipe_sha256",
    )
    @classmethod
    def validate_optional_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _validate_sha256(value, field=getattr(info, "field_name", "sha256"))

    @model_validator(mode="after")
    def validate_shared_recipe_contract(self) -> Self:
        variant_ids = tuple(item.variant_id for item in self.variants)
        if not variant_ids or len(set(variant_ids)) != len(variant_ids):
            raise ValueError("variants must be non-empty with unique variant IDs")
        selected = self.selection.selected_variant_id
        if selected is not None and selected not in variant_ids:
            raise ValueError("selected_variant_id must reference a declared variant")
        if self.fidelity_intent is FidelityIntent.ADAPTATION:
            if self.derived_from_recipe_sha256 is None:
                raise ValueError("adaptation requires derived_from_recipe_sha256")
        elif self.derived_from_recipe_sha256 is not None:
            raise ValueError("derived_from_recipe_sha256 is reserved for adaptations")
        return self


class ResearchRecipeDraftV1(_ResearchRecipeContent):
    schema_version: Literal["qap.research.recipe-draft.v1"] = (
        "qap.research.recipe-draft.v1"
    )
    research_object: str


class ResearchRecipeV1(_ResearchRecipeContent):
    schema_version: Literal["qap.research.recipe.v1"] = "qap.research.recipe.v1"
    recipe_sha256: str = ""
    research_object: ResearchObject

    @field_validator("recipe_sha256")
    @classmethod
    def validate_recipe_sha256(cls, value: str) -> str:
        return _validate_sha256(value, field="recipe_sha256", allow_empty=True)

    @model_validator(mode="after")
    def validate_and_seal(self) -> Self:
        if self.research_object is ResearchObject.PAIR and len(self.assets) != 2:
            raise ValueError("pair research requires exactly two assets")
        if self.research_object is ResearchObject.FIXED_BASKET and len(self.assets) < 2:
            raise ValueError("fixed_basket research requires at least two assets")
        expected = canonical_recipe_sha256(self)
        if self.recipe_sha256 and self.recipe_sha256 != expected:
            raise ValueError("recipe_sha256 does not match canonical recipe content")
        object.__setattr__(self, "recipe_sha256", expected)
        return self


class ResearchRecipeCompilationV1(_FrozenModel):
    schema_version: Literal["qap.research.recipe-compilation.v1"] = (
        "qap.research.recipe-compilation.v1"
    )
    compilation_sha256: str = ""
    recipe_sha256: str
    research_family_id: str
    compiler_version: str
    capability_catalog_version: str
    ordered_compiled_manifest_sha256: tuple[str, ...]

    @field_validator("compilation_sha256")
    @classmethod
    def validate_compilation_sha256(cls, value: str) -> str:
        return _validate_sha256(value, field="compilation_sha256", allow_empty=True)

    @field_validator("recipe_sha256")
    @classmethod
    def validate_recipe_sha(cls, value: str) -> str:
        return _validate_sha256(value, field="recipe_sha256")

    @field_validator("ordered_compiled_manifest_sha256")
    @classmethod
    def validate_manifest_hashes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("compilation requires at least one manifest hash")
        return tuple(
            _validate_sha256(value, field="compiled manifest hash") for value in values
        )

    @model_validator(mode="after")
    def validate_and_seal(self) -> Self:
        expected = canonical_compilation_sha256(self)
        if self.compilation_sha256 and self.compilation_sha256 != expected:
            raise ValueError(
                "compilation_sha256 does not match canonical compilation content"
            )
        object.__setattr__(self, "compilation_sha256", expected)
        return self


class SupportReasonV1(_FrozenModel):
    code: SupportReasonCode
    category: SupportReasonCategory
    component: str
    detail: str
    nearest_capability: str | None = None


class SupportReportV1(_FrozenModel):
    schema_version: Literal["qap.research.support-report.v1"] = (
        "qap.research.support-report.v1"
    )
    structure: SupportStructure
    capability: SupportCapability
    authority: SupportAuthority
    readiness: SupportReadiness
    fidelity: SupportFidelity
    runnable: bool
    reasons: tuple[SupportReasonV1, ...] = ()
    suggestions: tuple[str, ...] = ()


class ResearchRecipeCheckV1(_FrozenModel):
    schema_version: Literal["qap.research.recipe-check.v1"] = (
        "qap.research.recipe-check.v1"
    )
    recipe: ResearchRecipeV1 | None
    support: SupportReportV1


class CapabilityMetadataV1(_FrozenModel):
    kind: CapabilityKind
    component_id: str
    capability: SupportCapability
    allowed_research_objects: tuple[ResearchObject, ...]
    canonical_owner: str | None = None
    allocation_semantics: str | None = None
    reason_code: SupportReasonCode | None = None
    authority_reason: SupportReasonCode | None = None
    nearest_capability: str | None = None


def canonical_recipe_sha256(recipe: ResearchRecipeV1) -> str:
    payload = recipe.model_dump(
        mode="json",
        exclude={
            "recipe_sha256",
            "research_family_id",
            "selected_from_compilation_sha256",
            "derived_from_recipe_sha256",
        },
    )
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def canonical_compilation_sha256(compilation: ResearchRecipeCompilationV1) -> str:
    payload = compilation.model_dump(mode="json", exclude={"compilation_sha256"})
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def canonical_variant_bytes(variant: ResearchVariantV1) -> bytes:
    return _canonical_json_bytes(variant.model_dump(mode="json"))


__all__ = [
    "CapabilityKind",
    "CapabilityMetadataV1",
    "FidelityIntent",
    "ResearchBenchmarkV1",
    "ResearchComponentV1",
    "ResearchDataBindingV1",
    "ResearchExecutionV1",
    "ResearchGenerationBindingV1",
    "ResearchObject",
    "ResearchRecipeCheckV1",
    "ResearchRecipeCompilationV1",
    "ResearchRecipeDraftV1",
    "ResearchRecipeV1",
    "ResearchSourceV1",
    "ResearchVariantV1",
    "SelectionProtocolV1",
    "SupportAuthority",
    "SupportCapability",
    "SupportFidelity",
    "SupportReadiness",
    "SupportReasonCategory",
    "SupportReasonCode",
    "SupportReasonV1",
    "SupportReportV1",
    "SupportStructure",
    "canonical_compilation_sha256",
    "canonical_recipe_sha256",
    "canonical_variant_bytes",
]
