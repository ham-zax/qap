"""Read-only Scanner-V1 discovery and prospective routes."""

from typing import cast

from fastapi import APIRouter, Request
from pydantic import JsonValue

from qap.api.operations import OperationKind
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import (
    AdvanceForwardCohortRequestDto,
    CandidateDetailDto,
    CandidateListDto,
    CapturePublicEvidenceRequestDto,
    ForwardCohortDetailDto,
    ForwardCohortListDto,
    FreezeForwardCohortRequestDto,
    MomentumGenerationRequestDto,
    OperationRefDto,
    QualificationRequestDto,
    RunScanRequestDto,
    ScanDetailDto,
    ScanListDto,
    ScannerProtocolDto,
)
from qap.api.scanner_views import ScannerArtifactReader
from qap.api.schemas import ApiDto

router = APIRouter(tags=["scanner"])


def _reader(request: Request) -> ScannerArtifactReader:
    reader = cast(object, request.app.state.scanner_reader)
    if not isinstance(reader, ScannerArtifactReader):
        raise RuntimeError("scanner artifact reader is not configured")
    return reader


def _payload(value: ApiDto) -> dict[str, JsonValue]:
    return cast(dict[str, JsonValue], value.model_dump(mode="json"))


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


@router.post(
    "/api/scans",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="runScan",
)
def run_scan(command: RunScanRequestDto, request: Request) -> OperationRefDto:
    return operation_manager(request).submit(OperationKind.RUN_SCAN, _payload(command))


@router.post(
    "/api/scans/{scan_id}/momentum-generations",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="generateAssetMomentum",
)
def generate_momentum(
    scan_id: str,
    command: MomentumGenerationRequestDto,
    request: Request,
) -> OperationRefDto:
    payload = _payload(command)
    payload["scan_id"] = scan_id
    return operation_manager(request).submit(
        OperationKind.GENERATE_ASSET_MOMENTUM,
        payload,
    )


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


@router.post(
    "/api/forward/cohorts",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="freezeForwardCohort",
)
def freeze_forward_cohort(
    command: FreezeForwardCohortRequestDto,
    request: Request,
) -> OperationRefDto:
    return operation_manager(request).submit(
        OperationKind.FREEZE_FORWARD_COHORT,
        _payload(command),
    )


@router.post(
    "/api/forward/cohorts/{cohort_id}/advances",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="advanceForwardCohort",
)
def advance_forward_cohort(
    cohort_id: str,
    command: AdvanceForwardCohortRequestDto,
    request: Request,
) -> OperationRefDto:
    payload = _payload(command)
    payload["cohort_id"] = cohort_id
    return operation_manager(request).submit(
        OperationKind.ADVANCE_FORWARD_COHORT,
        payload,
    )


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


@router.post(
    "/api/captures",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="capturePublicEvidence",
)
def capture_public_evidence(
    command: CapturePublicEvidenceRequestDto,
    request: Request,
) -> OperationRefDto:
    return operation_manager(request).submit(
        OperationKind.CAPTURE_PUBLIC_EVIDENCE,
        _payload(command),
    )


@router.post(
    "/api/qualifications",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="qualifyCandidate",
)
def qualify_candidate(
    command: QualificationRequestDto,
    request: Request,
) -> OperationRefDto:
    return operation_manager(request).submit(
        OperationKind.QUALIFY_CANDIDATE,
        _payload(command),
    )


__all__ = ["router"]
