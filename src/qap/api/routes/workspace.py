"""Product workspace identity and bounded local readiness status."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Request

from qap.api.schemas import WorkspaceStatusDto
from qap.api.settings import ApiSettings
from qap.product_market_data import ProductMarketData

router = APIRouter(tags=["workspace"])


def _market_data_status(
    settings: ApiSettings,
) -> tuple[Literal["not_prepared", "catalog_detected"], datetime | None]:
    if settings.market_data_root is None:
        return "not_prepared", None

    catalog_path = settings.market_data_root / "catalog.json"
    if not catalog_path.is_file():
        return "not_prepared", None

    updated_at = datetime.fromtimestamp(catalog_path.stat().st_mtime, tz=timezone.utc)
    return "catalog_detected", updated_at


@router.get(
    "/api/workspace",
    response_model=WorkspaceStatusDto,
    operation_id="getWorkspaceStatus",
)
def workspace_status(request: Request) -> WorkspaceStatusDto:
    settings: ApiSettings = request.app.state.settings
    market_data_status, catalog_updated_at = _market_data_status(settings)
    product_market_data: ProductMarketData = request.app.state.product_market_data
    return WorkspaceStatusDto(
        workspace_mode=settings.workspace_mode,
        workspace_root=str(settings.run_root),
        market_data_status=market_data_status,
        market_data_catalog_updated_at=catalog_updated_at,
        product_maintenance_status=product_market_data.maintenance_state().status,
    )


__all__ = ["router"]
