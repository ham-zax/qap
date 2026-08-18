"""Read-only terminal basket evidence routes."""

from typing import cast

from fastapi import APIRouter, Request
from pydantic import JsonValue

from qap.api.basket_schemas import BasketDetailDto, BasketListDto, BasketRunRequestDto
from qap.api.basket_views import BasketArtifactReader
from qap.api.operations import OperationKind
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import OperationRefDto

router = APIRouter(tags=["baskets"])


def _reader(request: Request) -> BasketArtifactReader:
    reader = cast(object, request.app.state.basket_reader)
    if not isinstance(reader, BasketArtifactReader):
        raise RuntimeError("basket artifact reader is not configured")
    return reader


@router.get("/api/baskets", response_model=BasketListDto, operation_id="listBaskets")
def list_baskets(request: Request) -> BasketListDto:
    return _reader(request).list_baskets()


@router.get(
    "/api/baskets/{basket_id}",
    response_model=BasketDetailDto,
    operation_id="getBasket",
)
def basket_detail(basket_id: str, request: Request) -> BasketDetailDto:
    return _reader(request).basket_detail(basket_id)


@router.post(
    "/api/basket-runs",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="runBasket",
)
def run_basket(command: BasketRunRequestDto, request: Request) -> OperationRefDto:
    payload = cast(dict[str, JsonValue], command.model_dump(mode="json"))
    return operation_manager(request).submit(OperationKind.RUN_BASKET, payload)


__all__ = ["router"]
