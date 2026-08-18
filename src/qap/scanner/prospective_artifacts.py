# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Recoverable immutable artifacts for scanner prospective evidence."""

import json
import os
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from qap.artifact_integrity import (
    INTEGRITY_FILE,
    ArtifactIntegrity,
    build_integrity_record,
)
from qap.scanner.liquidity_policy import QualificationReason, QualificationState
from qap.scanner.prospective import ForwardCheckpoint, ForwardCohort
from qap.scanner.prospective_artifact_schemas import (
    CHECKPOINT_AUTHORITATIVE_FILES,
    CHECKPOINT_DIRECTORY,
    CHECKPOINT_SCHEMA,
    CHECKPOINT_TABLE,
    CHECKPOINTS_INDEX,
    COHORT_DEFINITION,
    FREEZE_SCHEMA,
    FREEZES_TABLE,
    LIQUIDITY_SCHEMA,
    LIQUIDITY_TABLE,
    MANIFEST,
    OUTCOME_INDEX_SCHEMA,
    OUTCOMES_INDEX,
    QUALIFICATION_SCHEMA,
    QUALIFICATION_TABLE,
)
from qap.scanner.prospective_integrity import (
    ProspectiveArtifactError,
    completed_generation_dirs,
    read_manifest,
    validate_completed_generation,
)


