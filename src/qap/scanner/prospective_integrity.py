# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Validation for completed scanner prospective checkpoint generations."""

import json
import string
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from qap.artifact_integrity import read_and_validate_integrity
from qap.scanner.prospective import ForwardOutcome
from qap.scanner.prospective_artifact_schemas import (
    CHECKPOINT_AUTHORITATIVE_FILES,
    CHECKPOINT_DIRECTORY,
    CHECKPOINT_SCHEMA,
    CHECKPOINT_TABLE,
    LIQUIDITY_SCHEMA,
    LIQUIDITY_TABLE,
    MANIFEST,
    OUTCOME_FILE,
    QUALIFICATION_SCHEMA,
    QUALIFICATION_TABLE,
)


class ProspectiveArtifactError(ValueError):
    """Raised when prospective evidence cannot be trusted or published."""


def _identity(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ProspectiveArtifactError(f"{field} identity must be a string")
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise ProspectiveArtifactError(
            f"{field} identity must be a SHA-256 fingerprint"
        )
    return normalized


def _read_table(path: Path, schema: Any) -> Any:
    try:
        table = pq.read_table(path)
    except (OSError, pa.ArrowException) as exc:
        raise ProspectiveArtifactError(f"table is malformed: {path.name}") from exc
    if not table.schema.equals(schema):
        raise ProspectiveArtifactError(f"table schema mismatch: {path.name}")
    return table


def read_manifest(directory: Path) -> dict[str, object]:
    path = directory / MANIFEST
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProspectiveArtifactError(
            "completed checkpoint manifest is malformed"
        ) from exc
    if not isinstance(payload, dict):
        raise ProspectiveArtifactError("completed checkpoint manifest is malformed")
    return payload


def read_outcome(directory: Path) -> ForwardOutcome:
    path = directory / OUTCOME_FILE
    try:
        return ForwardOutcome.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProspectiveArtifactError("forward outcome is malformed") from exc


def validate_completed_generation(
    directory: Path,
    *,
    allow_partial: bool = False,
) -> tuple[dict[str, object], dict[str, Any]]:
    payload = read_manifest(directory)
    try:
        checkpoint_id = _identity(payload["checkpoint_id"], field="checkpoint")
        candidate_id = _identity(payload["candidate_id"], field="candidate")
        freeze_id = _identity(payload["freeze_id"], field="freeze")
        cohort_id = _identity(payload["cohort_id"], field="cohort")
        raw_index = payload["checkpoint_index"]
        if not isinstance(raw_index, int) or isinstance(raw_index, bool):
            raise TypeError
        index = raw_index
    except (KeyError, TypeError, ValueError) as exc:
        raise ProspectiveArtifactError(
            "completed checkpoint manifest is malformed"
        ) from exc
    expected_name = f"{index:04d}-{checkpoint_id}"
    valid_names = {expected_name}
    if allow_partial:
        valid_names.add(f"{expected_name}.partial")
    if index < 1 or directory.name not in valid_names:
        raise ProspectiveArtifactError(
            "completed checkpoint directory identity mismatch"
        )
    try:
        read_and_validate_integrity(
            directory,
            artifact_id=checkpoint_id,
            required_files=CHECKPOINT_AUTHORITATIVE_FILES,
            allowed_files=CHECKPOINT_AUTHORITATIVE_FILES,
        )
    except ValueError as exc:
        raise ProspectiveArtifactError(str(exc)) from exc

    schemas = {
        CHECKPOINT_TABLE: CHECKPOINT_SCHEMA,
        LIQUIDITY_TABLE: LIQUIDITY_SCHEMA,
        QUALIFICATION_TABLE: QUALIFICATION_SCHEMA,
    }
    tables = {
        name: _read_table(directory / name, schema) for name, schema in schemas.items()
    }
    counts = {name: table.num_rows for name, table in tables.items()}
    if payload.get("table_counts") != dict(sorted(counts.items())):
        raise ProspectiveArtifactError(
            "checkpoint manifest table counts do not reconcile"
        )

    checkpoint = tables[CHECKPOINT_TABLE].to_pylist()[0]
    outcome = read_outcome(directory)
    expected = {
        "checkpoint_id": checkpoint_id,
        "candidate_id": candidate_id,
        "freeze_id": freeze_id,
        "cohort_id": cohort_id,
        "checkpoint_index": index,
        "prospective_protocol_version": payload.get("prospective_protocol_version"),
        "prospective_protocol_identity": payload.get("prospective_protocol_identity"),
    }
    for key, value in expected.items():
        if checkpoint.get(key) != value:
            raise ProspectiveArtifactError(f"completed checkpoint {key} mismatch")
    if (
        outcome.checkpoint_id != checkpoint_id
        or outcome.candidate_id != candidate_id
        or outcome.freeze_id != freeze_id
        or outcome.prospective_protocol_version
        != payload.get("prospective_protocol_version")
        or outcome.prospective_protocol_identity
        != payload.get("prospective_protocol_identity")
        or outcome.through != checkpoint.get("information_end")
        or outcome.outcome_id != payload.get("outcome_id")
        or outcome.status.value != payload.get("outcome_status")
        or outcome.qap_run_id != payload.get("qap_run_id")
    ):
        raise ProspectiveArtifactError("forward outcome lineage mismatch")
    for name, table in tables.items():
        for row in table.to_pylist():
            if row["checkpoint_id"] != checkpoint_id:
                raise ProspectiveArtifactError(f"{name} checkpoint lineage mismatch")
            if row["candidate_id"] != candidate_id:
                raise ProspectiveArtifactError(f"{name} candidate lineage mismatch")
    return payload, tables


def completed_generation_dirs(cohort_root: Path) -> tuple[Path, ...]:
    root = cohort_root / CHECKPOINT_DIRECTORY
    if not root.is_dir():
        return ()
    completed: list[tuple[int, Path]] = []
    for path in root.iterdir():
        if not path.is_dir() or path.name.endswith(".partial"):
            continue
        if not (path / MANIFEST).is_file():
            continue
        payload, _tables = validate_completed_generation(path)
        raw_index = payload["checkpoint_index"]
        assert isinstance(raw_index, int) and not isinstance(raw_index, bool)
        completed.append((raw_index, path))
    completed.sort(key=lambda item: (item[0], item[1].name))
    return tuple(path for _index, path in completed)


__all__ = [
    "ProspectiveArtifactError",
    "completed_generation_dirs",
    "read_manifest",
    "read_outcome",
    "validate_completed_generation",
]
