# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Recoverable immutable evidence artifacts for Scanner-V1 Slice 2."""

import json
import os
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from qap.scanner.liquidity_policy import QualificationReason, QualificationState
from qap.scanner.prospective import ProspectiveCheckpoint, ProspectiveCohort
from qap.scanner.slice2_artifact_contract import (
    CHECKPOINT_DIRECTORY,
    CHECKPOINT_TABLE,
    CHECKPOINTS_INDEX,
    COHORT_DEFINITION,
    FREEZES_TABLE,
    LIQUIDITY_TABLE,
    MANIFEST,
    OUTCOMES_INDEX,
    QUALIFICATION_TABLE,
)
from qap.scanner.slice2_artifact_schemas import (
    CHECKPOINT_SCHEMA,
    FREEZE_SCHEMA,
    LIQUIDITY_SCHEMA,
    OUTCOME_INDEX_SCHEMA,
    QUALIFICATION_SCHEMA,
)


class Slice2ArtifactError(ValueError):
    """Raised when prospective evidence cannot be published without ambiguity."""


def _identity(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise Slice2ArtifactError(f"{field} identity must be a SHA-256 fingerprint")
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
        raise Slice2ArtifactError(f"failed to publish {path.name}") from exc


def _write_table(path: Path, table: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        pq.write_table(table, temporary)
        os.replace(temporary, path)
    except (OSError, pa.ArrowException) as exc:
        temporary.unlink(missing_ok=True)
        raise Slice2ArtifactError(f"failed to write {path.name}") from exc


def _read_table(path: Path, schema: Any) -> Any:
    try:
        table = pq.read_table(path)
    except (OSError, pa.ArrowException) as exc:
        raise Slice2ArtifactError(f"table is malformed: {path.name}") from exc
    if not table.schema.equals(schema):
        raise Slice2ArtifactError(f"table schema mismatch: {path.name}")
    return table


@dataclass(frozen=True, slots=True)
class CheckpointObservationRecord:
    checkpoint_id: str
    cohort_id: str
    candidate_id: str
    checkpoint_index: int
    freeze_at: datetime
    evidence_window_start: datetime
    evidence_window_end: datetime
    information_end: datetime
    forward_slices_json: str
    evidence_role: str
    slice2_protocol_version: str
    protocol_identity: str
    prospective_complete: bool
    prospective_status: str
    authoritative_run_id: str | None

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: ProspectiveCheckpoint,
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
            checkpoint_index=checkpoint.checkpoint_index,
            freeze_at=checkpoint.freeze_at,
            evidence_window_start=checkpoint.evidence_window_start,
            evidence_window_end=checkpoint.evidence_window_end,
            information_end=checkpoint.information_end,
            forward_slices_json=_json_bytes(slices).decode("utf-8"),
            evidence_role=checkpoint.evidence_role,
            slice2_protocol_version=checkpoint.slice2_protocol_version,
            protocol_identity=checkpoint.protocol_identity,
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
class Slice2CheckpointGeneration:
    cohort_root: Path
    checkpoint: ProspectiveCheckpoint
    staging_directory: Path
    final_directory: Path


def _cohort_payload(cohort: ProspectiveCohort) -> dict[str, object]:
    payload = cohort.model_dump(mode="json")
    payload["cohort_id"] = cohort.cohort_id
    payload["candidate_ids"] = list(cohort.candidate_ids)
    return payload


def _freeze_table(cohort: ProspectiveCohort) -> Any:
    rows = [
        {
            "cohort_id": cohort.cohort_id,
            "candidate_id": item.candidate_id,
            "deep_replay_run_id": item.deep_replay_run_id,
            "slice1_economic_gate_status": item.slice1_economic_gate_status,
            "freeze_at": cohort.freeze_at,
            "source_scan_id": cohort.source_scan_id,
            "slice2_protocol_version": cohort.slice2_protocol_version,
            "protocol_identity": cohort.protocol_identity,
        }
        for item in cohort.candidates
    ]
    return pa.Table.from_pylist(rows, schema=FREEZE_SCHEMA)


def _verify_cohort_root(root: Path, cohort: ProspectiveCohort) -> None:
    definition = root / COHORT_DEFINITION
    freezes = root / FREEZES_TABLE
    if not definition.is_file() or not freezes.is_file():
        raise Slice2ArtifactError("cohort definition is incomplete")
    if definition.read_bytes() != _json_bytes(_cohort_payload(cohort)):
        raise Slice2ArtifactError("cohort definition does not match frozen identity")
    if not _read_table(freezes, FREEZE_SCHEMA).equals(_freeze_table(cohort)):
        raise Slice2ArtifactError("cohort freeze table does not match frozen identity")


def start_prospective_cohort(
    run_root: str | Path,
    cohort: ProspectiveCohort,
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
        raise Slice2ArtifactError("cohort definition is malformed") from exc
    if not isinstance(payload, dict):
        raise Slice2ArtifactError("cohort definition is malformed")
    return payload


def _checkpoint_row(checkpoint: ProspectiveCheckpoint) -> dict[str, object]:
    slices = [item.model_dump(mode="json") for item in checkpoint.forward_slices]
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "cohort_id": checkpoint.cohort_id,
        "candidate_id": checkpoint.candidate_id,
        "checkpoint_index": checkpoint.checkpoint_index,
        "freeze_at": checkpoint.freeze_at,
        "evidence_window_start": checkpoint.evidence_window_start,
        "evidence_window_end": checkpoint.evidence_window_end,
        "information_end": checkpoint.information_end,
        "forward_slices_json": _json_bytes(slices).decode("utf-8"),
        "evidence_role": checkpoint.evidence_role,
        "slice2_protocol_version": checkpoint.slice2_protocol_version,
        "protocol_identity": checkpoint.protocol_identity,
        "prospective_complete": False,
        "prospective_status": "enumerated",
        "authoritative_run_id": None,
    }


def start_checkpoint(
    cohort_root: str | Path,
    checkpoint: ProspectiveCheckpoint,
    *,
    checkpoint_id_override: str | None = None,
) -> Slice2CheckpointGeneration:
    """Create or resume one immutable checkpoint staging generation."""

    root = Path(cohort_root).resolve()
    payload = _load_cohort_payload(root)
    if payload.get("cohort_id") != checkpoint.cohort_id:
        raise Slice2ArtifactError("checkpoint cohort identity mismatch")
    candidate_ids = payload.get("candidate_ids")
    if (
        not isinstance(candidate_ids, list)
        or checkpoint.candidate_id not in candidate_ids
    ):
        raise Slice2ArtifactError("checkpoint candidate is not frozen in cohort")
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
        raise Slice2ArtifactError("completed checkpoint is immutable")
    definition_path = staging / CHECKPOINT_TABLE
    expected = _checkpoint_row(checkpoint)
    if staging.exists():
        if identity != checkpoint.checkpoint_id or not definition_path.is_file():
            raise Slice2ArtifactError("checkpoint definition does not match request")
        table = _read_table(definition_path, CHECKPOINT_SCHEMA)
        if table.num_rows != 1:
            raise Slice2ArtifactError("checkpoint definition does not match request")
        stored = table.to_pylist()[0]
        for key, value in expected.items():
            if key in {
                "prospective_complete",
                "prospective_status",
                "authoritative_run_id",
            }:
                continue
            if stored[key] != value:
                raise Slice2ArtifactError(
                    "checkpoint definition does not match request"
                )
        return Slice2CheckpointGeneration(root, checkpoint, staging, final)
    staging.mkdir(parents=True, exist_ok=False)
    _write_table(
        definition_path,
        pa.Table.from_pylist([expected], schema=CHECKPOINT_SCHEMA),
    )
    return Slice2CheckpointGeneration(root, checkpoint, staging, final)


def _observation_table(records: tuple[CheckpointObservationRecord, ...]) -> Any:
    rows = [
        {
            "checkpoint_id": record.checkpoint_id,
            "cohort_id": record.cohort_id,
            "candidate_id": record.candidate_id,
            "checkpoint_index": record.checkpoint_index,
            "freeze_at": record.freeze_at,
            "evidence_window_start": record.evidence_window_start,
            "evidence_window_end": record.evidence_window_end,
            "information_end": record.information_end,
            "forward_slices_json": record.forward_slices_json,
            "evidence_role": record.evidence_role,
            "slice2_protocol_version": record.slice2_protocol_version,
            "protocol_identity": record.protocol_identity,
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
    generation: Slice2CheckpointGeneration,
    observations: tuple[CheckpointObservationRecord, ...],
    liquidity: tuple[LiquidityEvidenceRecord, ...],
    qualifications: tuple[CapacityQualificationRecord, ...],
) -> None:
    checkpoint = generation.checkpoint
    if len(observations) != 1 or len(qualifications) != 1:
        raise Slice2ArtifactError(
            "checkpoint requires one observation and qualification row"
        )
    for row in (*observations, *liquidity, *qualifications):
        if (
            getattr(row, "checkpoint_id", None) != checkpoint.checkpoint_id
            or getattr(row, "candidate_id", None) != checkpoint.candidate_id
        ):
            raise Slice2ArtifactError("checkpoint lineage mismatch")
    if observations[0].cohort_id != checkpoint.cohort_id:
        raise Slice2ArtifactError("checkpoint lineage mismatch")
    if qualifications[0].as_of != checkpoint.information_end:
        raise Slice2ArtifactError(
            "qualification timestamp must match checkpoint cutoff"
        )


def write_checkpoint_evidence(
    generation: Slice2CheckpointGeneration,
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
            raise Slice2ArtifactError(f"checkpoint is missing {name}")
        tables[name] = _read_table(path, schema)
    return tables


def _reconcile(generation: Slice2CheckpointGeneration, tables: dict[str, Any]) -> None:
    if (
        tables[CHECKPOINT_TABLE].num_rows != 1
        or tables[QUALIFICATION_TABLE].num_rows != 1
    ):
        raise Slice2ArtifactError("checkpoint row counts do not reconcile")
    for name, table in tables.items():
        for row in table.to_pylist():
            if row["checkpoint_id"] != generation.checkpoint.checkpoint_id:
                raise Slice2ArtifactError(f"{name} checkpoint lineage mismatch")
            if row["candidate_id"] != generation.checkpoint.candidate_id:
                raise Slice2ArtifactError(f"{name} candidate lineage mismatch")


def _table_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _completed_generation_dirs(cohort_root: Path) -> tuple[Path, ...]:
    root = cohort_root / CHECKPOINT_DIRECTORY
    if not root.is_dir():
        return ()
    completed: list[tuple[int, Path]] = []
    for path in root.iterdir():
        if not path.is_dir() or path.name.endswith(".partial"):
            continue
        manifest = path / MANIFEST
        if not manifest.is_file():
            continue
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            index = int(payload["checkpoint_index"])
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise Slice2ArtifactError(
                "completed checkpoint manifest is malformed"
            ) from exc
        completed.append((index, path))
    completed.sort(key=lambda item: (item[0], item[1].name))
    return tuple(path for _index, path in completed)


def _rebuild_indices(cohort_root: Path) -> None:
    checkpoint_rows: list[dict[str, object]] = []
    outcome_rows: list[dict[str, object]] = []
    for directory in _completed_generation_dirs(cohort_root):
        tables = _required_tables(directory)
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


def publish_checkpoint(generation: Slice2CheckpointGeneration) -> Path:
    """Reconcile and atomically publish one completed checkpoint generation."""

    if generation.final_directory.exists():
        raise Slice2ArtifactError("completed checkpoint publication collision")
    tables = _required_tables(generation.staging_directory)
    _reconcile(generation, tables)
    table_counts = {name: table.num_rows for name, table in tables.items()}
    table_hashes = {
        name: _table_hash(generation.staging_directory / name) for name in tables
    }
    observation = tables[CHECKPOINT_TABLE].to_pylist()[0]
    qualification = tables[QUALIFICATION_TABLE].to_pylist()[0]
    manifest = {
        "schema_version": "qap.scanner.prospective-checkpoint-manifest.v1",
        "cohort_id": generation.checkpoint.cohort_id,
        "checkpoint_id": generation.checkpoint.checkpoint_id,
        "candidate_id": generation.checkpoint.candidate_id,
        "checkpoint_index": generation.checkpoint.checkpoint_index,
        "slice2_protocol_version": generation.checkpoint.slice2_protocol_version,
        "protocol_identity": generation.checkpoint.protocol_identity,
        "prospective_status": observation["prospective_status"],
        "authoritative_run_id": observation["authoritative_run_id"],
        "qualification_state": qualification["qualification_state"],
        "table_counts": dict(sorted(table_counts.items())),
        "table_hashes": dict(sorted(table_hashes.items())),
        "published_at": datetime.now(UTC).isoformat(),
    }
    manifest_path = generation.staging_directory / MANIFEST
    _atomic_write_bytes(manifest_path, _json_bytes(manifest))
    reread = json.loads(manifest_path.read_text(encoding="utf-8"))
    reread_tables = _required_tables(generation.staging_directory)
    _reconcile(generation, reread_tables)
    if reread["table_counts"] != {
        name: table.num_rows for name, table in reread_tables.items()
    }:
        raise Slice2ArtifactError("checkpoint manifest table counts do not reconcile")
    if reread["table_hashes"] != {
        name: _table_hash(generation.staging_directory / name) for name in reread_tables
    }:
        raise Slice2ArtifactError("checkpoint manifest table hashes do not reconcile")
    generation.final_directory.parent.mkdir(parents=True, exist_ok=True)
    os.replace(generation.staging_directory, generation.final_directory)
    _rebuild_indices(generation.cohort_root)
    return generation.final_directory


def read_completed_checkpoints(cohort_root: str | Path) -> tuple[Path, ...]:
    """Return manifest-bearing checkpoint generations, never partial state."""

    return _completed_generation_dirs(Path(cohort_root).resolve())


__all__ = [
    "CapacityQualificationRecord",
    "CheckpointObservationRecord",
    "LiquidityEvidenceRecord",
    "Slice2ArtifactError",
    "Slice2CheckpointGeneration",
    "publish_checkpoint",
    "read_completed_checkpoints",
    "start_checkpoint",
    "start_prospective_cohort",
    "write_checkpoint_evidence",
]