def _identity(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise ProspectiveArtifactError(
            f"{field} identity must be a SHA-256 fingerprint"
        )
    return normalized


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not value.is_finite():
        raise ValueError("persisted decimal values must be finite Decimal values")
    return format(value, "f")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise ProspectiveArtifactError(f"failed to publish {path.name}") from exc


def _write_table(path: Path, table: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        pq.write_table(table, temporary)
        os.replace(temporary, path)
    except (OSError, pa.ArrowException) as exc:
        temporary.unlink(missing_ok=True)
        raise ProspectiveArtifactError(f"failed to write {path.name}") from exc


def _read_table(path: Path, schema: Any) -> Any:
    try:
        table = pq.read_table(path)
    except (OSError, pa.ArrowException) as exc:
        raise ProspectiveArtifactError(f"table is malformed: {path.name}") from exc
    if not table.schema.equals(schema):
        raise ProspectiveArtifactError(f"table schema mismatch: {path.name}")
    return table


@dataclass(frozen=True, slots=True)
class CheckpointObservationRecord:
    checkpoint_id: str
    cohort_id: str
    candidate_id: str
    freeze_id: str
    checkpoint_index: int
    freeze_at: datetime
    eligible_information_end: datetime
    forward_start: datetime
    first_outcome_complete_at: datetime
    evidence_window_start: datetime
    evidence_window_end: datetime
    information_end: datetime
    forward_slices_json: str
    evidence_role: str
    prospective_protocol_version: str
    prospective_protocol_identity: str
    prospective_complete: bool
    prospective_status: str
    authoritative_run_id: str | None

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: ForwardCheckpoint,
        *,
        prospective_complete: bool,
        prospective_status: str,
        authoritative_run_id: str | None,
    ) -> "CheckpointObservationRecord":
        slices = [item.model_dump(mode="json") for item in checkpoint.forward_slices]
        return cls(
            checkpoint_id=checkpoint.checkpoint_id,
            cohort_id=checkpoint.cohort_id,
            candidate_id=checkpoint.candidate_id,
            freeze_id=checkpoint.freeze_id,
            checkpoint_index=checkpoint.checkpoint_index,
            freeze_at=checkpoint.freeze_at,
            eligible_information_end=checkpoint.eligible_information_end,
            forward_start=checkpoint.forward_start,
            first_outcome_complete_at=checkpoint.first_outcome_complete_at,
            evidence_window_start=checkpoint.evidence_window_start,
            evidence_window_end=checkpoint.evidence_window_end,
            information_end=checkpoint.information_end,
            forward_slices_json=_json_bytes(slices).decode("utf-8"),
            evidence_role=checkpoint.evidence_role,
            prospective_protocol_version=checkpoint.prospective_protocol_version,
            prospective_protocol_identity=checkpoint.prospective_protocol_identity,
            prospective_complete=prospective_complete,
            prospective_status=prospective_status.strip(),
            authoritative_run_id=(
                None if authoritative_run_id is None else authoritative_run_id.strip()
            ),
        )


@dataclass(frozen=True, slots=True)
class LiquidityEvidenceRecord:
    checkpoint_id: str
    candidate_id: str
    snapshot_id: str
    side: str
    quote_notional: Decimal
    fillable: bool
    fee_bps: Decimal
    book_price_impact_bps: Decimal | None
    total_friction_bps: Decimal | None


@dataclass(frozen=True, slots=True)
class CapacityQualificationRecord:
    checkpoint_id: str
    candidate_id: str
    as_of: datetime
    requested_capital: Decimal
    q_star_buy: Decimal | None
    q_safe_buy: Decimal | None
    q_star_sell: Decimal | None
    q_safe_sell: Decimal | None
    current_base_weight: Decimal | None
    required_buy_fraction: Decimal | None
    required_sell_fraction: Decimal | None
    candidate_capital_ceiling: Decimal | None
    qualification_state: QualificationState
    reason: QualificationReason
    capture_contract_satisfied: bool
    current_two_way_trading: bool
    order_constraints_satisfied: bool
    economic_gates_at_requested_capital: bool
    lower_tested_capital: Decimal | None
    economic_gates_at_lower_capital: bool


@dataclass(frozen=True, slots=True)
class ForwardCheckpointGeneration:
    cohort_root: Path
    checkpoint: ForwardCheckpoint
    staging_directory: Path
    final_directory: Path


def _cohort_payload(cohort: ForwardCohort) -> dict[str, object]:
    payload = cohort.model_dump(mode="json")
    payload["cohort_id"] = cohort.cohort_id
    payload["candidate_ids"] = list(cohort.candidate_ids)
    payload["checkpoint_freeze_ids"] = list(cohort.candidate_freeze_ids)
    return payload


def _freeze_table(cohort: ForwardCohort) -> Any:
    rows = [
        {
            "cohort_id": cohort.cohort_id,
            "freeze_id": item.freeze_id,
            "candidate_id": item.candidate_id,
            "scan_id": item.scan_id,
            "scanner_protocol_version": item.scanner_protocol_version,
            "scanner_protocol_identity": item.scanner_protocol_identity,
            "prospective_protocol_version": item.prospective_protocol_version,
            "prospective_protocol_identity": item.prospective_protocol_identity,
            "automatic_selected": item.automatic_selected,
            "manual_selected": item.manual_selected,
            "frozen_at": item.frozen_at,
            "eligible_information_end": item.eligible_information_end,
            "forward_start": item.forward_start,
            "forward_end": item.forward_end,
            "horizon": item.horizon.value,
            "venue": item.venue,
            "pair_id": item.pair_id,
            "orientation": item.orientation,
            "resolution": item.resolution,
            "model_family": item.model_family,
            "template_id": item.template_id,
            "model_parameters_json": _json_bytes(list(item.model_parameters)).decode(
                "utf-8"
            ),
            "source_artifact_fingerprints": list(item.source_artifact_fingerprints),
            "selection_slice_fingerprints": list(item.selection_slice_fingerprints),
            "universe_snapshot_id": item.universe_snapshot_id,
            "cost_policy_reference": item.cost_policy_reference,
            "primary_control_reference": item.primary_control_reference,
            "candidate_deep_replay_run_id": item.candidate_deep_replay_run_id,
            "candidate_deep_replay_gate_status": (
                item.candidate_deep_replay_gate_status
            ),
        }
        for item in cohort.candidate_freezes
    ]
    return pa.Table.from_pylist(rows, schema=FREEZE_SCHEMA)


def _verify_cohort_root(root: Path, cohort: ForwardCohort) -> None:
    definition = root / COHORT_DEFINITION
    freezes = root / FREEZES_TABLE
    if not definition.is_file() or not freezes.is_file():
        raise ProspectiveArtifactError("cohort definition is incomplete")
    if definition.read_bytes() != _json_bytes(_cohort_payload(cohort)):
        raise ProspectiveArtifactError(
            "cohort definition does not match frozen identity"
        )
    if not _read_table(freezes, FREEZE_SCHEMA).equals(_freeze_table(cohort)):
        raise ProspectiveArtifactError(
            "cohort freeze table does not match frozen identity"
        )


def start_forward_cohort(
    run_root: str | Path,
    cohort: ForwardCohort,
    *,
    cohort_id_override: str | None = None,
) -> Path:
    """Atomically publish cohort/freeze identity before forward evidence exists."""

    identity = _identity(
        cohort.cohort_id if cohort_id_override is None else cohort_id_override,
        field="cohort",
    )
    parent = Path(run_root).resolve() / "scanner-forward"
    final = parent / identity
    staging = parent / f"{identity}.partial"
    if final.exists():
        _verify_cohort_root(final, cohort)
        _rebuild_indices(final)
        return final
    if staging.exists():
        _verify_cohort_root(staging, cohort)
        os.replace(staging, final)
        return final
    staging.mkdir(parents=True, exist_ok=False)
    try:
        _atomic_write_bytes(
            staging / COHORT_DEFINITION,
            _json_bytes(_cohort_payload(cohort)),
        )
        _write_table(staging / FREEZES_TABLE, _freeze_table(cohort))
        os.replace(staging, final)
    except BaseException:
        if staging.exists():
            for path in staging.iterdir():
                path.unlink(missing_ok=True)
            staging.rmdir()
        raise
    return final


def _load_cohort_payload(root: Path) -> dict[str, object]:
    path = root / COHORT_DEFINITION
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProspectiveArtifactError("cohort definition is malformed") from exc
    if not isinstance(payload, dict):
        raise ProspectiveArtifactError("cohort definition is malformed")
    return payload


def _checkpoint_row(checkpoint: ForwardCheckpoint) -> dict[str, object]:
    slices = [item.model_dump(mode="json") for item in checkpoint.forward_slices]
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "cohort_id": checkpoint.cohort_id,
        "candidate_id": checkpoint.candidate_id,
        "freeze_id": checkpoint.freeze_id,
        "checkpoint_index": checkpoint.checkpoint_index,
        "freeze_at": checkpoint.freeze_at,
        "eligible_information_end": checkpoint.eligible_information_end,
        "forward_start": checkpoint.forward_start,
        "first_outcome_complete_at": checkpoint.first_outcome_complete_at,
        "evidence_window_start": checkpoint.evidence_window_start,
        "evidence_window_end": checkpoint.evidence_window_end,
        "information_end": checkpoint.information_end,
        "forward_slices_json": _json_bytes(slices).decode("utf-8"),
        "evidence_role": checkpoint.evidence_role,
        "prospective_protocol_version": checkpoint.prospective_protocol_version,
        "prospective_protocol_identity": checkpoint.prospective_protocol_identity,
        "prospective_complete": False,
        "prospective_status": "enumerated",
        "authoritative_run_id": None,
    }


