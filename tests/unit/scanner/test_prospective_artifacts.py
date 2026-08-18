# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import (
    CandidateFreeze,
    ForwardCheckpoint,
    ForwardOutcome,
    ForwardOutcomeStatus,
    enroll_forward_cohort,
)
from qap.scanner.prospective_artifacts import (
    CHECKPOINTS_INDEX,
    FREEZES_TABLE,
    INTEGRITY_FILE,
    LIQUIDITY_TABLE,
    OUTCOMES_INDEX,
    LiquidityEvidenceRecord,
    ProspectiveArtifactError,
    publish_checkpoint,
    read_completed_checkpoints,
    start_checkpoint,
    start_forward_cohort,
    write_checkpoint_evidence,
)
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity

FREEZE = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)
FORWARD_START = FREEZE + timedelta(hours=1)


def _freeze() -> CandidateFreeze:
    return CandidateFreeze(
        candidate_id="b" * 64,
        scan_id="a" * 64,
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        scanner_protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        prospective_protocol_version=PROSPECTIVE_V1.protocol_id,
        prospective_protocol_identity=prospective_protocol_identity(PROSPECTIVE_V1),
        automatic_selected=True,
        manual_selected=False,
        frozen_at=FREEZE,
        eligible_information_end=FREEZE,
        forward_start=FORWARD_START,
        forward_end=FORWARD_START + timedelta(hours=48),
        horizon=ScannerHorizon.SHORT,
        venue="binance",
        pair_id="BTC/ETH",
        orientation="BTC/ETH",
        resolution="1h",
        model_family="log_ratio_mean_reversion",
        template_id="fast",
        model_parameters=(("window_bars", "48"),),
        source_artifact_fingerprints=("c" * 64, "d" * 64),
        selection_slice_fingerprints=("1" * 64, "2" * 64),
        universe_snapshot_id="e" * 64,
        cost_policy_reference=PROSPECTIVE_V1.adverse_cost_reference,
        primary_control_reference=PROSPECTIVE_V1.primary_control_reference,
        candidate_deep_replay_run_id="slice1-run-b",
        candidate_deep_replay_gate_status="deep_replay_survivor",
    )


def _cohort():
    return enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE,
        selected_freezes=(_freeze(),),
    )


def _checkpoint(index: int) -> ForwardCheckpoint:
    freeze = _freeze()
    end = FORWARD_START + timedelta(hours=6 * index)
    return ForwardCheckpoint(
        cohort_id=_cohort().cohort_id,
        candidate_id=freeze.candidate_id,
        freeze_id=freeze.freeze_id,
        checkpoint_index=index,
        freeze_at=FREEZE,
        eligible_information_end=FREEZE,
        forward_start=FORWARD_START,
        first_outcome_complete_at=FORWARD_START + timedelta(hours=1),
        evidence_window_start=FORWARD_START,
        evidence_window_end=end,
        information_end=end,
        forward_slices=(
            ScanInputIdentity(
                dataset_id=f"forward-{index}",
                source_artifact_fingerprint="f" * 64,
                selection_slice_fingerprint=f"{index:x}" * 64,
            ),
        ),
        evidence_role="prospective",
        prospective_protocol_version=PROSPECTIVE_V1.protocol_id,
        prospective_protocol_identity=prospective_protocol_identity(PROSPECTIVE_V1),
        created_at=end + timedelta(seconds=1),
    )


def _outcome(checkpoint: ForwardCheckpoint) -> ForwardOutcome:
    return ForwardOutcome(
        freeze_id=checkpoint.freeze_id,
        candidate_id=checkpoint.candidate_id,
        checkpoint_id=checkpoint.checkpoint_id,
        prospective_protocol_version=checkpoint.prospective_protocol_version,
        prospective_protocol_identity=checkpoint.prospective_protocol_identity,
        status=ForwardOutcomeStatus.PARTIAL,
        through=checkpoint.information_end,
        qap_run_id="qap-forward-run",
        primary_control_reference=PROSPECTIVE_V1.primary_control_reference,
        cost_policy_reference=PROSPECTIVE_V1.adverse_cost_reference,
        strategy_vs_hodl=Decimal("0.01"),
        strategy_vs_primary_control=Decimal("0.005"),
        baseline_economic_gates_passed=True,
        adverse_economic_gates_passed=False,
    )


