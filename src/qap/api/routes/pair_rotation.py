"""Admission-free spot research discovery and background data preparation."""

from typing import cast

from fastapi import APIRouter, Query, Request

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.pair_rotation_schemas import CoinSearchDto, PairRotationRequestDto
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import OperationRefDto
from qap.api.settings import ApiSettings
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


@router.get("/coins", response_model=CoinSearchDto, operation_id="searchResearchCoins")
def search_research_coins(
    request: Request,
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
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
            coins=owner.search(q, limit=limit),
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
        },
    )
