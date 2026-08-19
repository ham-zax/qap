"""Backend-composed longitudinal History route."""

from fastapi import APIRouter, Request

from qap.api.history_schemas import HistoryDto
from qap.api.history_views import HistoryReader

router = APIRouter(tags=["history"])


def _reader(request: Request) -> HistoryReader:
    reader = getattr(request.app.state, "history_reader", None)
    if not isinstance(reader, HistoryReader):
        raise RuntimeError("history reader is not configured")
    return reader


@router.get("/api/history", response_model=HistoryDto, operation_id="getHistory")
def history(request: Request) -> HistoryDto:
    return _reader(request).read()


__all__ = ["router"]
