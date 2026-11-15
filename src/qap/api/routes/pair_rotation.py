"""Admission-free spot research discovery and background data preparation."""

from typing import Literal, cast

from fastapi import APIRouter, Query, Request
from pydantic import ValidationError

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.pair_rotation_analysis_schemas import AnalysisDays, LabAnalysisDto
from qap.api.pair_rotation_schemas import CoinSearchDto, PairRotationRequestDto
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import OperationRefDto
from qap.api.settings import ApiSettings
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_generation import ProductGenerationReadError
from qap.product_pair_rotation_analysis import PairAnalysisError, PairRotationAnalysis
from qap.product_universe import ProductUniverse, ProductUniverseError

router = APIRouter(prefix="/api/pair-rotation", tags=["pair-rotation"])


def universe(request: Request) -> ProductUniverse:
    owner = cast(ProductUniverse, request.app.state.product_universe)
    return owner


def require_local(request: Request) -> None:
    settings = cast(ApiSettings, request.app.state.settings)
    if settings.workspace_mode != "local_market":
        raise ApiBoundaryError(
            code="pair_rotation_read_only",
            message="Pair data preparation requires a Local Market workspace.",
            status_code=409,
            context={},
        )


@router.get(
    "/analysis", response_model=LabAnalysisDto, operation_id="analyzePairRotation"
)
def analyze_pair_rotation(
    request: Request,
    coin_a: str = Query(min_length=1, max_length=100),
    coin_b: str = Query(min_length=1, max_length=100),
    bar: Literal["1m", "15m", "1h", "4h", "1d"] = "15m",
    days: AnalysisDays = AnalysisDays.half_year,
    band_lookback: int = Query(default=672, ge=2, le=10000),
    anchor: str | None = Query(default=None, min_length=1, max_length=100),
) -> LabAnalysisDto:
    require_local(request)
    settings = cast(ApiSettings, request.app.state.settings)
    if settings.market_data_root is None:
        raise ApiBoundaryError(
            code="pair_rotation_analysis_unavailable",
            message="Market data root is not configured.",
            status_code=409,
            context={},
        )
    try:
        command = PairRotationRequestDto(coin_a=coin_a, coin_b=coin_b)
    except ValidationError as exc:
        raise ApiBoundaryError(
            code="pair_rotation_invalid_request",
            message="Choose two distinct Binance listings.",
            status_code=422,
            context={},
        ) from exc
    try:
        owner = PairRotationAnalysis(
            universe(request),
            cast(ProductMarketData, request.app.state.product_market_data),
            settings.market_data_root,
        )
        return LabAnalysisDto.model_validate(
            owner.analyze(
                command.coin_a,
                command.coin_b,
                bar=bar,
                days=days,
                band_lookback=band_lookback,
                anchor=anchor,
            )
        )
    except (
        PairAnalysisError,
        ProductUniverseError,
        ProductMarketDataError,
        ProductGenerationReadError,
    ) as exc:
        raise ApiBoundaryError(
            code="pair_rotation_analysis_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.get("/coins", response_model=CoinSearchDto, operation_id="searchResearchCoins")
def search_research_coins(
    request: Request,
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=50, ge=1, le=1000),
    venue: Literal["binance", "gate"] | None = Query(default=None),
) -> CoinSearchDto:
    try:
        owner = universe(request)
        directory = owner.read_directory()
        snapshot = owner.registry_snapshot()
        # Search composes cached evidence and venue metadata, never the network.
        return CoinSearchDto(
            directory_status="not_refreshed" if directory is None else "observed",
            registry_status="unavailable" if snapshot is None else "cached",
            directory_observed_at=None if directory is None else directory.observed_at,
            registry_observed_at=None if snapshot is None else snapshot.observed_at,
            registry_attribution=None if snapshot is None else snapshot.attribution,
            coins=owner.search(q, limit=limit, venue=venue),
        )
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="coin_search_state_invalid",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.post(
    "/bootstrap",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="refreshResearchCoins",
)
def refresh_research_coins(request: Request) -> OperationRefDto:
    require_local(request)
    return operation_manager(request).submit(OperationKind.REFRESH_COIN_DIRECTORY, {})


@router.post(
    "/open",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="openPairRotationData",
)
def open_pair_rotation(
    command: PairRotationRequestDto, request: Request
) -> OperationRefDto:
    require_local(request)
    return operation_manager(request).submit(
        OperationKind.PREPARE_PAIR_ROTATION_DATA,
        {
            "coin_a": command.coin_a,
            "coin_b": command.coin_b,
            "lookback_days": command.lookback_days,
            "base_interval": command.base_interval,
            "include_execution": command.include_execution,
        },
    )
