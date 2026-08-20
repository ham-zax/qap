"""HTTP request contracts for typed research recipe preflight and launch."""

from typing import Literal

from qap.api.schemas import ApiDto
from qap.experiment.research_recipe import (
    CapabilityMetadataV1,
    ResearchRecipeCompilationV1,
    ResearchRecipeDraftV1,
    ResearchRecipeV1,
    SupportReasonCode,
)


class ResearchRecipeCheckRequestDto(ApiDto):
    schema_version: Literal["qap.api.research-recipe-check-request.v1"] = (
        "qap.api.research-recipe-check-request.v1"
    )
    recipe: ResearchRecipeDraftV1


class ResearchRecipeRunRequestDto(ApiDto):
    schema_version: Literal["qap.api.research-recipe-run-request.v1"] = (
        "qap.api.research-recipe-run-request.v1"
    )
    recipe: ResearchRecipeV1


class ResearchRecipeProductIssueDto(ApiDto):
    code: SupportReasonCode
    component: str
    detail: str


class ResearchRecipeProductContextDto(ApiDto):
    schema_version: Literal["qap.api.research-recipe-product-context.v1"] = (
        "qap.api.research-recipe-product-context.v1"
    )
    capability_catalog_version: str
    default_recipe_version: str
    capabilities: tuple[CapabilityMetadataV1, ...]
    default_draft: ResearchRecipeDraftV1 | None = None
    default_issue: ResearchRecipeProductIssueDto | None = None


class ResearchRecipeLineageMatchDto(ApiDto):
    recipe: ResearchRecipeV1
    compilation: ResearchRecipeCompilationV1


class ResearchRecipeRunLineageDto(ApiDto):
    schema_version: Literal["qap.api.research-recipe-run-lineage.v1"] = (
        "qap.api.research-recipe-run-lineage.v1"
    )
    run_id: str
    research_family_id: str
    manifest_sha256: str
    matches: tuple[ResearchRecipeLineageMatchDto, ...]


__all__ = [
    "ResearchRecipeCheckRequestDto",
    "ResearchRecipeLineageMatchDto",
    "ResearchRecipeProductContextDto",
    "ResearchRecipeProductIssueDto",
    "ResearchRecipeRunLineageDto",
    "ResearchRecipeRunRequestDto",
]
