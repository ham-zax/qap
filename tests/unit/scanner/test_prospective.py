from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import (
    CandidateFreeze,
    ForwardCheckpoint,
    ForwardCohort,
    enroll_forward_cohort,
)
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    protocol_identity,
)

FREEZE = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)
FORWARD_START = FREEZE + timedelta(hours=1)


def _freeze(
    *,
    candidate: str = "b",
    scan: str = "a",
    frozen_at: datetime = FREEZE,
    forward_start: datetime = FORWARD_START,
    automatic: bool = True,
    manual: bool = False,
    source_fingerprint: str = "c",
) -> CandidateFreeze:
    return CandidateFreeze(
        candidate_id=candidate * 64,
        scan_id=scan * 64,
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        scanner_protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        prospective_protocol_version=PROSPECTIVE_V1.protocol_id,
        prospective_protocol_identity=prospective_protocol_identity(PROSPECTIVE_V1),
        automatic_selected=automatic,
        manual_selected=manual,
        frozen_at=frozen_at,
        eligible_information_end=frozen_at,
        forward_start=forward_start,
        forward_end=forward_start + timedelta(hours=48),
        horizon=ScannerHorizon.SHORT,
        venue="binance",
        pair_id="BTC/ETH",
        orientation="BTC/ETH",
        resolution="1h",
        model_family="log_ratio_mean_reversion",
        template_id="fast",
        model_parameters=(("window_bars", "48"),),
        source_artifact_fingerprints=(source_fingerprint * 64, "d" * 64),
        selection_slice_fingerprints=("1" * 64, "2" * 64),
        universe_snapshot_id="e" * 64,
        cost_policy_reference=PROSPECTIVE_V1.adverse_cost_reference,
        primary_control_reference=PROSPECTIVE_V1.primary_control_reference,
        candidate_deep_replay_run_id=f"slice1-run-{candidate}",
        candidate_deep_replay_gate_status="deep_replay_survivor",
    )


def _slice(fingerprint: str = "1" * 64) -> ScanInputIdentity:
    return ScanInputIdentity(
        dataset_id="btceth-forward-1h",
        source_artifact_fingerprint="f" * 64,
        selection_slice_fingerprint=fingerprint,
    )


def _cohort(*freezes: CandidateFreeze) -> ForwardCohort:
    return enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE,
        selected_freezes=freezes,
        created_at=FREEZE + timedelta(minutes=1),
    )


def _checkpoint(**updates: object) -> ForwardCheckpoint:
    freeze = _freeze()
    cohort = _cohort(freeze)
    values: dict[str, object] = {
        "cohort_id": cohort.cohort_id,
        "candidate_id": freeze.candidate_id,
        "freeze_id": freeze.freeze_id,
        "checkpoint_index": 1,
        "freeze_at": FREEZE,
        "eligible_information_end": FREEZE,
        "forward_start": FORWARD_START,
        "first_outcome_complete_at": FORWARD_START + timedelta(hours=1),
        "evidence_window_start": FORWARD_START,
        "evidence_window_end": FORWARD_START + timedelta(hours=24),
        "information_end": FORWARD_START + timedelta(hours=24),
        "forward_slices": (_slice(),),
        "evidence_role": "prospective",
        "prospective_protocol_version": PROSPECTIVE_V1.protocol_id,
        "prospective_protocol_identity": prospective_protocol_identity(PROSPECTIVE_V1),
        "created_at": FORWARD_START + timedelta(hours=24, minutes=1),
    }
    values.update(updates)
    return ForwardCheckpoint.model_validate(values)


def test_prospective_protocol_identity_binds_semantic_policy_payload() -> None:
    baseline = prospective_protocol_identity(PROSPECTIVE_V1)
    changed = prospective_protocol_identity(
        replace(PROSPECTIVE_V1, checkpoint_policy_version="changed")
    )
    changed_cost = prospective_protocol_identity(
        replace(PROSPECTIVE_V1, adverse_cost_reference="changed-cost")
    )

    assert len(baseline) == 64
    assert baseline != changed
    assert baseline != changed_cost


