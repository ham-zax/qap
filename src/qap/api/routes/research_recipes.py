"""Typed research recipe support-check and execution routes."""

from typing import Literal, cast

from fastapi import APIRouter, Query, Request
from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.relationship_views import requested_pair_orientation
from qap.api.research_recipe_schemas import (
    ResearchRecipeCheckRequestDto,
    ResearchRecipeLineageMatchDto,
    ResearchRecipeProductContextDto,
    ResearchRecipeProductIssueDto,
    ResearchRecipeRunLineageDto,
    ResearchRecipeRunRequestDto,
)
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import OperationRefDto
from qap.experiment.artifacts import ArtifactError, read_run_artifacts
from qap.experiment.provenance import manifest_sha256
from qap.experiment.research_recipe import (
    ResearchObject,
    ResearchRecipeCheckV1,
    SupportReasonCode,
)
from qap.experiment.research_recipe_artifacts import (
    ResearchRecipeArtifactError,
    find_research_recipe_compilations_for_manifest,
)
from qap.portfolio import AssetId
from qap.product_pair_study import ProductPairStudyError
from qap.research_recipe_capabilities import (
    CAPABILITY_CATALOG,
    CAPABILITY_CATALOG_VERSION,
)
from qap.research_recipe_entry import ResearchRecipeService
from qap.research_recipe_product import (
    DEFAULT_PRODUCT_RECIPE_VERSION,
    ProductRecipeDraftUnavailable,
    default_product_recipe_draft,
)
from qap.scanner.protocol import ScannerHorizon

router = APIRouter(prefix="/api/research-recipes", tags=["research-recipes"])


def _owner(request: Request) -> ResearchRecipeService:
    owner = cast(object, request.app.state.research_recipe_service)
    if not isinstance(owner, ResearchRecipeService):
        raise RuntimeError("Research recipe service is not configured")
    return owner


@router.get(
    "/product-context",
    response_model=ResearchRecipeProductContextDto,
    operation_id="getResearchRecipeProductContext",
)
def research_recipe_product_context(
    request: Request,
    research_object: Literal["pair", "fixed_basket"] = "pair",
    horizon: Literal["short", "medium", "swing"] | None = None,
    asset: list[str] = Query(default=[]),
    orientation: str | None = Query(default=None, min_length=3),
    venue: Literal["binance", "gate"] | None = Query(default=None),
) -> ResearchRecipeProductContextDto:
    draft = None
    issue = None
    if horizon is not None and asset:
        try:
            assets = tuple(AssetId(item).key for item in asset)
            pair_context = None
            if research_object == "pair" and len(assets) == 2:
                requested = requested_pair_orientation(
                    asset_x=assets[0],
                    asset_y=assets[1],
                    orientation=orientation,
                )
                try:
                    pair_context = _owner(request).pair_study.context(
                        asset_a=AssetId(assets[0]),
                        asset_b=AssetId(assets[1]),
                        orientation=requested,
                        horizon=ScannerHorizon(horizon),
                        venue=venue,
                    )
                except ProductPairStudyError as exc:
                    issue = ResearchRecipeProductIssueDto(
                        code=SupportReasonCode.REQUIRES_MARKET_DATA,
                        component="pair_study",
                        detail=str(exc),
                    )
            if issue is None:
                draft = default_product_recipe_draft(
                    _owner(request),
                    research_object=ResearchObject(research_object),
                    assets=assets,
                    horizon=ScannerHorizon(horizon),
                    pair_study_context=pair_context,
                )
        except ProductRecipeDraftUnavailable as exc:
            issue = ResearchRecipeProductIssueDto(
                code=exc.issue.code,
                component=exc.issue.component,
                detail=exc.issue.detail,
            )
        except ValueError as exc:
            raise ApiBoundaryError(
                code="research_recipe_product_selection_invalid",
                message=str(exc),
                status_code=422,
                context={},
            ) from exc
    return ResearchRecipeProductContextDto(
        capability_catalog_version=CAPABILITY_CATALOG_VERSION,
        default_recipe_version=DEFAULT_PRODUCT_RECIPE_VERSION,
        capabilities=CAPABILITY_CATALOG,
        default_draft=draft,
        default_issue=issue,
    )


@router.get(
    "/runs/{run_id}/lineage",
    response_model=ResearchRecipeRunLineageDto,
    operation_id="getResearchRecipeRunLineage",
)
def research_recipe_run_lineage(
    run_id: str,
    request: Request,
) -> ResearchRecipeRunLineageDto:
    owner = _owner(request)
    run_root = owner.run_root.resolve()
    run_directory = (run_root / run_id).resolve()
    try:
        run_directory.relative_to(run_root)
    except ValueError as exc:
        raise ApiBoundaryError(
            code="research_recipe_run_unavailable",
            message="The requested QAP run is unavailable or invalid.",
            status_code=404,
            context={"run_id": run_id},
        ) from exc
    if run_directory.parent != run_root or run_directory.name != run_id:
        raise ApiBoundaryError(
            code="research_recipe_run_unavailable",
            message="The requested QAP run is unavailable or invalid.",
            status_code=404,
            context={"run_id": run_id},
        )
    try:
        loaded = read_run_artifacts(run_directory)
    except ArtifactError as exc:
        raise ApiBoundaryError(
            code="research_recipe_run_unavailable",
            message="The requested QAP run is unavailable or invalid.",
            status_code=404,
            context={"run_id": run_id},
        ) from exc
    exact_manifest_sha256 = manifest_sha256(loaded.manifest)
    try:
        stored = find_research_recipe_compilations_for_manifest(
            owner.run_root,
            research_family_id=loaded.manifest.research_family_id,
            exact_manifest_sha256=exact_manifest_sha256,
        )
    except ResearchRecipeArtifactError as exc:
        raise ApiBoundaryError(
            code="research_recipe_lineage_invalid",
            message="Research recipe lineage could not be integrity-verified.",
            status_code=409,
            context={"run_id": run_id},
        ) from exc
    return ResearchRecipeRunLineageDto(
        run_id=run_id,
        research_family_id=loaded.manifest.research_family_id,
        manifest_sha256=exact_manifest_sha256,
        matches=tuple(
            ResearchRecipeLineageMatchDto(
                recipe=item.recipe,
                compilation=item.compilation,
            )
            for item in stored
        ),
    )


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
