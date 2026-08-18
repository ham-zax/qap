# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Recoverable, atomic Scanner-V1 Slice-1 research artifacts."""

import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from qap.scanner.artifact_schemas import (
    PROMOTION_SCHEMA,
    REPLAY_SCHEMA,
    TABLE_SCHEMAS,
)
from qap.scanner.artifact_tables import (
    eligible_table,
    graph_metadata_table,
    neighbor_table,
    promotion_table,
    scout_table,
)
from qap.scanner.graph import GraphMetadataRecord, NeighborRecord
from qap.scanner.integrity import validate_scanner_integrity, write_scanner_integrity
from qap.scanner.models import ScanDefinition
from qap.scanner.promotion import PromotionRecord
from qap.scanner.scout import ScoutTrialRecord
from qap.scanner.universe import EligibleAssetRecord

_AUTHORITATIVE_FILES = frozenset(("definition.json", "manifest.json", *TABLE_SCHEMAS))


class ScanArtifactError(RuntimeError):
    """Raised when scanner staging or publication cannot preserve evidence integrity."""


class ReplayAttemptStatus(StrEnum):
    ENUMERATED = "enumerated"
    SETUP_FAILED = "setup_failed"
    REPLAY_FAILED = "replay_failed"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ReplayAttemptRecord:
    attempt_id: str
    scan_id: str
    candidate_id: str
    promotion_rank: int | None
    attempt_status: ReplayAttemptStatus
    failure_stage: str | None = None
    failure_reason: str | None = None
    deep_replay_run_id: str | None = None