def test_candidate_freeze_requires_strict_forward_boundary_and_frozen_horizon() -> None:
    baseline = _freeze()
    assert baseline.forward_end == baseline.forward_start + timedelta(hours=48)
    assert len(baseline.freeze_id) == 64
    assert len(baseline.semantic_rule_id) == 64

    with pytest.raises(ValueError, match="strictly after frozen_at"):
        _freeze(forward_start=FREEZE)
    with pytest.raises(ValueError, match="frozen horizon window"):
        CandidateFreeze.model_validate(
            {
                **baseline.model_dump(mode="python"),
                "forward_end": baseline.forward_end + timedelta(1),
            }
        )


def test_zero_new_member_cohort_is_valid_and_creation_time_is_nonsemantic() -> None:
    cohort = _cohort()
    later = cohort.model_copy(update={"created_at": FREEZE + timedelta(hours=1)})

    assert cohort.candidate_freeze_ids == ()
    assert cohort.reselected_active_freeze_ids == ()
    assert cohort.automatic_member_count == 0
    assert cohort.manual_member_count == 0
    assert cohort.cohort_id == later.cohort_id


def test_active_semantic_rule_is_reselection_not_duplicate_freeze() -> None:
    active = _freeze(candidate="b", scan="f", frozen_at=FREEZE - timedelta(hours=1))
    selected = _freeze(candidate="c", scan="a", source_fingerprint="9")
    assert active.semantic_rule_id == selected.semantic_rule_id

    cohort = enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE,
        selected_freezes=(selected,),
        active_freezes=(active,),
    )

    assert cohort.candidate_freeze_ids == ()
    assert cohort.reselected_active_freeze_ids == (active.freeze_id,)
    assert cohort.candidate_ids == (selected.candidate_id,)
    assert cohort.automatic_member_count == 1


def test_matured_semantic_rule_can_open_new_generation() -> None:
    matured_start = FREEZE - timedelta(hours=49)
    matured = _freeze(
        candidate="b",
        scan="f",
        frozen_at=FREEZE - timedelta(hours=50),
        forward_start=matured_start,
    )
    selected = _freeze(candidate="c", scan="a", source_fingerprint="9")

    cohort = enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE,
        selected_freezes=(selected,),
        active_freezes=(matured,),
    )

    assert cohort.candidate_freeze_ids == (selected.freeze_id,)
    assert cohort.reselected_active_freeze_ids == ()


def test_manual_and_automatic_membership_counts_remain_separate() -> None:
    automatic = _freeze(candidate="b", automatic=True, manual=False)
    manual = _freeze(candidate="c", automatic=False, manual=True)
    cohort = _cohort(automatic, manual)

    assert cohort.automatic_member_count == 1
    assert cohort.manual_member_count == 1
    assert set(cohort.candidate_ids) == {automatic.candidate_id, manual.candidate_id}


def test_checkpoint_is_strictly_forward_and_binds_exact_boundaries() -> None:
    checkpoint = _checkpoint()
    later_created = checkpoint.model_copy(
        update={"created_at": checkpoint.created_at + timedelta(hours=1)}
    )
    changed_start = checkpoint.model_copy(
        update={
            "forward_start": checkpoint.forward_start + timedelta(minutes=1),
            "evidence_window_start": checkpoint.forward_start + timedelta(minutes=1),
        }
    )

    assert checkpoint.checkpoint_id == later_created.checkpoint_id
    assert checkpoint.checkpoint_id != changed_start.checkpoint_id

    with pytest.raises(ValueError, match="strictly after freeze_at"):
        _checkpoint(forward_start=FREEZE, evidence_window_start=FREEZE)
    with pytest.raises(ValueError, match="strictly after forward_start"):
        _checkpoint(first_outcome_complete_at=FORWARD_START)


def test_checkpoint_rejects_pre_forward_or_uncovered_outcomes() -> None:
    with pytest.raises(ValueError, match="equal forward_start"):
        _checkpoint(evidence_window_start=FORWARD_START + timedelta(minutes=1))
    with pytest.raises(ValueError, match="within evidence window"):
        _checkpoint(first_outcome_complete_at=FORWARD_START + timedelta(hours=25))
    with pytest.raises(ValueError, match="cover evidence_window_end"):
        _checkpoint(information_end=FORWARD_START + timedelta(hours=23))


def test_checkpoint_rejects_final_oos_role_at_schema_boundary() -> None:
    with pytest.raises(ValidationError):
        _checkpoint(evidence_role="final_oos")
