"""HTTP request contracts for typed research recipe preflight and launch."""

from typing import Literal

from qap.api.schemas import ApiDto
from qap.experiment.research_recipe import ResearchRecipeDraftV1, ResearchRecipeV1


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


__all__ = ["ResearchRecipeCheckRequestDto", "ResearchRecipeRunRequestDto"]
