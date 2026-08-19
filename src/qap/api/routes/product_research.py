"""Current-approved Product research readiness and initiation routes."""

from datetime import UTC, datetime
from typing import Literal, cast

from fastapi import APIRouter, Request
from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.product_research_schemas import (
    CurrentApprovedReadinessDto,
    CurrentApprovedResearchRequestDto,
    DirectMarketReadinessDto,
    GenerationBindingDto,
    ProductRunScanRequestDto,
    ReadinessReasonDto,
    ResearchAssetReadinessDto,
    ResearchPathReadinessDto,
)
from qap.api.product_schemas import MarketDataMaintenanceDto
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import FreezeForwardCohortRequestDto, OperationRefDto
from qap.api.scanner_views import ScannerArtifactReader
from qap.api.settings import ApiSettings
from qap.product_current_approved import (
    CurrentApprovedReadiness,
    CurrentApprovedResearch,
    CurrentApprovedResearchError,
)
from qap.product_current_approved_models import GenerationBinding, ReadinessReason
from qap.product_market_data import ProductMarketDataError
from qap.product_universe import ProductUniverseError
from qap.scanner.protocol import ScannerHorizon

router = APIRouter(prefix="/api/product-research", tags=["product-research"])


def _owner(request: Request) -> CurrentApprovedResearch:
    owner = cast(object, request.app.state.current_approved_research)
    if not isinstance(owner, CurrentApprovedResearch):
        raise RuntimeError("Current-approved Product research is not configured")
    return owner


def _settings(request: Request) -> ApiSettings:
    settings = cast(object, request.app.state.settings)
    if not isinstance(settings, ApiSettings):
        raise RuntimeError("API settings are not configured")
    return settings


def _scanner_reader(request: Request) -> ScannerArtifactReader:
    reader = cast(object, request.app.state.scanner_reader)
    if not isinstance(reader, ScannerArtifactReader):
        raise RuntimeError("Scanner artifact reader is not configured")
    return reader


def _require_local_market(request: Request) -> None:
    if _settings(request).workspace_mode != "local_market":
        raise ApiBoundaryError(
            code="product_research_read_only",
            message="Current-approved research is available only in Local Market.",
            status_code=409,
            context={},
        )


def _dto(value: CurrentApprovedReadiness) -> CurrentApprovedReadinessDto:
    def reason(item: ReadinessReason) -> ReadinessReasonDto:
        return ReadinessReasonDto(
            code=item.code,
            detail=item.detail,
            blocking=item.blocking,
        )

    def generations(
        items: tuple[GenerationBinding, ...],
    ) -> tuple[GenerationBindingDto, ...]:
        return tuple(
            GenerationBindingDto(
                dataset_id=item.dataset_id,
                semantic_fingerprint=item.semantic_fingerprint,
                interval=item.interval,
            )
            for item in items
        )

    assets = tuple(
        ResearchAssetReadinessDto(
            canonical_asset_id=item.canonical_asset_id,
            approved=item.approved,
            identity_state=cast(
                Literal["resolved", "review_required"], item.identity_state
            ),
            ready=item.ready,
            reasons=tuple(reason(entry) for entry in item.reasons),
            paths=tuple(
                ResearchPathReadinessDto(
                    canonical_asset_id=path.canonical_asset_id,
                    venue=cast(Literal["binance", "gate"], path.venue),
                    venue_symbol=path.venue_symbol,
                    ready=path.ready,
                    data_through=path.data_through,
                    reasons=tuple(reason(entry) for entry in path.reasons),
                    generations=generations(path.generations),
                )
                for path in item.paths
            ),
        )
        for item in value.assets
    )
    direct = tuple(
        DirectMarketReadinessDto(
            venue=cast(Literal["binance", "gate"], item.venue),
            asset_a=item.asset_a,
            asset_b=item.asset_b,
            venue_symbol=item.venue_symbol,
            status=item.status,
            reasons=tuple(reason(entry) for entry in item.reasons),
            generations=generations(item.generations),
        )
        for item in value.direct_markets
    )
    maintenance = value.maintenance
    return CurrentApprovedReadinessDto(
        claim_id=value.claim_id,
        claim_label=value.claim_label,
        claim_identity=value.claim_identity,
        scanner_protocol_id=value.scanner_protocol_id,
        scanner_protocol_identity=value.scanner_protocol_identity,
        horizon=value.horizon.value,
        readiness_id=value.readiness_id,
        directory_id=value.directory_id,
        directory_observed_at=value.directory_observed_at,
        catalog_identity=value.catalog_identity,
        safe_cutoff=value.safe_cutoff,
        approved_asset_count=value.approved_asset_count,
        ready_asset_count=value.ready_asset_count,
        ready_path_count=value.ready_path_count,
        ready_venues=cast(tuple[Literal["binance", "gate"], ...], value.ready_venues),
        assets=assets,
        direct_markets=direct,
        maintenance=MarketDataMaintenanceDto(
            status=maintenance.status,
            kind=maintenance.kind,
            started_at=maintenance.started_at,
            finished_at=maintenance.finished_at,
            failure_reason=maintenance.failure_reason,
        ),
        reasons=tuple(reason(item) for item in value.reasons),
        ready_for_research=value.ready_for_research,
    )


