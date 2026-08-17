"""Read-only portfolio projections from immutable experiment artifacts."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.readers import RunArtifactReader
from qap.api.schemas import PortfolioPerformanceDto, PortfolioSnapshotDto

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


def _reader(request: Request) -> RunArtifactReader:
    reader = cast(object, request.app.state.run_reader)
    if not isinstance(reader, RunArtifactReader):
        raise RuntimeError("run artifact reader is not configured")
    return reader


@router.get(
    "/{run_id}",
    response_model=PortfolioSnapshotDto,
    operation_id="getPortfolio",
)
def portfolio(run_id: str, request: Request) -> PortfolioSnapshotDto:
    return _reader(request).portfolio_snapshot(run_id)


@router.get(
    "/{run_id}/performance",
    response_model=PortfolioPerformanceDto,
    operation_id="getPortfolioPerformance",
)
def portfolio_performance(run_id: str, request: Request) -> PortfolioPerformanceDto:
    return _reader(request).portfolio_performance(run_id)


__all__ = ["router"]
