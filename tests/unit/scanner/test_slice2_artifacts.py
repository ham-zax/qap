# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from qap.scanner.liquidity_policy import QualificationReason, QualificationState
from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import (
    SLICE2_PROTOCOL,
    FrozenCandidateAttachment,
    ProspectiveCheckpoint,
    ProspectiveCohort,
    prospective_protocol_identity,
)
from qap.scanner.slice2_artifact_contract import (
    ARTIFACT_DESIGN_SHA256,
    CHECKPOINT_TABLE,
    CHECKPOINTS_INDEX,
    COHORT_DEFINITION,
    FREEZES_TABLE,
    LIQUIDITY_TABLE,
    MANIFEST,
    OUTCOMES_INDEX,
    QUALIFICATION_TABLE,
)
from qap.scanner.slice2_artifacts import (
    CapacityQualificationRecord,
    CheckpointObservationRecord,
    LiquidityEvidenceRecord,
    Slice2ArtifactError,
    publish_checkpoint,
    read_completed_checkpoints,
    start_checkpoint,
    start_prospective_cohort,
    write_checkpoint_evidence,
)

FREEZE = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)


def _cohort() -> ProspectiveCohort:
    return ProspectiveCohort(
        schema_version="qap.scanner.prospective-cohort.v1",
        slice2_protocol_version=SLICE2_PROTOCOL.protocol_id,
        protocol_identity=prospective_protocol_identity(SLICE2_PROTOCOL),
        source_scan_id="a" * 64,
        freeze_at=FREEZE,
        candidates=(
            FrozenCandidateAttachment(
                candidate_id="b" * 64,
                deep_replay_run_id="slice1-run-b",
                slice1_economic_gate_status="deep_replay_survivor",
            ),
        ),
        created_at=FREEZE + timedelta(seconds=1),
    )


def _checkpoint(index: int = 1) -> ProspectiveCheckpoint:
    return ProspectiveCheckpoint(
        schema_version="qap.scanner.prospective-checkpoint.v1",
        cohort_id=_cohort().cohort_id,
        candidate_id="b" * 64,
        checkpoint_index=index,
        freeze_at=FREEZE,
        evidence_window_start=FREEZE,
        evidence_window_end=FREEZE + timedelta(days=7 * index),
        information_end=FREEZE + timedelta(days=7 * index),
        forward_slices=(
            ScanInputIdentity(
                dataset_id=f"forward-{index}",
                source_artifact_fingerprint="c" * 64,
                selection_slice_fingerprint=f"{index:x}" * 64,
            ),
        ),
        evidence_role="prospective",
        slice2_protocol_version=SLICE2_PROTOCOL.protocol_id,
        protocol_identity=prospective_protocol_identity(SLICE2_PROTOCOL),
        created_at=FREEZE + timedelta(days=7 * index, seconds=1),
    )


def _observation(checkpoint: ProspectiveCheckpoint) -> CheckpointObservationRecord:
    return CheckpointObservationRecord.from_checkpoint(
        checkpoint,
        prospective_complete=True,
        prospective_status="observed",
        authoritative_run_id=None,
    )


def _liquidity(checkpoint: ProspectiveCheckpoint) -> LiquidityEvidenceRecord:
    return LiquidityEvidenceRecord(
        checkpoint_id=checkpoint.checkpoint_id,
        candidate_id=checkpoint.candidate_id,
        snapshot_id="d" * 64,
        side="buy_base",
        quote_notional=Decimal("100"),
        fillable=False,
        fee_bps=Decimal("20"),
        book_price_impact_bps=None,
        total_friction_bps=None,
    )


def _qualification(checkpoint: ProspectiveCheckpoint) -> CapacityQualificationRecord:
    return CapacityQualificationRecord(
        checkpoint_id=checkpoint.checkpoint_id,
        candidate_id=checkpoint.candidate_id,
        as_of=checkpoint.information_end,
        requested_capital=Decimal("500"),
        q_star_buy=None,
        q_safe_buy=None,
        q_star_sell=None,
        q_safe_sell=None,
        current_base_weight=Decimal("0.50"),
        required_buy_fraction=Decimal("0.20"),
        required_sell_fraction=Decimal("0.20"),
        candidate_capital_ceiling=None,
        qualification_state=QualificationState.RESEARCH_ONLY,
        reason=QualificationReason.CAPACITY_UNKNOWN,
        capture_contract_satisfied=False,
        current_two_way_trading=True,
        order_constraints_satisfied=True,
        economic_gates_at_requested_capital=False,
        lower_tested_capital=None,
        economic_gates_at_lower_capital=False,
    )


