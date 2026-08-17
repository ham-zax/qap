"""Read-only experiment artifact routes."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.readers import RunArtifactReader
from qap.api.schemas import ExperimentDetailDto, ExperimentListDto

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def _reader(request: Request) -> RunArtifactReader:
    reader = cast(object, request.app.state.run_reader)
    if not isinstance(reader, RunArtifactReader):
        raise RuntimeError("run artifact reader is not configured")
    return reader


@router.get("", response_model=ExperimentListDto, operation_id="listExperiments")
def list_experiments(request: Request) -> ExperimentListDto:
    return _reader(request).list_experiments()


@router.get(
    "/{run_id}",
    response_model=ExperimentDetailDto,
    operation_id="getExperiment",
)
def experiment_detail(run_id: str, request: Request) -> ExperimentDetailDto:
    return _reader(request).experiment_detail(run_id)


__all__ = ["router"]
