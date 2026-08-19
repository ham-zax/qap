"""Longitudinal Research Idea composition over immutable scanner evidence."""

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

from qap.api.scanner_schemas import (
    CandidateSummaryDto,
    ForwardReselectionDto,
    ProductFollowUpDto,
    ResearchClaimDto,
    ResearchIdeaCurrentAssessmentDto,
    ResearchIdeaFollowUpMembershipDto,
    ResearchIdeaForwardCheckpointDto,
    ResearchIdeaLongitudinalDto,
)
from qap.scanner.prospective import CandidateFreeze, ForwardCohort
from qap.scanner.prospective_artifact_schemas import CHECKPOINT_TABLE
from qap.scanner.prospective_artifacts import read_completed_checkpoints
from qap.scanner.prospective_integrity import (
    read_outcome,
    validate_completed_generation,
)
from qap.scanner.qualification_artifacts import read_qualifications

CohortEntry = tuple[Path, ForwardCohort]
CohortSource = tuple[CohortEntry, ...] | Callable[[], tuple[CohortEntry, ...]]
FreezeOwner = tuple[Path, ForwardCohort, CandidateFreeze]


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return cast(Mapping[str, object], value)


def _freeze_owners(cohorts: tuple[CohortEntry, ...]) -> dict[str, FreezeOwner]:
    owners: dict[str, FreezeOwner] = {}
    for root, cohort in cohorts:
        for freeze in cohort.candidate_freezes:
            existing = owners.get(freeze.freeze_id)
            if existing is not None and existing[1].cohort_id != cohort.cohort_id:
                raise ValueError("active freeze is owned by multiple cohorts")
            owners[freeze.freeze_id] = (root, cohort, freeze)
    return owners


def _active_owner(
    active_freeze_id: str,
    owners: dict[str, FreezeOwner],
) -> FreezeOwner:
    try:
        return owners[active_freeze_id]
    except KeyError as exc:
        raise ValueError("reselection active freeze is unavailable") from exc


def product_follow_up(
    *,
    scan_id: str,
    claim: ResearchClaimDto,
    horizons: tuple[str, ...],
    survivor_count: int,
    cohorts: CohortSource,
) -> ProductFollowUpDto | None:
    """Return the valid Product action for one completed research generation."""

    if claim.kind != "current_approved_retrospective":
        return None
    if len(horizons) != 1:
        return ProductFollowUpDto(
            state="unavailable",
            horizon=None,
            survivor_count=survivor_count,
            reason="Current-approved Product follow-up requires one frozen timeframe.",
        )
    horizon = horizons[0]
    resolved_cohorts = cohorts() if callable(cohorts) else cohorts
    existing = sorted(
        (
            cohort
            for _root, cohort in resolved_cohorts
            if cohort.source_scan_id == scan_id and cohort.horizon.value == horizon
        ),
        key=lambda cohort: (cohort.freeze_at, cohort.cohort_id),
        reverse=True,
    )
    if existing:
        return ProductFollowUpDto(
            state="existing",
            horizon=horizon,
            survivor_count=survivor_count,
            cohort_id=existing[0].cohort_id,
        )
    if survivor_count <= 0:
        return ProductFollowUpDto(
            state="unavailable",
            horizon=horizon,
            survivor_count=survivor_count,
            reason="No historical Research Ideas are available for follow-up.",
        )
    return ProductFollowUpDto(
        state="start_available",
        horizon=horizon,
        survivor_count=survivor_count,
    )


