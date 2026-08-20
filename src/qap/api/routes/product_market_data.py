"""Bounded Product market-data preparation and projection routes."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.errors import ApiBoundaryError
from qap.api.product_schemas import (
    MarketDataGenerationDto,
    MarketDataMaintenanceDto,
    MarketDataPreparationRequestDto,
    ProductMarketDataDto,
)
from qap.api.settings import ApiSettings
from qap.portfolio import AssetId
from qap.product_market_data import ProductMarketDataError
from qap.product_market_data_models import ProductMarketDataProjection
from qap.product_market_data_prepare import (
    ProductMarketDataPreparation,
    ProductMarketDataPreparationError,
)
from qap.product_universe import ProductUniverseError
from qap.scanner.protocol import ScannerHorizon

router = APIRouter(prefix="/api/product-market-data", tags=["product-market-data"])


def _owner(request: Request) -> ProductMarketDataPreparation:
    owner = cast(object, request.app.state.product_market_data_preparation)
    if not isinstance(owner, ProductMarketDataPreparation):
        raise RuntimeError("Product market-data preparation is not configured")
    return owner


def _settings(request: Request) -> ApiSettings:
    settings = cast(object, request.app.state.settings)
    if not isinstance(settings, ApiSettings):
        raise RuntimeError("API settings are not configured")
    return settings


def _require_local_market(request: Request) -> None:
    if _settings(request).workspace_mode != "local_market":
        raise ApiBoundaryError(
            code="product_market_data_read_only",
            message="Market-data preparation is available only in Local Market.",
            status_code=409,
            context={},
        )


def _dto(projection: ProductMarketDataProjection) -> ProductMarketDataDto:
    maintenance = projection.maintenance
    return ProductMarketDataDto(
        generations=tuple(
            MarketDataGenerationDto(
                dataset_id=item.dataset_id,
                relative_path=item.relative_path,
                venue=item.venue,
                venue_symbol=item.venue_symbol,
                base_asset=item.base_asset,
                quote_asset=item.quote_asset,
                interval=item.interval,
                semantic_fingerprint=item.semantic_fingerprint,
                coverage_start=item.coverage_start,
                coverage_end_exclusive=item.coverage_end_exclusive,
                provenance_status=item.provenance_status,
                provenance_relative_path=item.provenance_relative_path,
                issue=item.issue,
            )
            for item in projection.generations
        ),
        maintenance=MarketDataMaintenanceDto(
            status=maintenance.status,
            kind=maintenance.kind,
            started_at=maintenance.started_at,
            finished_at=maintenance.finished_at,
            failure_reason=maintenance.failure_reason,
        ),
    )


def _execute(
    command: MarketDataPreparationRequestDto,
    request: Request,
    *,
    refresh: bool,
) -> ProductMarketDataDto:
    _require_local_market(request)
    horizons = tuple(ScannerHorizon(value) for value in command.horizons)
    asset_ids = (
        None
        if command.asset_ids is None
        else tuple(AssetId(value) for value in command.asset_ids)
    )
    analysis_reference_ids = tuple(
        AssetId(value) for value in command.analysis_reference_ids
    )
    try:
        projection = (
            _owner(request).refresh(
                horizons,
                asset_ids=asset_ids,
                analysis_reference_ids=analysis_reference_ids,
            )
            if refresh
            else _owner(request).prepare(
                horizons,
                asset_ids=asset_ids,
                analysis_reference_ids=analysis_reference_ids,
            )
        )
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="product_market_data_scope_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc
    except ProductMarketDataError as exc:
        raise ApiBoundaryError(
            code="product_market_data_state_invalid",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc
    except ProductMarketDataPreparationError as exc:
        raise ApiBoundaryError(
            code="product_market_data_acquisition_failed",
            message=str(exc),
            status_code=502,
            context={},
        ) from exc
    return _dto(projection)


@router.get(
    "",
    response_model=ProductMarketDataDto,
    operation_id="getProductMarketData",
)
def get_product_market_data(request: Request) -> ProductMarketDataDto:
    try:
        return _dto(_owner(request).projection())
    except ProductMarketDataError as exc:
        raise ApiBoundaryError(
            code="product_market_data_state_invalid",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.post(
    "/prepare",
    response_model=ProductMarketDataDto,
    operation_id="prepareProductMarketData",
)
def prepare_product_market_data(
    command: MarketDataPreparationRequestDto,
    request: Request,
) -> ProductMarketDataDto:
    return _execute(command, request, refresh=False)


@router.post(
    "/refresh",
    response_model=ProductMarketDataDto,
    operation_id="refreshProductMarketData",
)
def refresh_product_market_data(
    command: MarketDataPreparationRequestDto,
    request: Request,
) -> ProductMarketDataDto:
    return _execute(command, request, refresh=True)


__all__ = ["router"]
