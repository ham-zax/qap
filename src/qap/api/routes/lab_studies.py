"""Explicit Lab study writes and immutable saved-result queries."""

from pathlib import Path
from typing import cast

from fastapi import APIRouter, Query, Request

from qap.api.errors import ApiBoundaryError
from qap.api.lab_study_schemas import (
    LabPinDto,
    LabSavedListDto,
    LabStudyDto,
    LabStudyRequestDto,
)
from qap.api.routes.pair_rotation import require_local, universe
from qap.api.settings import ApiSettings
from qap.product_lab_store import LabStoreError, LabStudyStore
from qap.product_lab_study import LabStudyService
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_generation import ProductGenerationReadError
from qap.product_pair_rotation_analysis import PairAnalysisError
from qap.product_universe import ProductUniverseError

router = APIRouter(prefix="/api/pair-rotation", tags=["pair-rotation"])


def _store(request: Request) -> LabStudyStore:
    settings = cast(ApiSettings, request.app.state.settings)
    return LabStudyStore(settings.run_root)


@router.post("/studies", response_model=LabStudyDto, operation_id="computeLabStudy")
def compute_study(command: LabStudyRequestDto, request: Request) -> LabStudyDto:
    require_local(request)
    settings = cast(ApiSettings, request.app.state.settings)
    if settings.market_data_root is None:
        raise ApiBoundaryError(
            code="lab_study_unavailable",
            message="Market data is not configured.",
            status_code=409,
            context={},
        )
    try:
        service = LabStudyService(
            universe(request),
            cast(ProductMarketData, request.app.state.product_market_data),
            settings.market_data_root,
            settings.run_root,
            settings.repository_root or Path(__file__).resolve().parents[4],
        )
        result = service.run(
            command.coin_a,
            command.coin_b,
            bar=command.bar,
            days=int(command.days),
            band_lookback=command.band_lookback,
            anchor=command.anchor,
            settings=command.settings,
        )
        return LabStudyDto.model_validate(result)
    except (
        PairAnalysisError,
        ProductUniverseError,
        ProductMarketDataError,
        ProductGenerationReadError,
        LabStoreError,
    ) as exc:
        raise ApiBoundaryError(
            code="lab_study_unavailable", message=str(exc), status_code=409, context={}
        ) from exc


@router.get(
    "/studies", response_model=LabSavedListDto, operation_id="listSavedLabStudies"
)
def list_studies(
    request: Request,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LabSavedListDto:
    try:
        rows = _store(request).list(limit=limit, offset=offset)
        return LabSavedListDto.model_validate(
            {
                "studies": rows,
                "next_offset": offset + limit if len(rows) == limit else None,
            }
        )
    except LabStoreError as exc:
        raise ApiBoundaryError(
            code="lab_saved_result_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.get(
    "/studies/{study_id}", response_model=LabStudyDto, operation_id="getSavedLabStudy"
)
def read_study(study_id: str, request: Request) -> LabStudyDto:
    try:
        return LabStudyDto.model_validate(_store(request).read(study_id))
    except LabStoreError as exc:
        raise ApiBoundaryError(
            code="lab_saved_result_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.post(
    "/studies/{study_id}/pin", response_model=LabStudyDto, operation_id="pinLabStudy"
)
def pin_study(study_id: str, command: LabPinDto, request: Request) -> LabStudyDto:
    require_local(request)
    try:
        return LabStudyDto.model_validate(
            _store(request).set_pin(study_id, command.pinned)
        )
    except LabStoreError as exc:
        raise ApiBoundaryError(
            code="lab_saved_result_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc
