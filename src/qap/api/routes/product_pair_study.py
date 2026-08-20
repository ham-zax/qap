"""Backend-owned Product Pair Study read routes."""

from dataclasses import asdict
from typing import Literal, cast

from fastapi import APIRouter, Query, Request

from qap.api.errors import ApiBoundaryError
from qap.api.product_pair_study_schemas import (
    ProductPairStudyContextDto,
    ProductPairStudySeriesDto,
)
from qap.api.relationship_views import requested_pair_orientation
from qap.portfolio import AssetId, PairOrientation
from qap.product_pair_study import ProductPairStudy, ProductPairStudyError
from qap.scanner.protocol import ScannerHorizon

router = APIRouter(prefix="/api/product-pair-study", tags=["product-pair-study"])


def _owner(request: Request) -> ProductPairStudy:
    owner = cast(object, request.app.state.product_pair_study)
    if not isinstance(owner, ProductPairStudy):
        raise RuntimeError("Product Pair Study is not configured")
    return owner


def _analysis_reference(value: str | None) -> AssetId | None:
    if value is None:
        return None
    try:
        return AssetId(value)
    except (TypeError, ValueError) as exc:
        raise ApiBoundaryError(
            code="invalid_pair_study_reference",
            message="Analysis reference must be a valid canonical asset identifier.",
            status_code=422,
            context={"analysis_reference": value},
        ) from exc


def _inputs(
    *,
    asset_a: str,
    asset_b: str,
    orientation: str | None,
) -> tuple[AssetId, AssetId, PairOrientation]:
    requested = requested_pair_orientation(
        asset_x=asset_a,
        asset_y=asset_b,
        orientation=orientation,
    )
    return AssetId(asset_a), AssetId(asset_b), requested


def _error(
    error: ProductPairStudyError,
    *,
    asset_a: str,
    asset_b: str,
    horizon: str,
) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="product_pair_study_unavailable",
        message=str(error),
        status_code=409,
        context={
            "asset_a": asset_a.strip().upper(),
            "asset_b": asset_b.strip().upper(),
            "horizon": horizon,
        },
    )


@router.get(
    "/context",
    response_model=ProductPairStudyContextDto,
    operation_id="getProductPairStudyContext",
)
def product_pair_study_context(
    request: Request,
    asset_a: str = Query(min_length=1),
    asset_b: str = Query(min_length=1),
    horizon: Literal["short", "medium", "swing"] = Query(),
    orientation: str | None = Query(default=None, min_length=3),
    venue: Literal["binance", "gate"] | None = Query(default=None),
    analysis_reference: str | None = Query(default=None, min_length=1),
) -> ProductPairStudyContextDto:
    left, right, requested = _inputs(
        asset_a=asset_a,
        asset_b=asset_b,
        orientation=orientation,
    )
    try:
        context = _owner(request).context(
            asset_a=left,
            asset_b=right,
            orientation=requested,
            horizon=ScannerHorizon(horizon),
            venue=venue,
            analysis_reference=_analysis_reference(analysis_reference),
        )
    except ProductPairStudyError as exc:
        raise _error(exc, asset_a=asset_a, asset_b=asset_b, horizon=horizon) from exc
    return ProductPairStudyContextDto.model_validate(asdict(context))


@router.get(
    "/series",
    response_model=ProductPairStudySeriesDto,
    operation_id="getProductPairStudySeries",
)
def product_pair_study_series(
    request: Request,
    asset_a: str = Query(min_length=1),
    asset_b: str = Query(min_length=1),
    horizon: Literal["short", "medium", "swing"] = Query(),
    orientation: str | None = Query(default=None, min_length=3),
    venue: Literal["binance", "gate"] | None = Query(default=None),
    analysis_reference: str | None = Query(default=None, min_length=1),
) -> ProductPairStudySeriesDto:
    left, right, requested = _inputs(
        asset_a=asset_a,
        asset_b=asset_b,
        orientation=orientation,
    )
    try:
        series = _owner(request).series(
            asset_a=left,
            asset_b=right,
            orientation=requested,
            horizon=ScannerHorizon(horizon),
            venue=venue,
            analysis_reference=_analysis_reference(analysis_reference),
        )
    except ProductPairStudyError as exc:
        raise _error(exc, asset_a=asset_a, asset_b=asset_b, horizon=horizon) from exc
    return ProductPairStudySeriesDto.model_validate(asdict(series))


__all__ = ["router"]