@dataclass(frozen=True, slots=True)
class ScanArtifactGeneration:
    run_root: Path
    scan_root: Path
    definition: ScanDefinition
    staging_directory: Path
    final_directory: Path

    @property
    def definition_path(self) -> Path:
        return self.staging_directory / "definition.json"

    @property
    def replay_attempts_path(self) -> Path:
        return self.staging_directory / "replay_attempts.parquet"


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _definition_bytes(definition: ScanDefinition) -> bytes:
    payload = definition.model_dump(mode="json")
    payload["scan_id"] = definition.scan_id
    return _canonical_json_bytes(payload)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_write_table(path: Path, table: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    pq.write_table(table, temporary, compression="zstd", version="2.6")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_definition(path: Path) -> ScanDefinition:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("definition must be a JSON object")
        declared_scan_id = payload.pop("scan_id", None)
        definition = ScanDefinition.model_validate(payload)
    except (OSError, ValueError) as exc:
        raise ScanArtifactError("partial scan definition is malformed") from exc
    if declared_scan_id != definition.scan_id:
        raise ScanArtifactError("partial scan definition mismatch")
    return definition


def start_scan_generation(
    run_root: str | Path,
    definition: ScanDefinition,
) -> ScanArtifactGeneration:
    """Create or exactly resume one immutable scanner staging generation."""

    if not isinstance(cast(object, definition), ScanDefinition):
        raise TypeError("definition must be a ScanDefinition")
    root = Path(run_root).resolve()
    scan_root = root / "scans"
    scan_root.mkdir(parents=True, exist_ok=True)
    staging = scan_root / f"{definition.scan_id}.partial"
    final = scan_root / definition.scan_id
    if final.exists():
        raise ScanArtifactError(f"completed scan already exists: {definition.scan_id}")

    if staging.exists():
        definition_path = staging / "definition.json"
        if not definition_path.is_file():
            raise ScanArtifactError("partial scan definition is missing")
        stored = _load_definition(definition_path)
        requested = definition.model_copy(update={"created_at": stored.created_at})
        if stored.scan_id != definition.scan_id or stored != requested:
            raise ScanArtifactError("partial scan definition mismatch")
        return ScanArtifactGeneration(root, scan_root, stored, staging, final)

    staging.mkdir()
    generation = ScanArtifactGeneration(root, scan_root, definition, staging, final)
    _atomic_write_bytes(generation.definition_path, _definition_bytes(definition))
    return generation


def _attempt_table(records: tuple[ReplayAttemptRecord, ...]) -> Any:
    rows = [
        {
            "attempt_id": item.attempt_id,
            "scan_id": item.scan_id,
            "candidate_id": item.candidate_id,
            "promotion_rank": item.promotion_rank,
            "attempt_status": item.attempt_status.value,
            "failure_stage": item.failure_stage,
            "failure_reason": item.failure_reason,
            "deep_replay_run_id": item.deep_replay_run_id,
        }
        for item in sorted(records, key=lambda value: value.attempt_id)
    ]
    return pa.Table.from_pylist(rows, schema=REPLAY_SCHEMA)


def write_scan_tables(
    generation: ScanArtifactGeneration,
    *,
    eligible_assets: tuple[EligibleAssetRecord, ...],
    graph_metadata: tuple[GraphMetadataRecord, ...],
    neighbors: tuple[NeighborRecord, ...],
    scout_trials: tuple[ScoutTrialRecord, ...],
    promotions: tuple[PromotionRecord, ...],
) -> None:
    """Atomically write deterministic search tables without declaring completion."""

    if not generation.staging_directory.is_dir():
        raise ScanArtifactError("scan staging directory does not exist")
    scan_id = generation.definition.scan_id
    if any(item.scan_id != scan_id for item in eligible_assets):
        raise ScanArtifactError("eligible asset record scan_id mismatch")
    if any(item.scan_id != scan_id for item in graph_metadata):
        raise ScanArtifactError("graph metadata record scan_id mismatch")
    if any(item.scan_id != scan_id for item in neighbors):
        raise ScanArtifactError("neighbor record scan_id mismatch")
    if any(item.scan_id != scan_id for item in scout_trials):
        raise ScanArtifactError("scout trial scan_id mismatch")
    scout_ids = {item.candidate_id for item in scout_trials}
    if any(item.candidate_id not in scout_ids for item in promotions):
        raise ScanArtifactError("promotion candidate is absent from scout trial table")

    tables = {
        "eligible_assets.parquet": eligible_table(eligible_assets),
        "graph_metadata.parquet": graph_metadata_table(graph_metadata),
        "neighbors.parquet": neighbor_table(neighbors),
        "scout_trials.parquet": scout_table(scout_trials),
        "promotions.parquet": promotion_table(promotions),
    }
    for name, table in tables.items():
        _atomic_write_table(generation.staging_directory / name, table)
    if not generation.replay_attempts_path.exists():
        _atomic_write_table(generation.replay_attempts_path, _attempt_table(()))


def _load_attempts(path: Path) -> tuple[ReplayAttemptRecord, ...]:
    if not path.is_file():
        raise ScanArtifactError("replay_attempts.parquet is missing")
    table = pq.read_table(path)
    if not table.schema.equals(REPLAY_SCHEMA):
        raise ScanArtifactError("replay attempt schema mismatch")
    return tuple(
        ReplayAttemptRecord(
            attempt_id=row["attempt_id"],
            scan_id=row["scan_id"],
            candidate_id=row["candidate_id"],
            promotion_rank=row["promotion_rank"],
            attempt_status=ReplayAttemptStatus(row["attempt_status"]),
            failure_stage=row["failure_stage"],
            failure_reason=row["failure_reason"],
            deep_replay_run_id=row["deep_replay_run_id"],
        )
        for row in table.to_pylist()
    )


def read_replay_attempt(
    generation: ScanArtifactGeneration,
    attempt_id: str,
) -> ReplayAttemptRecord:
    """Read exactly one durably persisted replay attempt by deterministic ID."""

    matches = tuple(
        attempt
        for attempt in _load_attempts(generation.replay_attempts_path)
        if attempt.attempt_id == attempt_id
    )
    if len(matches) != 1:
        raise ScanArtifactError(f"unknown replay attempt: {attempt_id}")
    return matches[0]


def _attempt_id(scan_id: str, promotion: PromotionRecord) -> str:
    rank = (
        "manual" if promotion.promotion_rank is None else str(promotion.promotion_rank)
    )
    payload = (
        f"qap.scanner.replay-attempt.v1\0{scan_id}\0{promotion.candidate_id}\0{rank}\0"
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def enumerate_replay_attempt(
    generation: ScanArtifactGeneration,
    promotion: PromotionRecord,
) -> ReplayAttemptRecord:
    """Durably enumerate one selected replay before any experiment preparation."""

    if not promotion.selected_for_replay:
        raise ScanArtifactError("cannot enumerate a non-selected promotion")
    promotion_path = generation.staging_directory / "promotions.parquet"
    if not promotion_path.is_file():
        raise ScanArtifactError("persisted selected promotion is missing")
    promotion_table = pq.read_table(promotion_path)
    if not promotion_table.schema.equals(PROMOTION_SCHEMA):
        raise ScanArtifactError("promotion table schema mismatch")
    persisted = [
        row
        for row in promotion_table.to_pylist()
        if row["candidate_id"] == promotion.candidate_id
    ]
    if (
        len(persisted) != 1
        or not persisted[0]["selected_for_replay"]
        or persisted[0]["promotion_rank"] != promotion.promotion_rank
    ):
        raise ScanArtifactError("persisted selected promotion does not match request")
    attempts = _load_attempts(generation.replay_attempts_path)
    attempt_id = _attempt_id(generation.definition.scan_id, promotion)
    for existing in attempts:
        if existing.attempt_id == attempt_id:
            if existing.candidate_id != promotion.candidate_id:
                raise ScanArtifactError("deterministic replay attempt ID collision")
            return existing
    record = ReplayAttemptRecord(
        attempt_id=attempt_id,
        scan_id=generation.definition.scan_id,
        candidate_id=promotion.candidate_id,
        promotion_rank=promotion.promotion_rank,
        attempt_status=ReplayAttemptStatus.ENUMERATED,
    )
    _atomic_write_table(
        generation.replay_attempts_path, _attempt_table((*attempts, record))
    )
    return record


def transition_replay_attempt(
    generation: ScanArtifactGeneration,
    attempt_id: str,
    *,
    status: ReplayAttemptStatus,
    failure_stage: str | None = None,
    failure_reason: str | None = None,
    deep_replay_run_id: str | None = None,
) -> ReplayAttemptRecord:
    """Replace one enumerated attempt with exactly one terminal attempt state."""

    if status is ReplayAttemptStatus.ENUMERATED:
        raise ScanArtifactError("attempt transition requires a terminal status")
    if status is ReplayAttemptStatus.COMPLETED:
        if not deep_replay_run_id:
            raise ScanArtifactError("completed replay attempt requires a run ID")
        if failure_stage is not None or failure_reason is not None:
            raise ScanArtifactError(
                "completed replay attempt cannot carry failure fields"
            )
    elif not failure_stage or not failure_reason:
        raise ScanArtifactError("failed replay attempt requires stage and reason")

    attempts = list(_load_attempts(generation.replay_attempts_path))
    for index, existing in enumerate(attempts):
        if existing.attempt_id != attempt_id:
            continue
        replacement = ReplayAttemptRecord(
            attempt_id=existing.attempt_id,
            scan_id=existing.scan_id,
            candidate_id=existing.candidate_id,
            promotion_rank=existing.promotion_rank,
            attempt_status=status,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
            deep_replay_run_id=deep_replay_run_id,
        )
        if existing.attempt_status is not ReplayAttemptStatus.ENUMERATED:
            if existing == replacement:
                return existing
            raise ScanArtifactError("replay attempt is already terminal")
        attempts[index] = replacement
        _atomic_write_table(
            generation.replay_attempts_path, _attempt_table(tuple(attempts))
        )
        return replacement
    raise ScanArtifactError(f"unknown replay attempt: {attempt_id}")


def _semantic_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return value.hex()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ",".join(_semantic_value(item) for item in value) + "]"
    return str(value)


def _table_hash(table: Any) -> str:
    digest = sha256()
    for field in table.schema:
        digest.update(field.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(field.type).encode("utf-8"))
        digest.update(b"\0")
    for row in table.to_pylist():
        for name in table.schema.names:
            digest.update(_semantic_value(row[name]).encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def _read_required_tables(generation: ScanArtifactGeneration) -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for name, schema in TABLE_SCHEMAS.items():
        path = generation.staging_directory / name
        if not path.is_file():
            raise ScanArtifactError(f"required scanner table is missing: {name}")
        table = pq.read_table(path)
        if not table.schema.equals(schema):
            raise ScanArtifactError(f"scanner table schema mismatch: {name}")
        tables[name] = table
    return tables


def _reconcile_definition(
    definition: ScanDefinition,
    tables: dict[str, Any],
) -> None:
    frozen_pairs = {
        (
            item.source_artifact_fingerprint,
            item.selection_slice_fingerprint,
        )
        for item in definition.input_slices
    }
    eligible_rows = tables["eligible_assets.parquet"].to_pylist()
    for row in eligible_rows:
        if row["scan_id"] != definition.scan_id:
            raise ScanArtifactError("eligible asset scan_id does not match definition")
        pair = (
            row["source_artifact_fingerprint"],
            row["selection_slice_fingerprint"],
        )
        if pair not in frozen_pairs:
            raise ScanArtifactError(
                "eligible asset frozen source/slice identity is absent from definition"
            )

    metadata_rows = tables["graph_metadata.parquet"].to_pylist()
    metadata_scopes = [(row["venue"], row["horizon"]) for row in metadata_rows]
    if len(metadata_scopes) != len(set(metadata_scopes)):
        raise ScanArtifactError("graph metadata scopes must be unique")
    eligible_scopes = {(row["venue"], row["horizon"]) for row in eligible_rows}
    if set(metadata_scopes) != eligible_scopes:
        raise ScanArtifactError("graph metadata scopes do not match eligible evidence")
    for row in metadata_rows:
        if row["scan_id"] != definition.scan_id:
            raise ScanArtifactError("graph metadata scan_id does not match definition")
        if row["generator_version"] != definition.candidate_generator_version:
            raise ScanArtifactError("graph metadata generator version mismatch")
        scoped = [
            eligible
            for eligible in eligible_rows
            if eligible["venue"] == row["venue"]
            and eligible["horizon"] == row["horizon"]
            and eligible["automatic_eligible"]
        ]
        if row["eligible_asset_count"] != len(scoped):
            raise ScanArtifactError("graph metadata eligible denominator mismatch")
        fingerprints = sorted(
            eligible["selection_slice_fingerprint"] for eligible in scoped
        )
        if row["input_selection_slice_fingerprints"] != fingerprints:
            raise ScanArtifactError(
                "graph metadata selection-slice denominator mismatch"
            )
        maximum_pairs = len(scoped) * (len(scoped) - 1) // 2
        if not 0 <= row["total_valid_pair_comparisons"] <= maximum_pairs:
            raise ScanArtifactError("graph metadata pair denominator is impossible")
        digest = row["distance_digest"]
        if not isinstance(digest, str) or len(digest) != 64:
            raise ScanArtifactError("graph metadata distance digest is invalid")

    for name in ("neighbors.parquet", "scout_trials.parquet"):
        if any(
            row["scan_id"] != definition.scan_id for row in tables[name].to_pylist()
        ):
            raise ScanArtifactError(f"{name} scan_id does not match definition")


def _replay_references(tables: dict[str, Any]) -> list[dict[str, object]]:
    promotions = {
        row["candidate_id"]: row
        for row in tables["promotions.parquet"].to_pylist()
        if row["selected_for_replay"]
    }
    references: list[dict[str, object]] = []
    for attempt in sorted(
        tables["replay_attempts.parquet"].to_pylist(),
        key=lambda row: row["attempt_id"],
    ):
        promotion = promotions.get(attempt["candidate_id"])
        references.append(
            {
                "attempt_id": attempt["attempt_id"],
                "candidate_id": attempt["candidate_id"],
                "attempt_status": attempt["attempt_status"],
                "failure_stage": attempt["failure_stage"],
                "failure_reason": attempt["failure_reason"],
                "direct_execution_instrument_id": (
                    None
                    if promotion is None
                    else promotion["direct_execution_instrument_id"]
                ),
                "deep_replay_run_id": attempt["deep_replay_run_id"],
                "economic_gate_status": (
                    None if promotion is None else promotion["economic_gate_status"]
                ),
            }
        )
    return references


def _reconcile(tables: dict[str, Any]) -> Counter[str]:
    promotions = tables["promotions.parquet"].to_pylist()
    attempts = tables["replay_attempts.parquet"].to_pylist()
    selected = [row for row in promotions if row["selected_for_replay"]]
    selected_ids = [row["candidate_id"] for row in selected]
    attempt_ids = [row["candidate_id"] for row in attempts]
    if len(selected_ids) != len(set(selected_ids)):
        raise ScanArtifactError("selected promotion candidate IDs must be unique")
    if len(attempt_ids) != len(set(attempt_ids)):
        raise ScanArtifactError("replay attempt candidate IDs must be unique")
    if set(selected_ids) != set(attempt_ids):
        raise ScanArtifactError("selected promotion lacks exactly one replay attempt")
    attempts_by_candidate = {row["candidate_id"]: row for row in attempts}
    for promotion in promotions:
        outcome_fields = (
            promotion["direct_execution_instrument_id"],
            promotion["deep_replay_run_id"],
            promotion["deep_replay_status"],
            promotion["economic_gate_status"],
        )
        if not promotion["selected_for_replay"]:
            if any(value is not None for value in outcome_fields):
                raise ScanArtifactError("unselected promotion has replay outcome")
            continue
        attempt = attempts_by_candidate[promotion["candidate_id"]]
        status = attempt["attempt_status"]
        if (
            promotion["deep_replay_status"] != status
            or promotion["deep_replay_run_id"] != attempt["deep_replay_run_id"]
        ):
            raise ScanArtifactError("promotion replay outcome does not match attempt")
        completed = status == ReplayAttemptStatus.COMPLETED.value
        if completed != bool(promotion["economic_gate_status"]):
            raise ScanArtifactError("promotion economic gate does not match attempt")
        if completed and not promotion["direct_execution_instrument_id"]:
            raise ScanArtifactError("completed promotion lacks direct instrument")
    statuses = Counter(str(row["attempt_status"]) for row in attempts)
    if statuses[ReplayAttemptStatus.ENUMERATED.value]:
        raise ScanArtifactError("enumerated replay attempt is not terminal")
    return statuses


def publish_scan_generation(generation: ScanArtifactGeneration) -> Path:
    """Reconcile staging, write manifest last, then atomically publish the directory."""

    if generation.final_directory.exists():
        raise ScanArtifactError(
            f"completed scan already exists: {generation.definition.scan_id}"
        )
    if not generation.staging_directory.is_dir():
        raise ScanArtifactError("scan staging directory does not exist")
    stored = _load_definition(generation.definition_path)
    if stored != generation.definition:
        raise ScanArtifactError("partial scan definition mismatch")
    tables = _read_required_tables(generation)
    _reconcile_definition(generation.definition, tables)
    status_counts = _reconcile(tables)
    table_counts = {name: table.num_rows for name, table in tables.items()}
    table_hashes = {name: _table_hash(table) for name, table in tables.items()}
    manifest = {
        "schema_version": "qap.scanner.manifest.v1",
        "scan_id": generation.definition.scan_id,
        "scanner_protocol_version": generation.definition.scanner_protocol_version,
        "protocol_identity": generation.definition.protocol_identity,
        "universe_policy_version": generation.definition.universe_policy_version,
        "candidate_generator_version": (
            generation.definition.candidate_generator_version
        ),
        "template_set_version": generation.definition.template_set_version,
        "promotion_policy_version": generation.definition.promotion_policy_version,
        "cost_policy_reference": generation.definition.cost_policy_reference,
        "definition_sha256": sha256(_definition_bytes(stored)).hexdigest(),
        "table_counts": table_counts,
        "table_hashes": table_hashes,
        "replay_attempt_status_counts": dict(sorted(status_counts.items())),
        "replay_references": _replay_references(tables),
        "published_at": datetime.now(UTC).isoformat(),
    }
    manifest_path = generation.staging_directory / "manifest.json"
    _atomic_write_bytes(manifest_path, _canonical_json_bytes(manifest))

    reread = json.loads(manifest_path.read_text(encoding="utf-8"))
    if reread["scan_id"] != generation.definition.scan_id:
        raise ScanArtifactError("scanner manifest scan_id mismatch")
    reread_tables = _read_required_tables(generation)
    _reconcile_definition(generation.definition, reread_tables)
    if reread["table_counts"] != {
        name: table.num_rows for name, table in reread_tables.items()
    }:
        raise ScanArtifactError("scanner manifest table counts do not reconcile")
    if reread["table_hashes"] != {
        name: _table_hash(table) for name, table in reread_tables.items()
    }:
        raise ScanArtifactError("scanner manifest table hashes do not reconcile")
    _reconcile(reread_tables)
    if reread["replay_references"] != _replay_references(reread_tables):
        raise ScanArtifactError("scanner manifest replay references do not reconcile")
    try:
        write_scanner_integrity(
            generation.staging_directory,
            scan_id=generation.definition.scan_id,
            authoritative_files=_AUTHORITATIVE_FILES,
        )
        validate_scanner_integrity(
            generation.staging_directory,
            scan_id=generation.definition.scan_id,
            authoritative_files=_AUTHORITATIVE_FILES,
        )
    except ValueError as exc:
        raise ScanArtifactError(str(exc)) from exc
    os.replace(generation.staging_directory, generation.final_directory)
    return generation.final_directory


def read_completed_scan(
    directory: str | Path,
) -> tuple[ScanDefinition, dict[str, list[dict[str, Any]]]]:
    """Read one completed scanner generation with integrity and semantic checks."""

    root = Path(directory).resolve()
    scan_id = root.name
    try:
        validate_scanner_integrity(
            root,
            scan_id=scan_id,
            authoritative_files=_AUTHORITATIVE_FILES,
        )
        definition = _load_definition(root / "definition.json")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ScanArtifactError(str(exc)) from exc
    if not isinstance(manifest, dict):
        raise ScanArtifactError("scanner manifest must be an object")
    if definition.scan_id != scan_id or manifest.get("scan_id") != scan_id:
        raise ScanArtifactError("completed scanner artifact identity mismatch")

    generation = ScanArtifactGeneration(
        run_root=root.parent.parent,
        scan_root=root.parent,
        definition=definition,
        staging_directory=root,
        final_directory=root,
    )
    tables = _read_required_tables(generation)
    _reconcile_definition(definition, tables)
    _reconcile(tables)
    if manifest.get("table_counts") != {
        name: table.num_rows for name, table in tables.items()
    }:
        raise ScanArtifactError("scanner manifest table counts do not reconcile")
    if manifest.get("table_hashes") != {
        name: _table_hash(table) for name, table in tables.items()
    }:
        raise ScanArtifactError("scanner manifest table hashes do not reconcile")
    if manifest.get("replay_references") != _replay_references(tables):
        raise ScanArtifactError("scanner manifest replay references do not reconcile")
    return definition, {name: table.to_pylist() for name, table in tables.items()}


def discover_completed_scans(run_root: str | Path) -> tuple[Path, ...]:
    """Return only fully validated final scan directories, never partial staging."""

    scan_root = Path(run_root).resolve() / "scans"
    if not scan_root.is_dir():
        return ()
    completed: list[Path] = []
    for directory in scan_root.iterdir():
        if not directory.is_dir() or directory.name.endswith(".partial"):
            continue
        read_completed_scan(directory)
        completed.append(directory)
    return tuple(sorted(completed))


__all__ = [
    "ReplayAttemptRecord",
    "ReplayAttemptStatus",
    "ScanArtifactError",
    "ScanArtifactGeneration",
    "discover_completed_scans",
    "enumerate_replay_attempt",
    "publish_scan_generation",
    "read_completed_scan",
    "read_replay_attempt",
    "start_scan_generation",
    "transition_replay_attempt",
    "write_scan_tables",
]
