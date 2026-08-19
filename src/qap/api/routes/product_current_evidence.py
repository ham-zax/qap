"""Product routes for persistent current public-evidence collection and assessment."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, Request
from pydantic import JsonValue

from qap.api.capture_views import forward_capture_readiness
from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind
from qap.api.product_current_evidence_schemas import (
    CurrentEvidenceSlotCountsDto,
    ProductAmountAssessmentRequestDto,
    ProductQualificationWorkerRequestDto,
    ResearchIdeaCurrentEvidenceDto,
)
from qap.api.routes.operations import operation_manager
from qap.api.scanner_schemas import CandidateDetailDto, OperationRefDto
from qap.api.scanner_views import ScannerArtifactReader
from qap.api.settings import ApiSettings
from qap.product_current_evidence import (
    CollectionPlan,
    ProductCurrentEvidenceError,
    ProductCurrentEvidenceStore,
    ResolvedCollectorInstrument,
    resolve_frozen_instrument,
    scheduled_slot,
)
from qap.product_current_evidence_assessment import (
    ProductCurrentAssessmentError,
    current_assessment_as_of,
)
from qap.product_current_evidence_identity import frozen_market_codes
from qap.product_universe import ProductUniverse, ProductUniverseError
from qap.scanner.prospective_artifacts import ProspectiveArtifactError

router = APIRouter(prefix="/api/product-research", tags=["product-current-evidence"])


def _settings(request: Request) -> ApiSettings:
    settings = cast(object, request.app.state.settings)
    if not isinstance(settings, ApiSettings):
        raise RuntimeError("API settings are not configured")
    return settings


def _reader(request: Request) -> ScannerArtifactReader:
    reader = cast(object, request.app.state.scanner_reader)
    if not isinstance(reader, ScannerArtifactReader):
        raise RuntimeError("Scanner artifact reader is not configured")
    return reader


def _store(request: Request) -> ProductCurrentEvidenceStore:
    store = cast(object, request.app.state.product_current_evidence)
    if not isinstance(store, ProductCurrentEvidenceStore):
        raise RuntimeError("Product current-evidence state is not configured")
    return store


def _require_local(request: Request) -> ApiSettings:
    settings = _settings(request)
    if settings.workspace_mode != "local_market":
        raise ApiBoundaryError(
            code="product_current_evidence_local_only",
            message=(
                "Current public-evidence collection is available only in Local Market."
            ),
            status_code=409,
            context={},
        )
    return settings


def _idea(
    request: Request,
    *,
    scan_id: str,
    candidate_id: str,
) -> CandidateDetailDto:
    detail = _reader(request).candidate_detail(scan_id, candidate_id)
    if detail.claim.kind != "current_approved_retrospective":
        raise ApiBoundaryError(
            code="product_current_evidence_claim_invalid",
            message=(
                "Current public-evidence collection requires a Product Research Idea."
            ),
            status_code=409,
            context={"scan_id": scan_id, "candidate_id": candidate_id},
        )
    if detail.candidate.economic_gate_status != "deep_replay_survivor":
        raise ApiBoundaryError(
            code="product_current_evidence_idea_invalid",
            message=(
                "Current evidence can be collected only for a surviving Research Idea."
            ),
            status_code=409,
            context={"candidate_id": candidate_id},
        )
    if not detail.longitudinal.memberships:
        raise ApiBoundaryError(
            code="product_current_evidence_follow_up_required",
            message="Start follow-up before collecting current public-market evidence.",
            status_code=409,
            context={"candidate_id": candidate_id},
        )
    return detail


def _latest_membership(detail: CandidateDetailDto):
    return detail.longitudinal.memberships[-1]


def _target(
    settings: ApiSettings,
    *,
    active_cohort_id: str,
    active_freeze_id: str,
) -> ResolvedCollectorInstrument:
    try:
        return resolve_frozen_instrument(
            settings.run_root,
            active_cohort_id=active_cohort_id,
            active_freeze_id=active_freeze_id,
        )
    except (
        OSError,
        ProspectiveArtifactError,
        ProductCurrentEvidenceError,
        ValueError,
    ) as exc:
        raise ApiBoundaryError(
            code="product_current_evidence_lineage_invalid",
            message="Frozen current-evidence instrument lineage is unavailable.",
            status_code=409,
            context={},
        ) from exc


def _data_root(settings: ApiSettings) -> Path:
    if settings.market_data_root is None:
        raise ApiBoundaryError(
            code="product_current_market_data_unavailable",
            message="Current market data is not configured.",
            status_code=409,
            context={},
        )
    return settings.market_data_root


def _counts(
    store: ProductCurrentEvidenceStore, instrument_id: str, kind: Literal["l1", "depth"]
):
    value = store.slot_counts(instrument_id, kind)
    return CurrentEvidenceSlotCountsDto(
        scheduled=value.scheduled,
        captured=value.captured,
        missed=value.missed,
    )


def _empty_state(
    store: ProductCurrentEvidenceStore,
) -> ResearchIdeaCurrentEvidenceDto:
    lease = store.lease_state()
    return ResearchIdeaCurrentEvidenceDto(
        state="not_collecting",
        collector_status=lease.status,
        collector_failure_reason=lease.failure_reason,
        plan_id=None,
        collecting_since=None,
        active_cohort_id=None,
        active_freeze_id=None,
        venue=None,
        venue_symbol=None,
        latest_observation=None,
        l1_slots=CurrentEvidenceSlotCountsDto(scheduled=0, captured=0, missed=0),
        depth_slots=CurrentEvidenceSlotCountsDto(scheduled=0, captured=0, missed=0),
        readiness_as_of=None,
        readiness=None,
        assessment_blocker="Start current-evidence collection for this Research Idea.",
    )


def _plan_membership(detail: CandidateDetailDto, plan: CollectionPlan):
    value = next(
        (
            item
            for item in detail.longitudinal.memberships
            if item.selection_cohort_id == plan.selection_cohort_id
            and item.active_cohort_id == plan.active_cohort_id
            and item.active_freeze_id == plan.active_freeze_id
        ),
        None,
    )
    if value is None:
        raise ApiBoundaryError(
            code="product_current_evidence_plan_stale",
            message=(
                "Collection plan no longer matches the Research Idea follow-up lineage."
            ),
            status_code=409,
            context={"plan_id": plan.plan_id},
        )
    return value


def _state(
    request: Request,
    *,
    scan_id: str,
    candidate_id: str,
) -> ResearchIdeaCurrentEvidenceDto:
    settings = _require_local(request)
    detail = _idea(request, scan_id=scan_id, candidate_id=candidate_id)
    store = _store(request)
    plan = store.active_plan(source_scan_id=scan_id, candidate_id=candidate_id)
    if plan is None:
        return _empty_state(store)
    membership = _plan_membership(detail, plan)
    target = _target(
        settings,
        active_cohort_id=plan.active_cohort_id,
        active_freeze_id=plan.active_freeze_id,
    )
    if (
        target.execution_instrument_id != plan.execution_instrument_id
        or target.collector_instrument_id != plan.collector_instrument_id
    ):
        raise ApiBoundaryError(
            code="product_current_evidence_plan_invalid",
            message=(
                "Collection plan instrument no longer matches immutable frozen lineage."
            ),
            status_code=409,
            context={"plan_id": plan.plan_id},
        )
    evidence = store.evidence(target)
    lease = store.lease_state()
    readiness = None
    readiness_as_of = None
    blocker = None
    state: Literal[
        "collecting", "coverage_incomplete", "contract_ready", "evidence_unavailable"
    ] = "collecting"
    if lease.status != "running":
        state = "evidence_unavailable"
        blocker = (
            lease.failure_reason
            or "The current-evidence collector is not running for this Local Market "
            "workspace."
        )
    elif not membership.checkpoints:
        blocker = "A completed forward checkpoint is required before amount assessment."
    else:
        readiness_as_of = scheduled_slot(datetime.now(UTC), "depth")
        checkpoint = membership.checkpoints[-1]
        if readiness_as_of < checkpoint.information_end:
            blocker = (
                "The current evidence boundary has not passed the latest forward "
                "checkpoint."
            )
        else:
            readiness = forward_capture_readiness(
                detail=_reader(request).forward_cohort_detail(plan.active_cohort_id),
                run_root=settings.run_root,
                capture_root=settings.capture_root
                or (settings.run_root / "public-capture"),
                checkpoint_id=checkpoint.checkpoint_id,
                as_of=readiness_as_of,
                capture_evidence=evidence,
            )
            if readiness.ready:
                state = "contract_ready"
                try:
                    current_assessment_as_of(
                        run_root=settings.run_root,
                        data_root=_data_root(settings),
                        active_cohort_id=plan.active_cohort_id,
                        active_freeze_id=plan.active_freeze_id,
                    )
                except ProductCurrentAssessmentError as exc:
                    blocker = str(exc)
            else:
                state = "coverage_incomplete"
                blocker = "Current public-market evidence is still incomplete."
    return ResearchIdeaCurrentEvidenceDto(
        state=state,
        collector_status=lease.status,
        collector_failure_reason=lease.failure_reason,
        plan_id=plan.plan_id,
        collecting_since=plan.started_at,
        active_cohort_id=plan.active_cohort_id,
        active_freeze_id=plan.active_freeze_id,
        venue=cast(Literal["binance", "gate"], target.instrument.venue),
        venue_symbol=target.instrument.venue_symbol,
        latest_observation=store.latest_observation(target.collector_instrument_id),
        l1_slots=_counts(store, target.collector_instrument_id, "l1"),
        depth_slots=_counts(store, target.collector_instrument_id, "depth"),
        readiness_as_of=readiness_as_of,
        readiness=readiness,
        assessment_blocker=blocker,
    )


@router.get(
    "/{scan_id}/ideas/{candidate_id}/current-evidence",
    response_model=ResearchIdeaCurrentEvidenceDto,
    operation_id="getProductResearchIdeaCurrentEvidence",
)
def get_current_evidence(
    scan_id: str,
    candidate_id: str,
    request: Request,
) -> ResearchIdeaCurrentEvidenceDto:
    return _state(request, scan_id=scan_id, candidate_id=candidate_id)


@router.post(
    "/{scan_id}/ideas/{candidate_id}/current-evidence",
    response_model=ResearchIdeaCurrentEvidenceDto,
    operation_id="startProductResearchIdeaCurrentEvidence",
)
def start_current_evidence(
    scan_id: str,
    candidate_id: str,
    request: Request,
) -> ResearchIdeaCurrentEvidenceDto:
    settings = _require_local(request)
    detail = _idea(request, scan_id=scan_id, candidate_id=candidate_id)
    membership = _latest_membership(detail)
    target = _target(
        settings,
        active_cohort_id=membership.active_cohort_id,
        active_freeze_id=membership.active_freeze_id,
    )
    try:
        frozen_market_codes(ProductUniverse(settings.run_root), target.instrument)
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="product_current_evidence_instrument_unresolved",
            message=str(exc),
            status_code=409,
            context={"candidate_id": candidate_id},
        ) from exc
    try:
        _store(request).start_plan(
            source_scan_id=scan_id,
            candidate_id=candidate_id,
            selection_cohort_id=membership.selection_cohort_id,
            target=target,
        )
    except ProductCurrentEvidenceError as exc:
        raise ApiBoundaryError(
            code="product_current_evidence_plan_conflict",
            message=str(exc),
            status_code=409,
            context={"candidate_id": candidate_id},
        ) from exc
    return _state(request, scan_id=scan_id, candidate_id=candidate_id)


@router.delete(
    "/{scan_id}/ideas/{candidate_id}/current-evidence",
    response_model=ResearchIdeaCurrentEvidenceDto,
    operation_id="stopProductResearchIdeaCurrentEvidence",
)
def stop_current_evidence(
    scan_id: str,
    candidate_id: str,
    request: Request,
) -> ResearchIdeaCurrentEvidenceDto:
    _require_local(request)
    _idea(request, scan_id=scan_id, candidate_id=candidate_id)
    _store(request).stop_plan(source_scan_id=scan_id, candidate_id=candidate_id)
    return _state(request, scan_id=scan_id, candidate_id=candidate_id)


@router.post(
    "/{scan_id}/ideas/{candidate_id}/amount-assessments",
    response_model=OperationRefDto,
    status_code=202,
    operation_id="assessProductResearchIdeaAmount",
)
def assess_amount(
    scan_id: str,
    candidate_id: str,
    command: ProductAmountAssessmentRequestDto,
    request: Request,
) -> OperationRefDto:
    settings = _require_local(request)
    detail = _idea(request, scan_id=scan_id, candidate_id=candidate_id)
    store = _store(request)
    plan = store.active_plan(source_scan_id=scan_id, candidate_id=candidate_id)
    if plan is None:
        raise ApiBoundaryError(
            code="product_current_evidence_not_collecting",
            message="Start current-evidence collection before assessing an amount.",
            status_code=409,
            context={"candidate_id": candidate_id},
        )
    membership = _plan_membership(detail, plan)
    if not membership.checkpoints:
        raise ApiBoundaryError(
            code="product_current_evidence_checkpoint_required",
            message=(
                "A completed forward checkpoint is required before amount assessment."
            ),
            status_code=409,
            context={"candidate_id": candidate_id},
        )
    target = _target(
        settings,
        active_cohort_id=plan.active_cohort_id,
        active_freeze_id=plan.active_freeze_id,
    )
    try:
        as_of = current_assessment_as_of(
            run_root=settings.run_root,
            data_root=_data_root(settings),
            active_cohort_id=plan.active_cohort_id,
            active_freeze_id=plan.active_freeze_id,
        )
    except ProductCurrentAssessmentError as exc:
        raise ApiBoundaryError(
            code="product_current_market_data_stale",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc
    checkpoint = membership.checkpoints[-1]
    readiness = forward_capture_readiness(
        detail=_reader(request).forward_cohort_detail(plan.active_cohort_id),
        run_root=settings.run_root,
        capture_root=settings.capture_root or (settings.run_root / "public-capture"),
        checkpoint_id=checkpoint.checkpoint_id,
        as_of=as_of,
        capture_evidence=store.evidence(target),
    )
    if not readiness.ready:
        raise ApiBoundaryError(
            code="product_current_evidence_incomplete",
            message=(
                "Current public-market evidence is incomplete for this amount "
                "assessment."
            ),
            status_code=409,
            context={"checkpoint_id": checkpoint.checkpoint_id},
        )
    worker = ProductQualificationWorkerRequestDto(
        cohort_id=plan.active_cohort_id,
        checkpoint_id=checkpoint.checkpoint_id,
        as_of=as_of,
        requested_capital=command.requested_capital,
        evidence_source="product_collector",
        active_freeze_id=plan.active_freeze_id,
    )
    payload = cast(dict[str, JsonValue], worker.model_dump(mode="json"))
    return operation_manager(request).submit(OperationKind.QUALIFY_CANDIDATE, payload)


__all__ = ["router"]
