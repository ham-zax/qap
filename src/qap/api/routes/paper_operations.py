"""Read-only forward-paper operation routes."""

from fastapi import APIRouter, Request

from qap.api.paper_operation_schemas import (
    PaperOperationDetailDto,
    PaperOperationSummaryDto,
)
from qap.api.paper_operation_views import PaperOperationReader

router = APIRouter(prefix="/api/paper-operations", tags=["paper-operations"])


def _reader(request: Request) -> PaperOperationReader:
    reader = getattr(request.app.state, "paper_operation_reader", None)
    if not isinstance(reader, PaperOperationReader):
        raise RuntimeError("paper operation reader is not configured")
    return reader


@router.get(
    "",
    response_model=list[PaperOperationSummaryDto],
    operation_id="listPaperOperations",
)
def list_paper_operations(request: Request) -> tuple[PaperOperationSummaryDto, ...]:
    return _reader(request).list()


@router.get(
    "/{operation_id}",
    response_model=PaperOperationDetailDto,
    operation_id="getPaperOperation",
)
def get_paper_operation(operation_id: str, request: Request) -> PaperOperationDetailDto:
    return _reader(request).detail(operation_id)


__all__ = ["router"]
