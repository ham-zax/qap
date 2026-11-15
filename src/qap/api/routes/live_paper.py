"""Actor-scoped forward L2 paper sessions: create, step, read, list, stop."""

from typing import cast

from fastapi import APIRouter, Query, Request

from qap.api.errors import ApiBoundaryError
from qap.api.live_paper_schemas import (
    LivePaperCreateDto,
    LivePaperSessionDto,
    LivePaperSessionListDto,
    LivePaperStepDto,
)
from qap.api.routes.pair_rotation import require_local
from qap.api.settings import ApiSettings
from qap.experiment.live_paper_execution import BookProvider, window_book_provider
from qap.experiment.live_paper_runner import (
    LivePaperError,
    LivePaperSessionManager,
    LivePaperSessionNotFoundError,
)
from qap.market.binance_ws_stream import BinanceWsStreamError

router = APIRouter(prefix="/api/pair-rotation", tags=["pair-rotation"])


def _manager(
    request: Request, *, duration_seconds: float | None = None
) -> LivePaperSessionManager:
    settings = cast(ApiSettings, request.app.state.settings)
    provider = cast(
        BookProvider | None, getattr(request.app.state, "paper_book_provider", None)
    )
    if provider is None and duration_seconds is not None:
        provider = window_book_provider(duration_seconds)
    return LivePaperSessionManager(
        settings.run_root,
        actor_id=request.headers.get("X-QAP-Actor-Id") or "local",
        book_provider=provider,
    )


def _boundary(exc: LivePaperError | BinanceWsStreamError) -> ApiBoundaryError:
    missing = isinstance(exc, LivePaperSessionNotFoundError)
    return ApiBoundaryError(
        code="live_paper_session_not_found" if missing else "live_paper_unavailable",
        message=str(exc),
        status_code=404 if missing else 409,
        context={},
    )


@router.post(
    "/paper-sessions",
    response_model=LivePaperSessionDto,
    operation_id="createLivePaperSession",
)
def create_paper_session(
    command: LivePaperCreateDto, request: Request
) -> LivePaperSessionDto:
    require_local(request)
    try:
        view = _manager(request).create_session(
            command.coin_a,
            command.coin_b,
            anchor=command.anchor,
            bar=command.bar,
            settings=command.settings,
            order_rtt_ms=command.order_rtt_ms,
            max_staleness_ms=command.max_staleness_ms,
        )
        return LivePaperSessionDto.model_validate(view)
    except (LivePaperError, BinanceWsStreamError) as exc:
        raise _boundary(exc) from exc


@router.get(
    "/paper-sessions",
    response_model=LivePaperSessionListDto,
    operation_id="listLivePaperSessions",
)
def list_paper_sessions(
    request: Request,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LivePaperSessionListDto:
    try:
        rows = _manager(request).list_sessions(limit=limit, offset=offset)
        return LivePaperSessionListDto.model_validate(
            {
                "sessions": rows,
                "next_offset": offset + limit if len(rows) == limit else None,
            }
        )
    except LivePaperError as exc:
        raise _boundary(exc) from exc


@router.get(
    "/paper-sessions/{session_id}",
    response_model=LivePaperSessionDto,
    operation_id="getLivePaperSession",
)
def read_paper_session(session_id: str, request: Request) -> LivePaperSessionDto:
    try:
        return LivePaperSessionDto.model_validate(
            _manager(request).read_session(session_id)
        )
    except LivePaperError as exc:
        raise _boundary(exc) from exc


@router.post(
    "/paper-sessions/{session_id}/step",
    response_model=LivePaperSessionDto,
    operation_id="stepLivePaperSession",
)
def step_paper_session(
    session_id: str, request: Request, command: LivePaperStepDto | None = None
) -> LivePaperSessionDto:
    require_local(request)
    window = (command or LivePaperStepDto()).duration_seconds
    try:
        view = _manager(request, duration_seconds=window).step_session(session_id)
        return LivePaperSessionDto.model_validate(view)
    except (LivePaperError, BinanceWsStreamError) as exc:
        raise _boundary(exc) from exc


@router.post(
    "/paper-sessions/{session_id}/stop",
    response_model=LivePaperSessionDto,
    operation_id="stopLivePaperSession",
)
def stop_paper_session(session_id: str, request: Request) -> LivePaperSessionDto:
    require_local(request)
    try:
        return LivePaperSessionDto.model_validate(
            _manager(request).stop_session(session_id)
        )
    except LivePaperError as exc:
        raise _boundary(exc) from exc
