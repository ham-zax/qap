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

from qap.scanner.graph import NeighborRecord
from qap.scanner.models import ScanDefinition
from qap.scanner.promotion import PromotionRecord
from qap.scanner.scout import ScoutTrialRecord
from qap.scanner.universe import EligibleAssetRecord


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


_ELIGIBLE_SCHEMA = pa.schema(
    [
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("asset_id", pa.string()),
        ("venue_symbol", pa.string()),
        ("eligibility_state", pa.string()),
        ("eligibility_reason", pa.string()),
        ("lifecycle_evidence_refs", pa.list_(pa.string())),
        ("source_artifact_fingerprint", pa.string()),
        ("selection_slice_fingerprint", pa.string()),
        ("bar_coverage", pa.float64()),
        ("longest_missing_run", pa.int64()),
        ("automatic_eligible", pa.bool_()),
        ("forensic_research_allowed", pa.bool_()),
    ]
)
_NEIGHBOR_SCHEMA = pa.schema(
    [
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("pair_id", pa.string()),
        ("asset_a", pa.string()),
        ("asset_b", pa.string()),
        ("ssd_distance", pa.float64()),
        ("rank_from_a", pa.int64()),
        ("rank_from_b", pa.int64()),
        ("selected_by_a", pa.bool_()),
        ("selected_by_b", pa.bool_()),
        ("automatic_neighbor_selected", pa.bool_()),
        ("manual_pinned", pa.bool_()),
    ]
)
_SCOUT_SCHEMA = pa.schema(
    [
        ("candidate_id", pa.string()),
        ("scan_id", pa.string()),
        ("venue", pa.string()),
        ("horizon", pa.string()),
        ("pair_id", pa.string()),
        ("orientation", pa.string()),
        ("resolution", pa.string()),
        ("model_family", pa.string()),
        ("template_id", pa.string()),
        ("trial_status", pa.string()),
        ("failure_reason", pa.string()),
        ("scout_relative_wealth_proxy", pa.float64()),
        ("scout_turnover_proxy", pa.float64()),
        ("signal_count", pa.int64()),
        ("automatic_neighbor_selected", pa.bool_()),
        ("manual_pinned", pa.bool_()),
    ]
)
_PROMOTION_SCHEMA = pa.schema(
    [
        ("candidate_id", pa.string()),
        ("promotion_rank", pa.int64()),
        ("promotion_status", pa.string()),
        ("budget_reason", pa.string()),
        ("automatic_selected", pa.bool_()),
        ("manual_selected", pa.bool_()),
        ("selected_for_replay", pa.bool_()),
        ("direct_execution_instrument_id", pa.string()),
        ("deep_replay_run_id", pa.string()),
        ("deep_replay_status", pa.string()),
        ("economic_gate_status", pa.string()),
    ]
)
_REPLAY_SCHEMA = pa.schema(
    [
        ("attempt_id", pa.string()),
        ("scan_id", pa.string()),
        ("candidate_id", pa.string()),
        ("promotion_rank", pa.int64()),
        ("attempt_status", pa.string()),
        ("failure_stage", pa.string()),
        ("failure_reason", pa.string()),
        ("deep_replay_run_id", pa.string()),
    ]
)
_TABLE_SCHEMAS: dict[str, Any] = {
    "eligible_assets.parquet": _ELIGIBLE_SCHEMA,
    "neighbors.parquet": _NEIGHBOR_SCHEMA,
    "scout_trials.parquet": _SCOUT_SCHEMA,
    "promotions.parquet": _PROMOTION_SCHEMA,
    "replay_attempts.parquet": _REPLAY_SCHEMA,
}


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
    return _canonical_json_bytes(definition.model_dump(mode="json"))


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
        return ScanDefinition.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ScanArtifactError("partial scan definition is malformed") from exc


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


def _eligible_table(records: tuple[EligibleAssetRecord, ...]) -> Any:
    rows = [
        {
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon.value,
            "asset_id": item.asset_id,
            "venue_symbol": item.venue_symbol,
            "eligibility_state": item.eligibility_state.value,
            "eligibility_reason": item.eligibility_reason,
            "lifecycle_evidence_refs": list(item.lifecycle_evidence_refs),
            "source_artifact_fingerprint": item.source_artifact_fingerprint,
            "selection_slice_fingerprint": item.selection_slice_fingerprint,
            "bar_coverage": item.bar_coverage,
            "longest_missing_run": item.longest_missing_run,
            "automatic_eligible": item.automatic_eligible,
            "forensic_research_allowed": item.forensic_research_allowed,
        }
        for item in sorted(
            records,
            key=lambda value: (value.venue, value.horizon.value, value.asset_id),
        )
    ]
    return pa.Table.from_pylist(rows, schema=_ELIGIBLE_SCHEMA)