def _checkpoint_dtos(
    root: Path,
    *,
    active_cohort_id: str,
    freeze_id: str,
) -> tuple[ResearchIdeaForwardCheckpointDto, ...]:
    values: list[ResearchIdeaForwardCheckpointDto] = []
    for directory in read_completed_checkpoints(root):
        manifest, tables = validate_completed_generation(directory)
        outcome = read_outcome(directory)
        if outcome.freeze_id != freeze_id:
            continue
        rows = tables[CHECKPOINT_TABLE].to_pylist()
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError("forward checkpoint is malformed")
        row = cast(dict[str, Any], rows[0])
        raw_index = manifest["checkpoint_index"]
        if not isinstance(raw_index, int) or isinstance(raw_index, bool):
            raise ValueError("forward checkpoint index is malformed")
        values.append(
            ResearchIdeaForwardCheckpointDto(
                checkpoint_id=outcome.checkpoint_id,
                active_cohort_id=active_cohort_id,
                checkpoint_index=raw_index,
                information_end=row["information_end"],
                outcome_status=outcome.status.value,
                qap_run_id=outcome.qap_run_id,
                strategy_vs_hodl=(
                    None
                    if outcome.strategy_vs_hodl is None
                    else str(outcome.strategy_vs_hodl)
                ),
                strategy_vs_primary_control=(
                    None
                    if outcome.strategy_vs_primary_control is None
                    else str(outcome.strategy_vs_primary_control)
                ),
                baseline_economic_gates_passed=outcome.baseline_economic_gates_passed,
                adverse_economic_gates_passed=outcome.adverse_economic_gates_passed,
                failure_reason=outcome.failure_reason,
            )
        )
    values.sort(key=lambda item: (item.checkpoint_index, item.information_end))
    return tuple(values)


def _assessment_dtos(
    root: Path,
    *,
    active_cohort_id: str,
    freeze_id: str,
) -> tuple[ResearchIdeaCurrentAssessmentDto, ...]:
    values: list[ResearchIdeaCurrentAssessmentDto] = []
    for document in read_qualifications(root):
        request = _mapping(document.get("request"), field="qualification.request")
        if request.get("freeze_id") != freeze_id:
            continue
        values.append(
            ResearchIdeaCurrentAssessmentDto(
                qualification_id=str(document["qualification_id"]),
                active_cohort_id=active_cohort_id,
                checkpoint_id=str(document["checkpoint_id"]),
                as_of=cast(Any, request["as_of"]),
                requested_capital=str(request["requested_capital"]),
                state=cast(Any, document["state"]),
                reason=str(document["reason"]),
                candidate_capital_ceiling=(
                    None
                    if request.get("candidate_capital_ceiling") is None
                    else str(request["candidate_capital_ceiling"])
                ),
            )
        )
    values.sort(key=lambda item: (item.as_of, item.qualification_id))
    return tuple(values)


def _membership(
    *,
    selection_cohort: ForwardCohort,
    candidate_id: str,
    source_scan_id: str,
    selected_at: Any,
    automatic_selected: bool,
    manual_selected: bool,
    membership_kind: str,
    active_owner: FreezeOwner,
) -> ResearchIdeaFollowUpMembershipDto:
    active_root, active_cohort, active_freeze = active_owner
    checkpoints = _checkpoint_dtos(
        active_root,
        active_cohort_id=active_cohort.cohort_id,
        freeze_id=active_freeze.freeze_id,
    )
    assessments = _assessment_dtos(
        active_root,
        active_cohort_id=active_cohort.cohort_id,
        freeze_id=active_freeze.freeze_id,
    )
    return ResearchIdeaFollowUpMembershipDto(
        selection_cohort_id=selection_cohort.cohort_id,
        membership_kind=cast(Any, membership_kind),
        candidate_id=candidate_id,
        source_scan_id=source_scan_id,
        selected_at=selected_at,
        automatic_selected=automatic_selected,
        manual_selected=manual_selected,
        active_freeze_id=active_freeze.freeze_id,
        active_cohort_id=active_cohort.cohort_id,
        active_candidate_id=active_freeze.candidate_id,
        active_source_scan_id=active_freeze.scan_id,
        forward_start=active_freeze.forward_start,
        forward_end=active_freeze.forward_end,
        checkpoints=checkpoints,
        assessments=assessments,
    )


def _memberships(
    candidate_id: str,
    cohorts: tuple[CohortEntry, ...],
) -> tuple[ResearchIdeaFollowUpMembershipDto, ...]:
    owners = _freeze_owners(cohorts)
    values: list[ResearchIdeaFollowUpMembershipDto] = []
    for _root, cohort in cohorts:
        for freeze in cohort.candidate_freezes:
            if freeze.candidate_id != candidate_id:
                continue
            values.append(
                _membership(
                    selection_cohort=cohort,
                    candidate_id=freeze.candidate_id,
                    source_scan_id=freeze.scan_id,
                    selected_at=freeze.frozen_at,
                    automatic_selected=freeze.automatic_selected,
                    manual_selected=freeze.manual_selected,
                    membership_kind="new_freeze",
                    active_owner=(owners[freeze.freeze_id]),
                )
            )
        for reselection in cohort.reselections:
            if reselection.candidate_id != candidate_id:
                continue
            values.append(
                _membership(
                    selection_cohort=cohort,
                    candidate_id=reselection.candidate_id,
                    source_scan_id=reselection.source_scan_id,
                    selected_at=reselection.reselected_at,
                    automatic_selected=reselection.automatic_selected,
                    manual_selected=reselection.manual_selected,
                    membership_kind="reselection",
                    active_owner=_active_owner(reselection.active_freeze_id, owners),
                )
            )
    values.sort(
        key=lambda item: (
            item.selected_at,
            item.selection_cohort_id,
            item.membership_kind,
        )
    )
    return tuple(values)


