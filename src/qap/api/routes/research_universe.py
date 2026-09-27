"""Product Research Universe routes over workspace-scoped current state."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.errors import ApiBoundaryError
from qap.api.product_schemas import (
    AssetAdmissionRequestDto,
    DirectorySourceDto,
    IdentityMappingRequestDto,
    IdentityReviewDto,
    ResearchUniverseAssetDto,
    ResearchUniverseDto,
    ResearchUniverseVenueDto,
)
from qap.api.settings import ApiSettings
from qap.market.adapters.binance_public import BinancePublicDataError
from qap.market.adapters.gate_public import GatePublicDataError
from qap.product_universe import (
    ProductUniverse,
    ProductUniverseError,
    ResearchUniverseProjection,
    Venue,
)

router = APIRouter(prefix="/api/research-universe", tags=["research-universe"])


def _universe(request: Request) -> ProductUniverse:
    owner = cast(object, request.app.state.product_universe)
    if not isinstance(owner, ProductUniverse):
        raise RuntimeError("Product Research Universe is not configured")
    return owner


def _settings(request: Request) -> ApiSettings:
    settings = cast(object, request.app.state.settings)
    if not isinstance(settings, ApiSettings):
        raise RuntimeError("API settings are not configured")
    return settings


def _require_local_market(request: Request) -> None:
    if _settings(request).workspace_mode != "local_market":
        raise ApiBoundaryError(
            code="research_universe_read_only",
            message="Research Universe changes are available only in Local Market.",
            status_code=409,
            context={},
        )


def _projection(request: Request) -> ResearchUniverseProjection:
    try:
        return _universe(request).projection()
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="research_universe_state_invalid",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


def _dto(projection: ResearchUniverseProjection) -> ResearchUniverseDto:
    return ResearchUniverseDto(
        directory_status=(
            "not_refreshed" if projection.directory_id is None else "observed"
        ),
        directory_id=projection.directory_id,
        directory_observed_at=projection.directory_observed_at,
        sources=tuple(
            DirectorySourceDto(
                venue=source.venue,
                observed_at=source.observed_at,
                source_id=source.source_id,
                source_fingerprint=source.source_fingerprint,
            )
            for source in projection.sources
        ),
        assets=tuple(
            ResearchUniverseAssetDto(
                canonical_asset_id=item.asset.key,
                approved=item.approved,
                identity_state=item.identity_state,
                identity_reason=item.identity_reason,
                asset_identity_version=item.asset_identity_version,
                data_state=item.data_state,
                venues=tuple(
                    ResearchUniverseVenueDto(
                        venue=cast(Venue, venue.venue),
                        venue_symbol=venue.venue_symbol,
                        venue_asset_code=venue.venue_asset_code,
                        status=venue.status,
                        trading=venue.trading,
                    )
                    for venue in item.venues
                ),
            )
            for item in projection.assets
        ),
        identity_reviews=tuple(
            IdentityReviewDto(
                venue=cast(Venue, item.venue),
                venue_asset_code=item.venue_asset_code,
                venue_symbols=item.venue_symbols,
            )
            for item in projection.identity_reviews
        ),
    )


@router.get("", response_model=ResearchUniverseDto, operation_id="getResearchUniverse")
def get_research_universe(request: Request) -> ResearchUniverseDto:
    return _dto(_projection(request))


@router.post(
    "/directory-refresh",
    response_model=ResearchUniverseDto,
    operation_id="refreshResearchUniverseDirectory",
)
def refresh_directory(request: Request) -> ResearchUniverseDto:
    _require_local_market(request)
    try:
        _universe(request).refresh_directory()
    except (BinancePublicDataError, GatePublicDataError) as exc:
        raise ApiBoundaryError(
            code="market_directory_refresh_failed",
            message="Current public Spot markets could not be refreshed.",
            status_code=502,
            context={},
        ) from exc
    return _dto(_projection(request))


@router.post(
    "/identity-mappings",
    response_model=ResearchUniverseDto,
    operation_id="setResearchUniverseIdentityMapping",
)
def set_identity_mapping(
    command: IdentityMappingRequestDto,
    request: Request,
) -> ResearchUniverseDto:
    _require_local_market(request)
    try:
        _universe(request).set_identity_mapping(
            venue=command.venue,
            venue_asset_code=command.venue_asset_code,
            canonical_asset_id=command.canonical_asset_id,
            asset_identity_version=command.asset_identity_version,
        )
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="identity_mapping_rejected",
            message=str(exc),
            status_code=409,
            context={
                "venue": command.venue,
                "venue_asset_code": command.venue_asset_code,
            },
        ) from exc
    return _dto(_projection(request))


@router.post(
    "/admission",
    response_model=ResearchUniverseDto,
    operation_id="setResearchUniverseAdmission",
)
def set_asset_admission(
    command: AssetAdmissionRequestDto,
    request: Request,
) -> ResearchUniverseDto:
    _require_local_market(request)
    try:
        _universe(request).set_asset_admission(
            canonical_asset_id=command.canonical_asset_id,
            approved=command.approved,
        )
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="asset_admission_rejected",
            message=str(exc),
            status_code=409,
            context={"canonical_asset_id": command.canonical_asset_id},
        ) from exc
    return _dto(_projection(request))


__all__ = ["router"]