def start_checkpoint(
    cohort_root: str | Path,
    checkpoint: ForwardCheckpoint,
    *,
    checkpoint_id_override: str | None = None,
) -> ForwardCheckpointGeneration:
    """Create or resume one immutable checkpoint staging generation."""

    root = Path(cohort_root).resolve()
    payload = _load_cohort_payload(root)
    if payload.get("cohort_id") != checkpoint.cohort_id:
        raise ProspectiveArtifactError("checkpoint cohort identity mismatch")
    freeze_ids = payload.get("checkpoint_freeze_ids")
    if not isinstance(freeze_ids, list) or checkpoint.freeze_id not in freeze_ids:
        raise ProspectiveArtifactError("checkpoint freeze is not owned by cohort")
    freeze_rows = _read_table(root / FREEZES_TABLE, FREEZE_SCHEMA).to_pylist()
    freeze_row = next(
        (row for row in freeze_rows if row["freeze_id"] == checkpoint.freeze_id),
        None,
    )
    if freeze_row is None or freeze_row["candidate_id"] != checkpoint.candidate_id:
        raise ProspectiveArtifactError("checkpoint candidate/freeze lineage mismatch")
    completed_indices = [
        manifest["checkpoint_index"]
        for directory in completed_generation_dirs(root)
        for manifest in [read_manifest(directory)]
        if manifest.get("freeze_id") == checkpoint.freeze_id
        and isinstance(manifest["checkpoint_index"], int)
        and not isinstance(manifest["checkpoint_index"], bool)
    ]
    if completed_indices and checkpoint.checkpoint_index <= max(completed_indices):
        raise ProspectiveArtifactError(
            "checkpoint index must advance monotonically for the freeze"
        )
    identity = _identity(
        (
            checkpoint.checkpoint_id
            if checkpoint_id_override is None
            else checkpoint_id_override
        ),
        field="checkpoint",
    )
    generations = root / CHECKPOINT_DIRECTORY
    final = generations / f"{checkpoint.checkpoint_index:04d}-{identity}"
    staging = final.with_name(f"{final.name}.partial")
    if final.exists():
        raise ProspectiveArtifactError("completed checkpoint is immutable")
    definition_path = staging / CHECKPOINT_TABLE
    expected = _checkpoint_row(checkpoint)
    if staging.exists():
        if identity != checkpoint.checkpoint_id or not definition_path.is_file():
            raise ProspectiveArtifactError(
                "checkpoint definition does not match request"
            )
        table = _read_table(definition_path, CHECKPOINT_SCHEMA)
        if table.num_rows != 1:
            raise ProspectiveArtifactError(
                "checkpoint definition does not match request"
            )
        stored = table.to_pylist()[0]
        for key, value in expected.items():
            if key in {
                "prospective_complete",
                "prospective_status",
                "authoritative_run_id",
            }:
                continue
            if stored[key] != value:
                raise ProspectiveArtifactError(
                    "checkpoint definition does not match request"
                )
        return ForwardCheckpointGeneration(root, checkpoint, staging, final)
    staging.mkdir(parents=True, exist_ok=False)
    _write_table(
        definition_path,
        pa.Table.from_pylist([expected], schema=CHECKPOINT_SCHEMA),
    )
    return ForwardCheckpointGeneration(root, checkpoint, staging, final)