def _historical_replay_state(candidate: CandidateSummaryDto) -> str:
    if candidate.economic_gate_status == "deep_replay_survivor":
        return "supported"
    if candidate.economic_gate_status == "deep_replay_rejected":
        return "not_supported"
    if candidate.trial_status != "valid" or candidate.deep_replay_status in {
        "setup_failed",
        "replay_failed",
    }:
        return "unavailable"
    return "not_completed"


def _later_state(
    memberships: tuple[ResearchIdeaFollowUpMembershipDto, ...],
) -> tuple[str, str | None]:
    if not memberships:
        return "not_started", None
    latest = memberships[-1]
    if not latest.checkpoints:
        return "waiting_for_later_evidence", None
    outcome = latest.checkpoints[-1]
    if outcome.outcome_status == "pending":
        return "waiting_for_later_evidence", None
    if outcome.outcome_status == "partial":
        return "later_evidence_accumulating", None
    if outcome.outcome_status == "invalid":
        return "later_evidence_unavailable", outcome.failure_reason
    if (
        outcome.baseline_economic_gates_passed is True
        and outcome.adverse_economic_gates_passed is True
    ):
        return "later_evidence_supported", None
    return (
        "later_evidence_not_supported",
        "Matured later evidence did not pass both declared economic gates.",
    )


def research_idea_longitudinal(
    candidate: CandidateSummaryDto,
    cohorts: tuple[CohortEntry, ...],
) -> ResearchIdeaLongitudinalDto:
    """Compose historical, later, and persisted current evidence without copying it."""

    memberships = _memberships(candidate.candidate_id, cohorts)
    later_state, later_reason = _later_state(memberships)
    assessments_by_id = {
        item.qualification_id: item
        for membership in memberships
        for item in membership.assessments
    }
    assessments = tuple(
        sorted(
            assessments_by_id.values(),
            key=lambda item: (item.as_of, item.qualification_id),
        )
    )
    return ResearchIdeaLongitudinalDto(
        historical_discovery_state=(
            "evaluated" if candidate.trial_status == "valid" else "unavailable"
        ),
        historical_replay_state=cast(Any, _historical_replay_state(candidate)),
        later_state=cast(Any, later_state),
        later_reason=later_reason,
        memberships=memberships,
        current_evidence_state=(
            "assessment_available" if assessments else "not_assessed"
        ),
        current_assessments=assessments,
    )


def resolved_reselections(
    cohort: ForwardCohort,
    cohorts: tuple[CohortEntry, ...],
) -> tuple[ForwardReselectionDto, ...]:
    """Resolve reselections to the cohort/freezing rule that owns later evidence."""

    owners = _freeze_owners(cohorts)
    values: list[ForwardReselectionDto] = []
    for item in cohort.reselections:
        _root, active_cohort, active_freeze = _active_owner(
            item.active_freeze_id, owners
        )
        values.append(
            ForwardReselectionDto(
                active_freeze_id=item.active_freeze_id,
                candidate_id=item.candidate_id,
                source_scan_id=item.source_scan_id,
                automatic_selected=item.automatic_selected,
                manual_selected=item.manual_selected,
                reselected_at=item.reselected_at,
                active_cohort_id=active_cohort.cohort_id,
                active_candidate_id=active_freeze.candidate_id,
                active_source_scan_id=active_freeze.scan_id,
                forward_start=active_freeze.forward_start,
                forward_end=active_freeze.forward_end,
            )
        )
    return tuple(values)


__all__ = [
    "CohortEntry",
    "CohortSource",
    "product_follow_up",
    "research_idea_longitudinal",
    "resolved_reselections",
]
