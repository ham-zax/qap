"""Read-only descriptive pair and anchor-lens routes."""

from typing import cast

from fastapi import APIRouter, Query, Request

from qap.api.readers import RunArtifactReader
from qap.api.schemas import AnchorLensDto, PairSeriesDto

router = APIRouter(prefix="/api/pairs", tags=["pairs"])


def _reader(request: Request) -> RunArtifactReader:
    reader = cast(object, request.app.state.run_reader)
    if not isinstance(reader, RunArtifactReader):
        raise RuntimeError("run artifact reader is not configured")
    return reader


@router.get(
    "/{asset_x}/{asset_y}/series",
    response_model=PairSeriesDto,
    operation_id="getPairSeries",
)
def pair_series(
    asset_x: str,
    asset_y: str,
    request: Request,
    run_id: str = Query(min_length=1),
    orientation: str | None = Query(default=None, min_length=3),
) -> PairSeriesDto:
    return _reader(request).pair_series(
        run_id=run_id,
        asset_x=asset_x,
        asset_y=asset_y,
        orientation=orientation,
    )


@router.get(
    "/{asset_x}/{asset_y}/anchor",
    response_model=AnchorLensDto,
    operation_id="getAnchorLens",
)
def anchor_lens(
    asset_x: str,
    asset_y: str,
    request: Request,
    run_id: str = Query(min_length=1),
    anchor: str = Query(min_length=1),
    orientation: str | None = Query(default=None, min_length=3),
) -> AnchorLensDto:
    return _reader(request).anchor_lens(
        run_id=run_id,
        asset_x=asset_x,
        asset_y=asset_y,
        anchor=anchor,
        orientation=orientation,
    )


__all__ = ["router"]
