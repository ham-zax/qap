"""Typed research recipe support-check and execution routes."""

from typing import cast

from fastapi import APIRouter, Request
from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.research_recipe_schemas import (
    ResearchRecipeCheckRequestDto,
    ResearchRecipeRunRequestDto,
)
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import OperationRefDto
from qap.experiment.research_recipe import ResearchRecipeCheckV1
from qap.research_recipe_entry import ResearchRecipeService

router = APIRouter(prefix="/api/research-recipes", tags=["research-recipes"])


def _owner(request: Request) -> ResearchRecipeService:
    owner = cast(object, request.app.state.research_recipe_service)
    if not isinstance(owner, ResearchRecipeService):
        raise RuntimeError("Research recipe service is not configured")
    return owner


@router.post(
    "/check-support",
    response_model=ResearchRecipeCheckV1,
    operation_id="checkResearchRecipeSupport",
)
def check_research_recipe_support(
    command: ResearchRecipeCheckRequestDto,
    request: Request,
) -> ResearchRecipeCheckV1:
    """Explain support without mutating setup, lineage, or scientific state."""

    return _owner(request).check_draft(command.recipe)


@router.post(
    "/run",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="runResearchRecipe",
)
def run_research_recipe(
    command: ResearchRecipeRunRequestDto,
    request: Request,
) -> OperationRefDto:
    owner = _owner(request)
    support = owner.check_recipe(command.recipe)
    if not support.runnable:
        raise ApiBoundaryError(
            code="research_recipe_not_runnable",
            message=(
                "The exact research recipe is not runnable under current QAP authority."
            ),
            status_code=409,
            context={
                "reason_codes": ",".join(
                    reason.code.value for reason in support.reasons
                )
            },
        )
    payload = cast(dict[str, JsonValue], command.model_dump(mode="json"))
    return operation_manager(request).submit(OperationKind.RUN_RESEARCH_RECIPE, payload)


__all__ = ["router"]
