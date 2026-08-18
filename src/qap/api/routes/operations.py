"""Read-only operation lifecycle routes."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.operations import OperationManager
from qap.api.scanner_schemas import OperationDto, OperationListDto

router = APIRouter(prefix="/api/operations", tags=["operations"])


def operation_manager(request: Request) -> OperationManager:
    manager = cast(object, request.app.state.operation_manager)
    if not isinstance(manager, OperationManager):
        raise RuntimeError("operation manager is not configured")
    return manager


@router.get("", response_model=OperationListDto, operation_id="listOperations")
def list_operations(request: Request) -> OperationListDto:
    return operation_manager(request).list()


@router.get(
    "/{operation_id}",
    response_model=OperationDto,
    operation_id="getOperation",
)
def operation_detail(operation_id: str, request: Request) -> OperationDto:
    return operation_manager(request).get(operation_id)


__all__ = ["operation_manager", "router"]