def _liquidity(checkpoint: ForwardCheckpoint) -> LiquidityEvidenceRecord:
    return LiquidityEvidenceRecord(
        checkpoint_id=checkpoint.checkpoint_id,
        candidate_id=checkpoint.candidate_id,
        snapshot_id="9" * 64,
        side="buy_base",
        quote_notional=Decimal("100"),
        fillable=False,
        fee_bps=Decimal("20"),
        book_price_impact_bps=None,
        total_friction_bps=None,
    )


def _publish(root: Path, checkpoint: ForwardCheckpoint) -> Path:
    generation = start_checkpoint(root, checkpoint)
    write_checkpoint_evidence(
        generation,
        outcome=_outcome(checkpoint),
        liquidity=(_liquidity(checkpoint),),
    )
    return publish_checkpoint(generation)


def test_cohort_freeze_precedes_partial_checkpoint(tmp_path: Path) -> None:
    cohort = _cohort()
    root = start_forward_cohort(tmp_path, cohort)
    assert pq.read_table(root / FREEZES_TABLE).num_rows == 1

    generation = start_checkpoint(root, _checkpoint(1))
    assert generation.staging_directory.name.endswith(".partial")
    assert read_completed_checkpoints(root) == ()


def test_completed_checkpoint_and_cohort_root_are_integrity_sealed(
    tmp_path: Path,
) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint(1)
    final = _publish(root, checkpoint)

    assert (root / INTEGRITY_FILE).is_file()
    assert (final / INTEGRITY_FILE).is_file()
    assert read_completed_checkpoints(root) == (final,)
    assert pq.read_table(root / CHECKPOINTS_INDEX).num_rows == 1
    assert pq.read_table(root / OUTCOMES_INDEX).num_rows == 1
    assert pq.read_table(final / LIQUIDITY_TABLE).to_pylist()[0]["fillable"] is False

    (root / CHECKPOINTS_INDEX).unlink()
    with pytest.raises(ProspectiveArtifactError, match="file set mismatch"):
        start_forward_cohort(tmp_path, _cohort())


def test_cohort_freeze_tamper_fails_before_checkpoint_start(tmp_path: Path) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    table = pq.read_table(root / FREEZES_TABLE).to_pylist()
    table[0]["freeze_id"] = "8" * 64
    pq.write_table(
        pq.read_table(root / FREEZES_TABLE).from_pylist(
            table, schema=pq.read_table(root / FREEZES_TABLE).schema
        ),
        root / FREEZES_TABLE,
    )

    forged = _checkpoint(1).model_copy(update={"freeze_id": "8" * 64})
    with pytest.raises(ProspectiveArtifactError, match="digest mismatch"):
        start_checkpoint(root, forged)


def test_completed_checkpoint_tamper_fails_before_reindex(tmp_path: Path) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    final = _publish(root, _checkpoint(1))
    table = pq.read_table(final / LIQUIDITY_TABLE).to_pylist()
    table[0]["quote_notional"] = "999"
    pq.write_table(
        pq.read_table(final / LIQUIDITY_TABLE).from_pylist(
            table, schema=pq.read_table(final / LIQUIDITY_TABLE).schema
        ),
        final / LIQUIDITY_TABLE,
    )

    with pytest.raises(ProspectiveArtifactError, match="digest mismatch"):
        read_completed_checkpoints(root)


def test_retroactive_checkpoint_backfill_is_rejected_per_freeze(tmp_path: Path) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    _publish(root, _checkpoint(2))

    with pytest.raises(ProspectiveArtifactError, match="monotonically"):
        start_checkpoint(root, _checkpoint(1))


def test_checkpoint_publication_is_append_only(tmp_path: Path) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    first = _publish(root, _checkpoint(1))
    first_manifest = (first / "manifest.json").read_bytes()
    second = _publish(root, _checkpoint(2))

    assert read_completed_checkpoints(root) == (first, second)
    assert (first / "manifest.json").read_bytes() == first_manifest
    assert pq.read_table(root / CHECKPOINTS_INDEX).num_rows == 2


def test_checkpoint_must_reference_owned_freeze(tmp_path: Path) -> None:
    root = start_forward_cohort(tmp_path, _cohort())
    checkpoint = _checkpoint(1).model_copy(update={"freeze_id": "8" * 64})
    with pytest.raises(ProspectiveArtifactError, match="freeze is not owned"):
        start_checkpoint(root, checkpoint)
