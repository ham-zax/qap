"""Read-only Scanner-V1 discovery and prospective routes."""

from typing import cast

from fastapi import APIRouter, Request

from qap.api.scanner_schemas import (
    CandidateDetailDto,
    CandidateListDto,
    ForwardCohortDetailDto,
    ForwardCohortListDto,
    ScanDetailDto,
    ScanListDto,
    ScannerProtocolDto,
)
from qap.api.scanner_views import ScannerArtifactReader

router = APIRouter(tags=["scanner"])


def _reader(request: Request) -> ScannerArtifactReader:
    reader = cast(object, request.app.state.scanner_reader)
    if not isinstance(reader, ScannerArtifactReader):
        raise RuntimeError("scanner artifact reader is not configured")
    return reader


@router.get(
    "/api/scanner/protocol",
    response_model=ScannerProtocolDto,
    operation_id="getScannerProtocol",
)
def scanner_protocol(request: Request) -> ScannerProtocolDto:
    return _reader(request).protocol()


@router.get("/api/scans", response_model=ScanListDto, operation_id="listScans")
def list_scans(request: Request) -> ScanListDto:
    return _reader(request).list_scans()


@router.get(
    "/api/scans/{scan_id}",
    response_model=ScanDetailDto,
    operation_id="getScan",
)
def scan_detail(scan_id: str, request: Request) -> ScanDetailDto:
    return _reader(request).scan_detail(scan_id)


@router.get(
    "/api/scans/{scan_id}/candidates",
    response_model=CandidateListDto,
    operation_id="listScanCandidates",
)
def list_candidates(scan_id: str, request: Request) -> CandidateListDto:
    return _reader(request).list_candidates(scan_id)


@router.get(
    "/api/scans/{scan_id}/candidates/{candidate_id}",
    response_model=CandidateDetailDto,
    operation_id="getScanCandidate",
)
def candidate_detail(
    scan_id: str,
    candidate_id: str,
    request: Request,
) -> CandidateDetailDto:
    return _reader(request).candidate_detail(scan_id, candidate_id)


@router.get(
    "/api/forward/cohorts",
    response_model=ForwardCohortListDto,
    operation_id="listForwardCohorts",
)
def list_forward_cohorts(request: Request) -> ForwardCohortListDto:
    return _reader(request).list_forward_cohorts()


@router.get(
    "/api/forward/cohorts/{cohort_id}",
    response_model=ForwardCohortDetailDto,
    operation_id="getForwardCohort",
)
def forward_cohort_detail(
    cohort_id: str,
    request: Request,
) -> ForwardCohortDetailDto:
    return _reader(request).forward_cohort_detail(cohort_id)


__all__ = ["router"]