def test_slice2_artifact_contract_matches_approved_storage_surface() -> None:
    design = Path(
        "docs/superpowers/specs/"
        "2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md"
    )
    assert sha256(design.read_bytes()).hexdigest() == ARTIFACT_DESIGN_SHA256
    assert COHORT_DEFINITION == "cohort.json"
    assert FREEZES_TABLE == "freezes.parquet"
    assert CHECKPOINTS_INDEX == "checkpoints.parquet"
    assert OUTCOMES_INDEX == "outcomes.parquet"


def test_cohort_freeze_is_published_before_any_checkpoint(tmp_path: Path) -> None:
    cohort = _cohort()
    root = start_prospective_cohort(tmp_path, cohort)

    assert root == tmp_path.resolve() / "scanner-forward" / cohort.cohort_id
    payload = json.loads((root / COHORT_DEFINITION).read_text(encoding="utf-8"))
    assert payload["cohort_id"] == cohort.cohort_id
    freezes = pq.read_table(root / FREEZES_TABLE).to_pylist()
    assert freezes == [
        {
            "cohort_id": cohort.cohort_id,
            "candidate_id": "b" * 64,
            "deep_replay_run_id": "slice1-run-b",
            "slice1_economic_gate_status": "deep_replay_survivor",
            "freeze_at": FREEZE,
            "source_scan_id": "a" * 64,
            "slice2_protocol_version": SLICE2_PROTOCOL.protocol_id,
            "protocol_identity": prospective_protocol_identity(SLICE2_PROTOCOL),
        }
    ]
    assert read_completed_checkpoints(root) == ()
    assert start_prospective_cohort(tmp_path, cohort) == root

    changed = cohort.model_copy(update={"freeze_at": FREEZE + timedelta(seconds=1)})
    with pytest.raises(Slice2ArtifactError, match="cohort definition"):
        start_prospective_cohort(
            tmp_path,
            changed,
            cohort_id_override=cohort.cohort_id,
        )


def test_artifact_identity_overrides_cannot_escape_storage_roots(
    tmp_path: Path,
) -> None:
    with pytest.raises(Slice2ArtifactError, match="identity"):
        start_prospective_cohort(
            tmp_path,
            _cohort(),
            cohort_id_override="../escape",
        )

    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    with pytest.raises(Slice2ArtifactError, match="identity"):
        start_checkpoint(
            cohort_root,
            _checkpoint(),
            checkpoint_id_override="../escape",
        )


def test_checkpoint_partial_is_recoverable_and_not_complete(tmp_path: Path) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint()
    generation = start_checkpoint(cohort_root, checkpoint)

    assert generation.staging_directory.name.endswith(".partial")
    assert (generation.staging_directory / CHECKPOINT_TABLE).is_file()
    assert not (generation.staging_directory / MANIFEST).exists()
    assert read_completed_checkpoints(cohort_root) == ()
    assert start_checkpoint(cohort_root, checkpoint) == generation


def test_checkpoint_publication_preserves_unfillable_evidence_and_indices(
    tmp_path: Path,
) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint()
    generation = start_checkpoint(cohort_root, checkpoint)
    write_checkpoint_evidence(
        generation,
        observations=(_observation(checkpoint),),
        liquidity=(_liquidity(checkpoint),),
        qualifications=(_qualification(checkpoint),),
    )

    final = publish_checkpoint(generation)

    liquidity = pq.read_table(final / LIQUIDITY_TABLE).to_pylist()
    qualification = pq.read_table(final / QUALIFICATION_TABLE).to_pylist()
    assert liquidity[0]["fillable"] is False
    assert liquidity[0]["quote_notional"] == "100"
    assert liquidity[0]["book_price_impact_bps"] is None
    assert qualification[0]["qualification_state"] == "research_only"
    assert qualification[0]["requested_capital"] == "500"
    manifest = json.loads((final / MANIFEST).read_text(encoding="utf-8"))
    assert manifest["checkpoint_id"] == checkpoint.checkpoint_id
    assert manifest["table_counts"] == {
        CHECKPOINT_TABLE: 1,
        LIQUIDITY_TABLE: 1,
        QUALIFICATION_TABLE: 1,
    }
    checkpoint_index = pq.read_table(cohort_root / CHECKPOINTS_INDEX).to_pylist()
    outcome_index = pq.read_table(cohort_root / OUTCOMES_INDEX).to_pylist()
    assert len(checkpoint_index) == 1
    assert checkpoint_index[0]["checkpoint_id"] == checkpoint.checkpoint_id
    assert outcome_index[0]["qualification_state"] == "research_only"
    assert read_completed_checkpoints(cohort_root) == (final,)


def test_checkpoint_resume_rejects_identity_mismatch(tmp_path: Path) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    first = _checkpoint()
    generation = start_checkpoint(cohort_root, first)
    assert generation.staging_directory.is_dir()

    changed = first.model_copy(
        update={"information_end": first.information_end + timedelta(seconds=1)}
    )
    with pytest.raises(Slice2ArtifactError, match="checkpoint definition"):
        start_checkpoint(
            cohort_root,
            changed,
            checkpoint_id_override=first.checkpoint_id,
        )


