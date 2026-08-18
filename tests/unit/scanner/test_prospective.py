from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import (
    SLICE2_PROTOCOL,
    FrozenCandidateAttachment,
    ProspectiveCheckpoint,
    ProspectiveCohort,
    prospective_protocol_identity,
)

FREEZE = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)


def _attachment(candidate: str, run: str) -> FrozenCandidateAttachment:
    return FrozenCandidateAttachment(
        candidate_id=candidate * 64,
        deep_replay_run_id=run,
        slice1_economic_gate_status="deep_replay_survivor",
    )


def _cohort(*attachments: FrozenCandidateAttachment) -> ProspectiveCohort:
    return ProspectiveCohort(
        schema_version="qap.scanner.prospective-cohort.v1",
        slice2_protocol_version=SLICE2_PROTOCOL.protocol_id,
        protocol_identity=prospective_protocol_identity(SLICE2_PROTOCOL),
        source_scan_id="a" * 64,
        freeze_at=FREEZE,
        candidates=attachments or (_attachment("b", "run-b"),),
        created_at=FREEZE + timedelta(minutes=1),
    )


def _slice(fingerprint: str = "1" * 64) -> ScanInputIdentity:
    return ScanInputIdentity(
        dataset_id="btceth-forward-1h",
        source_artifact_fingerprint="f" * 64,
        selection_slice_fingerprint=fingerprint,
    )


def test_slice2_protocol_identity_binds_adverse_cost_and_policy_versions() -> None:
    baseline = prospective_protocol_identity(SLICE2_PROTOCOL)
    changed = prospective_protocol_identity(
        replace(SLICE2_PROTOCOL, checkpoint_policy_version="changed")
    )
    changed_cost = prospective_protocol_identity(
        replace(SLICE2_PROTOCOL, adverse_cost_reference="changed-cost")
    )

    assert len(baseline) == 64
    assert baseline != changed
    assert baseline != changed_cost
    assert SLICE2_PROTOCOL.adverse_cost_reference == "scanner-v1-historical-costs-v1"


def test_cohort_identity_is_order_independent_and_creation_time_is_nonsemantic() -> None:
    first = _attachment("b", "run-b")
    second = _attachment("c", "run-c")
    left = _cohort(first, second)
    right = _cohort(second, first).model_copy(
        update={"created_at": FREEZE + timedelta(hours=2)}
    )

    assert left.candidate_ids == ("b" * 64, "c" * 64)
    assert right.candidate_ids == left.candidate_ids
    assert left.cohort_id == right.cohort_id


def test_cohort_accepts_only_slice1_deep_replay_survivors_and_unique_candidates() -> None:
    survivor = _attachment("b", "run-b")
    rejected = survivor.model_copy(
        update={"slice1_economic_gate_status": "deep_replay_rejected"}
    )

    with pytest.raises(ValueError, match="deep_replay_survivor"):
        _cohort(rejected)
    with pytest.raises(ValueError, match="unique"):
        _cohort(survivor, survivor)


def test_checkpoint_is_strictly_forward_and_binds_exact_slice_identity() -> None:
    cohort = _cohort()
    checkpoint = ProspectiveCheckpoint(
        schema_version="qap.scanner.prospective-checkpoint.v1",
        cohort_id=cohort.cohort_id,
        candidate_id=cohort.candidate_ids[0],
        checkpoint_index=1,
        freeze_at=cohort.freeze_at,
        evidence_window_start=FREEZE,
        evidence_window_end=FREEZE + timedelta(days=7),
        information_end=FREEZE + timedelta(days=7),
        forward_slices=(_slice(),),
        evidence_role="prospective",
        slice2_protocol_version=SLICE2_PROTOCOL.protocol_id,
        protocol_identity=prospective_protocol_identity(SLICE2_PROTOCOL),
        created_at=FREEZE + timedelta(days=7, minutes=1),
    )
    later_created = checkpoint.model_copy(
        update={"created_at": checkpoint.created_at + timedelta(hours=1)}
    )
    changed_slice = checkpoint.model_copy(
        update={"forward_slices": (_slice("2" * 64),)}
    )

    assert len(checkpoint.checkpoint_id) == 64
    assert checkpoint.checkpoint_id == later_created.checkpoint_id
    assert checkpoint.checkpoint_id != changed_slice.checkpoint_id


@pytest.mark.parametrize(
    ("start", "end", "information_end", "message"),
    [
        (
            FREEZE - timedelta(seconds=1),
            FREEZE + timedelta(days=1),
            FREEZE + timedelta(days=1),
            "at or after freeze_at",
        ),
        (
            FREEZE,
            FREEZE,
            FREEZE,
            "end after start",
        ),
        (
            FREEZE,
            FREEZE + timedelta(days=2),
            FREEZE + timedelta(days=1),
            "cover evidence_window_end",
        ),
    ],
)
def test_checkpoint_rejects_nonprospective_windows(
    start: datetime,
    end: datetime,
    information_end: datetime,
    message: str,
) -> None:
    cohort = _cohort()
    with pytest.raises(ValueError, match=message):
        ProspectiveCheckpoint(
            schema_version="qap.scanner.prospective-checkpoint.v1",
            cohort_id=cohort.cohort_id,
            candidate_id=cohort.candidate_ids[0],
            checkpoint_index=1,
            freeze_at=cohort.freeze_at,
            evidence_window_start=start,
            evidence_window_end=end,
            information_end=information_end,
            forward_slices=(_slice(),),
            evidence_role="prospective",
            slice2_protocol_version=SLICE2_PROTOCOL.protocol_id,
            protocol_identity=prospective_protocol_identity(SLICE2_PROTOCOL),
            created_at=FREEZE + timedelta(days=3),
        )


def test_checkpoint_rejects_final_oos_role_at_schema_boundary() -> None:
    cohort = _cohort()
    with pytest.raises(ValidationError):
        ProspectiveCheckpoint.model_validate(
            {
                "schema_version": "qap.scanner.prospective-checkpoint.v1",
                "cohort_id": cohort.cohort_id,
                "candidate_id": cohort.candidate_ids[0],
                "checkpoint_index": 1,
                "freeze_at": cohort.freeze_at.isoformat(),
                "evidence_window_start": FREEZE.isoformat(),
                "evidence_window_end": (FREEZE + timedelta(days=1)).isoformat(),
                "information_end": (FREEZE + timedelta(days=1)).isoformat(),
                "forward_slices": [_slice().model_dump(mode="json")],
                "evidence_role": "final_oos",
                "slice2_protocol_version": SLICE2_PROTOCOL.protocol_id,
                "protocol_identity": prospective_protocol_identity(SLICE2_PROTOCOL),
                "created_at": (FREEZE + timedelta(days=1, minutes=1)).isoformat(),
            }
        )