def _observation_table(records: tuple[CheckpointObservationRecord, ...]) -> Any:
    rows = [
        {
            "checkpoint_id": record.checkpoint_id,
            "cohort_id": record.cohort_id,
            "candidate_id": record.candidate_id,
            "freeze_id": record.freeze_id,
            "checkpoint_index": record.checkpoint_index,
            "freeze_at": record.freeze_at,
            "eligible_information_end": record.eligible_information_end,
            "forward_start": record.forward_start,
            "first_outcome_complete_at": record.first_outcome_complete_at,
            "evidence_window_start": record.evidence_window_start,
            "evidence_window_end": record.evidence_window_end,
            "information_end": record.information_end,
            "forward_slices_json": record.forward_slices_json,
            "evidence_role": record.evidence_role,
            "prospective_protocol_version": record.prospective_protocol_version,
            "prospective_protocol_identity": record.prospective_protocol_identity,
            "prospective_complete": record.prospective_complete,
            "prospective_status": record.prospective_status,
            "authoritative_run_id": record.authoritative_run_id,
        }
        for record in records
    ]
    return pa.Table.from_pylist(rows, schema=CHECKPOINT_SCHEMA)


def _liquidity_table(records: tuple[LiquidityEvidenceRecord, ...]) -> Any:
    rows = [
        {
            "checkpoint_id": item.checkpoint_id,
            "candidate_id": item.candidate_id,
            "snapshot_id": item.snapshot_id,
            "side": item.side,
            "quote_notional": _decimal_text(item.quote_notional),
            "fillable": item.fillable,
            "fee_bps": _decimal_text(item.fee_bps),
            "book_price_impact_bps": _decimal_text(item.book_price_impact_bps),
            "total_friction_bps": _decimal_text(item.total_friction_bps),
        }
        for item in records
    ]
    return pa.Table.from_pylist(rows, schema=LIQUIDITY_SCHEMA)


