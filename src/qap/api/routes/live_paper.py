"""Actor-scoped forward L2 paper sessions: create, step, read, list, stop."""

from collections.abc import Callable
from typing import Literal, cast

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
from qap.experiment.live_paper_candles import CandleInputs
from qap.experiment.live_paper_execution import BookProvider, window_book_provider
from qap.experiment.live_paper_runner import (
    LivePaperError,
    LivePaperSessionManager,
    LivePaperSessionNotFoundError,
)
from qap.market.binance_ws_stream import BinanceWsStreamError
from qap.product_paper_inputs import PaperInputError, resolve_paper_inputs

router = APIRouter(prefix="/api/pair-rotation", tags=["pair-rotation"])

PaperInputsProvider = Callable[..., CandleInputs]


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


def _resolve_inputs(
    request: Request,
    *,
    coin_a: str,
    coin_b: str,
    anchor: str | None,
    anchor_mode: Literal["auto", "none", "explicit"],
    bar: str,
) -> CandleInputs:
    settings = cast(ApiSettings, request.app.state.settings)
    injected = cast(
        PaperInputsProvider | None,
        getattr(request.app.state, "paper_inputs_provider", None),
    )
    if injected is not None:
        return injected(
            coin_a=coin_a,
            coin_b=coin_b,
            anchor=anchor,
            anchor_mode=anchor_mode,
            bar=bar,
        )
    return resolve_paper_inputs(
        settings.run_root,
        settings.market_data_root,
        coin_a=coin_a,
        coin_b=coin_b,
        anchor=anchor,
        anchor_mode=anchor_mode,
        bar=bar,
        require_metadata=True,
    )


def _boundary(
    exc: LivePaperError | PaperInputError | BinanceWsStreamError,
) -> ApiBoundaryError:
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
    if command.anchor == "none":
        req_anchor: str | None = None
        anchor_mode: Literal["auto", "none", "explicit"] = "none"
    elif command.anchor is None:
        req_anchor = None
        anchor_mode = "auto"
    else:
        req_anchor = command.anchor
        anchor_mode = "explicit"

    try:
        candle_inputs = _resolve_inputs(
            request,
            coin_a=command.coin_a,
            coin_b=command.coin_b,
            anchor=req_anchor,
            anchor_mode=anchor_mode,
            bar=command.bar,
        )
        pinned_anchor = (
            None
            if anchor_mode == "none"
            else (
                candle_inputs.resolved_anchor if anchor_mode == "auto" else req_anchor
            )
        )
        persisted_mode = "none" if pinned_anchor is None else "pinned"
        view = _manager(request).create_session(
            command.coin_a,
            command.coin_b,
            anchor=pinned_anchor,
            anchor_mode=persisted_mode,
            bar=command.bar,
            settings=command.settings,
            order_rtt_ms=command.order_rtt_ms,
            max_staleness_ms=command.max_staleness_ms,
            candle_inputs=candle_inputs,
            require_metadata=True,
        )
        return LivePaperSessionDto.model_validate(view)
    except (LivePaperError, PaperInputError, BinanceWsStreamError) as exc:
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
        manager = _manager(request, duration_seconds=window)
        coin_a, coin_b, pinned_anchor, raw_mode, bar = manager.read_session_raw_anchor(
            session_id
        )
        step_mode: Literal["auto", "none", "explicit"] = (
            "none" if raw_mode == "none" or pinned_anchor is None else "explicit"
        )
        candle_inputs = _resolve_inputs(
            request,
            coin_a=coin_a,
            coin_b=coin_b,
            anchor=pinned_anchor,
            anchor_mode=step_mode,
            bar=bar,
        )
        view = manager.step_session(
            session_id,
            candle_inputs=candle_inputs,
            require_metadata=True,
        )
        return LivePaperSessionDto.model_validate(view)
    except (LivePaperError, PaperInputError, BinanceWsStreamError) as exc:
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
