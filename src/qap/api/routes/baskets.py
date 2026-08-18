"""Read-only terminal basket evidence routes."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.basket_schemas import BasketDetailDto, BasketListDto
from qap.api.basket_views import BasketArtifactReader

router = APIRouter(prefix="/api/baskets", tags=["baskets"])


def _reader(request: Request) -> BasketArtifactReader:
    reader = cast(object, request.app.state.basket_reader)
    if not isinstance(reader, BasketArtifactReader):
        raise RuntimeError("basket artifact reader is not configured")
    return reader


@router.get("", response_model=BasketListDto, operation_id="listBaskets")
def list_baskets(request: Request) -> BasketListDto:
    return _reader(request).list_baskets()


@router.get(
    "/{basket_id}",
    response_model=BasketDetailDto,
    operation_id="getBasket",
)
def basket_detail(basket_id: str, request: Request) -> BasketDetailDto:
    return _reader(request).basket_detail(basket_id)


__all__ = ["router"]