def _qualification_table(records: tuple[CapacityQualificationRecord, ...]) -> Any:
    rows = [
        {
            "checkpoint_id": item.checkpoint_id,
            "candidate_id": item.candidate_id,
            "as_of": item.as_of,
            "requested_capital": _decimal_text(item.requested_capital),
            "q_star_buy": _decimal_text(item.q_star_buy),
            "q_safe_buy": _decimal_text(item.q_safe_buy),
            "q_star_sell": _decimal_text(item.q_star_sell),
            "q_safe_sell": _decimal_text(item.q_safe_sell),
            "current_base_weight": _decimal_text(item.current_base_weight),
            "required_buy_fraction": _decimal_text(item.required_buy_fraction),
            "required_sell_fraction": _decimal_text(item.required_sell_fraction),
            "candidate_capital_ceiling": _decimal_text(item.candidate_capital_ceiling),
            "qualification_state": item.qualification_state.value,
            "reason": item.reason.value,
            "capture_contract_satisfied": item.capture_contract_satisfied,
            "current_two_way_trading": item.current_two_way_trading,
            "order_constraints_satisfied": item.order_constraints_satisfied,
            "economic_gates_at_requested_capital": (
                item.economic_gates_at_requested_capital
            ),
            "lower_tested_capital": _decimal_text(item.lower_tested_capital),
            "economic_gates_at_lower_capital": item.economic_gates_at_lower_capital,
        }
        for item in records
    ]
    return pa.Table.from_pylist(rows, schema=QUALIFICATION_SCHEMA)


def _validate_lineage(
    generation: ForwardCheckpointGeneration,
    observations: tuple[CheckpointObservationRecord, ...],
    liquidity: tuple[LiquidityEvidenceRecord, ...],
    qualifications: tuple[CapacityQualificationRecord, ...],
) -> None:
    checkpoint = generation.checkpoint
    if len(observations) != 1 or len(qualifications) != 1:
        raise ProspectiveArtifactError(
            "checkpoint requires one observation and qualification row"
        )
    for row in (*observations, *liquidity, *qualifications):
        if (
            getattr(row, "checkpoint_id", None) != checkpoint.checkpoint_id
            or getattr(row, "candidate_id", None) != checkpoint.candidate_id
        ):
            raise ProspectiveArtifactError("checkpoint lineage mismatch")
    if observations[0].cohort_id != checkpoint.cohort_id:
        raise ProspectiveArtifactError("checkpoint lineage mismatch")
    if qualifications[0].as_of != checkpoint.information_end:
        raise ProspectiveArtifactError(
            "qualification timestamp must match checkpoint cutoff"
        )


def write_checkpoint_evidence(
    generation: ForwardCheckpointGeneration,
    *,
    observations: tuple[CheckpointObservationRecord, ...],
    liquidity: tuple[LiquidityEvidenceRecord, ...],
    qualifications: tuple[CapacityQualificationRecord, ...],
) -> None:
    """Persist evidence while the checkpoint remains recoverable partial state."""

    _validate_lineage(generation, observations, liquidity, qualifications)
    _write_table(
        generation.staging_directory / CHECKPOINT_TABLE,
        _observation_table(observations),
    )
    _write_table(
        generation.staging_directory / LIQUIDITY_TABLE,
        _liquidity_table(liquidity),
    )
    _write_table(
        generation.staging_directory / QUALIFICATION_TABLE,
        _qualification_table(qualifications),
    )


def _required_tables(directory: Path) -> dict[str, Any]:
    schemas = {
        CHECKPOINT_TABLE: CHECKPOINT_SCHEMA,
        LIQUIDITY_TABLE: LIQUIDITY_SCHEMA,
        QUALIFICATION_TABLE: QUALIFICATION_SCHEMA,
    }
    tables: dict[str, Any] = {}
    for name, schema in schemas.items():
        path = directory / name
        if not path.is_file():
            raise ProspectiveArtifactError(f"checkpoint is missing {name}")
        tables[name] = _read_table(path, schema)
    return tables


def _reconcile(generation: ForwardCheckpointGeneration, tables: dict[str, Any]) -> None:
    if (
        tables[CHECKPOINT_TABLE].num_rows != 1
        or tables[QUALIFICATION_TABLE].num_rows != 1
    ):
        raise ProspectiveArtifactError("checkpoint row counts do not reconcile")
    for name, table in tables.items():
        for row in table.to_pylist():
            if row["checkpoint_id"] != generation.checkpoint.checkpoint_id:
                raise ProspectiveArtifactError(f"{name} checkpoint lineage mismatch")
            if row["candidate_id"] != generation.checkpoint.candidate_id:
                raise ProspectiveArtifactError(f"{name} candidate lineage mismatch")