def _readiness(request: Request, horizon: ScannerHorizon) -> CurrentApprovedReadiness:
    try:
        return _owner(request).readiness(horizon)
    except (
        CurrentApprovedResearchError,
        ProductMarketDataError,
        ProductUniverseError,
    ) as exc:
        raise ApiBoundaryError(
            code="product_research_state_invalid",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc


@router.get(
    "/readiness",
    response_model=CurrentApprovedReadinessDto,
    operation_id="getCurrentApprovedResearchReadiness",
)
def current_approved_readiness(
    horizon: Literal["short", "medium", "swing"],
    request: Request,
) -> CurrentApprovedReadinessDto:
    _require_local_market(request)
    return _dto(_readiness(request, ScannerHorizon(horizon)))


@router.post(
    "",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="runCurrentApprovedResearch",
)
def run_current_approved_research(
    command: CurrentApprovedResearchRequestDto,
    request: Request,
) -> OperationRefDto:
    _require_local_market(request)
    horizon = ScannerHorizon(command.horizon)
    current = _readiness(request, horizon)
    if current.readiness_id != command.readiness_id:
        raise ApiBoundaryError(
            code="product_research_readiness_stale",
            message=(
                "Research scope or market-data generations changed; refresh readiness."
            ),
            status_code=409,
            context={"current_readiness_id": current.readiness_id},
        )
    if not current.ready_for_research:
        raise ApiBoundaryError(
            code="product_research_not_ready",
            message="The current approved scope is not ready for this timeframe.",
            status_code=409,
            context={"readiness_id": current.readiness_id},
        )
    worker_request = ProductRunScanRequestDto(
        horizon=command.horizon,
        readiness_id=command.readiness_id,
    )
    payload = cast(dict[str, JsonValue], worker_request.model_dump(mode="json"))
    return operation_manager(request).submit(OperationKind.RUN_SCAN, payload)


@router.post(
    "/{scan_id}/follow-up",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="startCurrentApprovedResearchFollowUp",
)
def start_current_approved_follow_up(
    scan_id: str,
    request: Request,
) -> OperationRefDto:
    _require_local_market(request)
    detail = _scanner_reader(request).scan_detail(scan_id)
    follow_up = detail.product_follow_up
    if follow_up is None:
        raise ApiBoundaryError(
            code="product_follow_up_claim_invalid",
            message=(
                "Follow-up is available only for completed current-approved research."
            ),
            status_code=409,
            context={"scan_id": scan_id},
        )
    if follow_up.state == "existing" and follow_up.cohort_id is not None:
        raise ApiBoundaryError(
            code="product_follow_up_exists",
            message="Follow-up already exists for this research generation.",
            status_code=409,
            context={"cohort_id": follow_up.cohort_id},
        )
    if follow_up.state != "start_available" or follow_up.horizon is None:
        raise ApiBoundaryError(
            code="product_follow_up_unavailable",
            message=follow_up.reason
            or "Follow-up is unavailable for this research generation.",
            status_code=409,
            context={"scan_id": scan_id},
        )
    command = FreezeForwardCohortRequestDto(
        scan_id=detail.summary.scan_id,
        horizon=cast(Literal["short", "medium", "swing"], follow_up.horizon),
        freeze_at=datetime.now(UTC),
    )
    payload = cast(dict[str, JsonValue], command.model_dump(mode="json"))
    return operation_manager(request).submit(
        OperationKind.FREEZE_FORWARD_COHORT,
        payload,
    )


__all__ = ["router"]