def test_completed_checkpoints_append_without_mutating_prior_evidence(
    tmp_path: Path,
) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    first = _checkpoint(1)
    first_generation = start_checkpoint(cohort_root, first)
    write_checkpoint_evidence(
        first_generation,
        observations=(_observation(first),),
        liquidity=(_liquidity(first),),
        qualifications=(_qualification(first),),
    )
    first_final = publish_checkpoint(first_generation)
    first_hash = sha256((first_final / MANIFEST).read_bytes()).hexdigest()

    second = _checkpoint(2)
    second_generation = start_checkpoint(cohort_root, second)
    write_checkpoint_evidence(
        second_generation,
        observations=(_observation(second),),
        liquidity=(_liquidity(second),),
        qualifications=(_qualification(second),),
    )
    second_final = publish_checkpoint(second_generation)

    assert read_completed_checkpoints(cohort_root) == (first_final, second_final)
    assert sha256((first_final / MANIFEST).read_bytes()).hexdigest() == first_hash
    assert pq.read_table(cohort_root / CHECKPOINTS_INDEX).num_rows == 2
    assert pq.read_table(cohort_root / OUTCOMES_INDEX).num_rows == 2


def test_existing_cohort_repairs_indices_after_post_publish_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qap.scanner.slice2_artifacts as artifacts

    cohort = _cohort()
    cohort_root = start_prospective_cohort(tmp_path, cohort)
    checkpoint = _checkpoint()
    generation = start_checkpoint(cohort_root, checkpoint)
    write_checkpoint_evidence(
        generation,
        observations=(_observation(checkpoint),),
        liquidity=(_liquidity(checkpoint),),
        qualifications=(_qualification(checkpoint),),
    )

    def fail_index_rebuild(_root: Path) -> None:
        raise Slice2ArtifactError("simulated index refresh interruption")

    monkeypatch.setattr(artifacts, "_rebuild_indices", fail_index_rebuild)
    with pytest.raises(Slice2ArtifactError, match="simulated index refresh"):
        publish_checkpoint(generation)

    assert generation.final_directory.is_dir()
    assert not (cohort_root / CHECKPOINTS_INDEX).exists()
    assert not (cohort_root / OUTCOMES_INDEX).exists()

    monkeypatch.undo()
    assert start_prospective_cohort(tmp_path, cohort) == cohort_root
    assert pq.read_table(cohort_root / CHECKPOINTS_INDEX).num_rows == 1
    assert pq.read_table(cohort_root / OUTCOMES_INDEX).num_rows == 1


def test_start_checkpoint_rejects_candidate_not_frozen_in_cohort(
    tmp_path: Path,
) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint().model_copy(update={"candidate_id": "e" * 64})

    with pytest.raises(Slice2ArtifactError, match="candidate is not frozen"):
        start_checkpoint(cohort_root, checkpoint)


def test_write_rejects_candidate_or_checkpoint_lineage_mismatch(tmp_path: Path) -> None:
    cohort_root = start_prospective_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint()
    generation = start_checkpoint(cohort_root, checkpoint)
    wrong = _qualification(checkpoint)
    wrong = wrong.__class__(
        checkpoint_id="f" * 64,
        candidate_id=wrong.candidate_id,
        as_of=wrong.as_of,
        requested_capital=wrong.requested_capital,
        q_star_buy=wrong.q_star_buy,
        q_safe_buy=wrong.q_safe_buy,
        q_star_sell=wrong.q_star_sell,
        q_safe_sell=wrong.q_safe_sell,
        current_base_weight=wrong.current_base_weight,
        required_buy_fraction=wrong.required_buy_fraction,
        required_sell_fraction=wrong.required_sell_fraction,
        candidate_capital_ceiling=wrong.candidate_capital_ceiling,
        qualification_state=wrong.qualification_state,
        reason=wrong.reason,
        capture_contract_satisfied=wrong.capture_contract_satisfied,
        current_two_way_trading=wrong.current_two_way_trading,
        order_constraints_satisfied=wrong.order_constraints_satisfied,
        economic_gates_at_requested_capital=wrong.economic_gates_at_requested_capital,
        lower_tested_capital=wrong.lower_tested_capital,
        economic_gates_at_lower_capital=wrong.economic_gates_at_lower_capital,
    )

    with pytest.raises(Slice2ArtifactError, match="checkpoint lineage"):
        write_checkpoint_evidence(
            generation,
            observations=(_observation(checkpoint),),
            liquidity=(_liquidity(checkpoint),),
            qualifications=(wrong,),
        )