def _write_integrity(directory: Path, *, checkpoint_id: str) -> ArtifactIntegrity:
    record = build_integrity_record(
        directory,
        artifact_id=checkpoint_id,
        file_names=tuple(sorted(CHECKPOINT_AUTHORITATIVE_FILES)),
    )
    _atomic_write_bytes(
        directory / INTEGRITY_FILE,
        (record.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return record


def _rebuild_indices(cohort_root: Path) -> None:
    checkpoint_rows: list[dict[str, object]] = []
    outcome_rows: list[dict[str, object]] = []
    for directory in completed_generation_dirs(cohort_root):
        _manifest, tables = validate_completed_generation(directory)
        checkpoint = tables[CHECKPOINT_TABLE].to_pylist()[0]
        qualification = tables[QUALIFICATION_TABLE].to_pylist()[0]
        checkpoint_rows.append(checkpoint)
        outcome_rows.append(
            {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "cohort_id": checkpoint["cohort_id"],
                "candidate_id": checkpoint["candidate_id"],
                "checkpoint_index": checkpoint["checkpoint_index"],
                "information_end": checkpoint["information_end"],
                "prospective_status": checkpoint["prospective_status"],
                "authoritative_run_id": checkpoint["authoritative_run_id"],
                "qualification_state": qualification["qualification_state"],
                "qualification_reason": qualification["reason"],
                "requested_capital": qualification["requested_capital"],
                "candidate_capital_ceiling": qualification["candidate_capital_ceiling"],
            }
        )
    _write_table(
        cohort_root / CHECKPOINTS_INDEX,
        pa.Table.from_pylist(checkpoint_rows, schema=CHECKPOINT_SCHEMA),
    )
    _write_table(
        cohort_root / OUTCOMES_INDEX,
        pa.Table.from_pylist(outcome_rows, schema=OUTCOME_INDEX_SCHEMA),
    )


def publish_checkpoint(generation: ForwardCheckpointGeneration) -> Path:
    """Reconcile and atomically publish one completed checkpoint generation."""

    if generation.final_directory.exists():
        raise ProspectiveArtifactError("completed checkpoint publication collision")
    tables = _required_tables(generation.staging_directory)
    _reconcile(generation, tables)
    table_counts = {name: table.num_rows for name, table in tables.items()}
    observation = tables[CHECKPOINT_TABLE].to_pylist()[0]
    qualification = tables[QUALIFICATION_TABLE].to_pylist()[0]
    manifest = {
        "schema_version": "qap.scanner.prospective-checkpoint-manifest.v1",
        "cohort_id": generation.checkpoint.cohort_id,
        "checkpoint_id": generation.checkpoint.checkpoint_id,
        "candidate_id": generation.checkpoint.candidate_id,
        "checkpoint_index": generation.checkpoint.checkpoint_index,
        "prospective_protocol_version": (
            generation.checkpoint.prospective_protocol_version
        ),
        "prospective_protocol_identity": (
            generation.checkpoint.prospective_protocol_identity
        ),
        "freeze_id": generation.checkpoint.freeze_id,
        "prospective_status": observation["prospective_status"],
        "authoritative_run_id": observation["authoritative_run_id"],
        "qualification_state": qualification["qualification_state"],
        "table_counts": dict(sorted(table_counts.items())),
        "published_at": datetime.now(UTC).isoformat(),
    }
    manifest_path = generation.staging_directory / MANIFEST
    _atomic_write_bytes(manifest_path, _json_bytes(manifest))
    _write_integrity(
        generation.staging_directory,
        checkpoint_id=generation.checkpoint.checkpoint_id,
    )
    validate_completed_generation(generation.staging_directory, allow_partial=True)
    generation.final_directory.parent.mkdir(parents=True, exist_ok=True)
    os.replace(generation.staging_directory, generation.final_directory)
    validate_completed_generation(generation.final_directory)
    _rebuild_indices(generation.cohort_root)
    return generation.final_directory


def read_completed_checkpoints(cohort_root: str | Path) -> tuple[Path, ...]:
    """Return manifest-bearing checkpoint generations, never partial state."""

    return completed_generation_dirs(Path(cohort_root).resolve())


__all__ = [
    "CapacityQualificationRecord",
    "CheckpointObservationRecord",
    "LiquidityEvidenceRecord",
    "ProspectiveArtifactError",
    "ForwardCheckpointGeneration",
    "publish_checkpoint",
    "read_completed_checkpoints",
    "start_checkpoint",
    "start_forward_cohort",
    "write_checkpoint_evidence",
]