def _neighbor_table(records: tuple[NeighborRecord, ...]) -> Any:
    rows = [
        {
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon,
            "pair_id": item.pair_id,
            "asset_a": item.asset_a,
            "asset_b": item.asset_b,
            "ssd_distance": item.ssd_distance,
            "rank_from_a": item.rank_from_a,
            "rank_from_b": item.rank_from_b,
            "selected_by_a": item.selected_by_a,
            "selected_by_b": item.selected_by_b,
            "automatic_neighbor_selected": item.automatic_neighbor_selected,
            "manual_pinned": item.manual_pinned,
        }
        for item in sorted(
            records, key=lambda value: (value.venue, value.horizon, value.pair_id)
        )
    ]
    return pa.Table.from_pylist(rows, schema=_NEIGHBOR_SCHEMA)


def _scout_table(records: tuple[ScoutTrialRecord, ...]) -> Any:
    rows = [
        {
            "candidate_id": item.candidate_id,
            "scan_id": item.scan_id,
            "venue": item.venue,
            "horizon": item.horizon,
            "pair_id": item.pair_id,
            "orientation": item.orientation,
            "resolution": item.resolution,
            "model_family": item.model_family,
            "template_id": item.template_id,
            "trial_status": item.trial_status.value,
            "failure_reason": item.failure_reason,
            "scout_relative_wealth_proxy": item.scout_relative_wealth_proxy,
            "scout_turnover_proxy": item.scout_turnover_proxy,
            "signal_count": item.signal_count,
            "automatic_neighbor_selected": item.automatic_neighbor_selected,
            "manual_pinned": item.manual_pinned,
        }
        for item in sorted(records, key=lambda value: value.candidate_id)
    ]
    return pa.Table.from_pylist(rows, schema=_SCOUT_SCHEMA)


def _promotion_table(records: tuple[PromotionRecord, ...]) -> Any:
    rows = [
        {
            "candidate_id": item.candidate_id,
            "promotion_rank": item.promotion_rank,
            "promotion_status": item.promotion_status.value,
            "budget_reason": item.budget_reason,
            "automatic_selected": item.automatic_selected,
            "manual_selected": item.manual_selected,
            "selected_for_replay": item.selected_for_replay,
            "direct_execution_instrument_id": None,
            "deep_replay_run_id": None,
            "deep_replay_status": None,
            "economic_gate_status": None,
        }
        for item in sorted(records, key=lambda value: value.candidate_id)
    ]
    return pa.Table.from_pylist(rows, schema=_PROMOTION_SCHEMA)


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
    return pa.Table.from_pylist(rows, schema=_REPLAY_SCHEMA)


def write_scan_tables(
    generation: ScanArtifactGeneration,
    *,
    eligible_assets: tuple[EligibleAssetRecord, ...],
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
    if any(item.scan_id != scan_id for item in neighbors):
        raise ScanArtifactError("neighbor record scan_id mismatch")
    if any(item.scan_id != scan_id for item in scout_trials):
        raise ScanArtifactError("scout trial scan_id mismatch")
    scout_ids = {item.candidate_id for item in scout_trials}
    if any(item.candidate_id not in scout_ids for item in promotions):
        raise ScanArtifactError("promotion candidate is absent from scout trial table")

    tables = {
        "eligible_assets.parquet": _eligible_table(eligible_assets),
        "neighbors.parquet": _neighbor_table(neighbors),
        "scout_trials.parquet": _scout_table(scout_trials),
        "promotions.parquet": _promotion_table(promotions),
    }
    for name, table in tables.items():
        _atomic_write_table(generation.staging_directory / name, table)
    if not generation.replay_attempts_path.exists():
        _atomic_write_table(generation.replay_attempts_path, _attempt_table(()))


def _load_attempts(path: Path) -> tuple[ReplayAttemptRecord, ...]:
    if not path.is_file():
        raise ScanArtifactError("replay_attempts.parquet is missing")
    table = pq.read_table(path)
    if not table.schema.equals(_REPLAY_SCHEMA):
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
    if not promotion_table.schema.equals(_PROMOTION_SCHEMA):
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
    for name, schema in _TABLE_SCHEMAS.items():
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
    for row in tables["eligible_assets.parquet"].to_pylist():
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
    for name in ("neighbors.parquet", "scout_trials.parquet"):
        if any(
            row["scan_id"] != definition.scan_id for row in tables[name].to_pylist()
        ):
            raise ScanArtifactError(f"{name} scan_id does not match definition")


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
        "definition_sha256": sha256(_definition_bytes(stored)).hexdigest(),
        "table_counts": table_counts,
        "table_hashes": table_hashes,
        "replay_attempt_status_counts": dict(sorted(status_counts.items())),
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
    os.replace(generation.staging_directory, generation.final_directory)
    return generation.final_directory


def discover_completed_scans(run_root: str | Path) -> tuple[Path, ...]:
    """Return only manifest-bearing final scan directories, never partial staging."""

    scan_root = Path(run_root).resolve() / "scans"
    if not scan_root.is_dir():
        return ()
    completed: list[Path] = []
    for directory in scan_root.iterdir():
        if not directory.is_dir() or directory.name.endswith(".partial"):
            continue
        manifest_path = directory / "manifest.json"
        definition_path = directory / "definition.json"
        if not manifest_path.is_file() or not definition_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            continue
        if manifest.get("scan_id") == directory.name:
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
    "start_scan_generation",
    "transition_replay_attempt",
    "write_scan_tables",
]
