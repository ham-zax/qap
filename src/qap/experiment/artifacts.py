# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Immutable experiment run directories and final-OOS commitment discipline."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from pydantic import BaseModel

from qap.experiment.artifact_semantics import validate_run_artifact_semantics
from qap.experiment.events import read_event_records, write_event_records
from qap.experiment.final_oos import issue_final_oos_execution_permit
from qap.experiment.final_oos_reservation import (
    FinalOosCommitment,
    HoldoutAlreadyCommittedError,
)
from qap.experiment.final_oos_reservation import (
    assert_holdout_available as _assert_holdout_available,
)
from qap.experiment.final_oos_reservation import (
    consume_commitment as _consume_commitment,
)
from qap.experiment.final_oos_reservation import (
    initial_commitment as _initial_commitment,
)
from qap.experiment.final_oos_reservation import (
    reservation_failed_commitment as _reservation_failed_commitment,
)
from qap.experiment.final_oos_reservation import (
    reserve_holdout_registry as _reserve_holdout_registry,
)
from qap.experiment.integrity import (
    build_integrity_record,
    read_and_validate_integrity,
)
from qap.experiment.manifest import DataRole, ExperimentManifest
from qap.experiment.provenance import (
    RunProvenance,
    canonical_manifest_bytes,
    manifest_sha256,
)
from qap.experiment.result import ExperimentResult
from qap.experiment.runner import (
    ExperimentRun,
    PreparedExperiment,
    execute_precommitted_experiment,
    prepare_experiment,
)
from qap.experiment.tables import (
    build_evidence_table,
    build_inventory_table,
    build_performance_table,
    validate_artifact_table,
)


class ArtifactError(RuntimeError):
    """Base error for immutable experiment artifact operations."""


class RunAlreadyExistsError(ArtifactError):
    """Raised when a run ID already has a directory and cannot be overwritten."""


@dataclass(frozen=True, slots=True)
class RunArtifactPaths:
    run_id: str
    run_directory: Path
    manifest: Path
    provenance: Path
    result: Path
    performance: Path
    inventory: Path
    evidence: Path
    events: Path
    integrity: Path
    commitment: Path
    failure: Path


@dataclass(frozen=True, slots=True)
class LoadedRunArtifacts:
    manifest: ExperimentManifest
    provenance: RunProvenance
    result: ExperimentResult
    performance: Any
    inventory: Any
    evidence: Any | None
    events: tuple[dict[str, object], ...]
    commitment: FinalOosCommitment | None


def _paths(run_root: Path, run_id: str) -> RunArtifactPaths:
    directory = run_root / run_id
    return RunArtifactPaths(
        run_id=run_id,
        run_directory=directory,
        manifest=directory / "manifest.json",
        provenance=directory / "provenance.json",
        result=directory / "result.json",
        performance=directory / "performance.parquet",
        inventory=directory / "inventory.parquet",
        evidence=directory / "evidence.parquet",
        events=directory / "events.jsonl",
        integrity=directory / "integrity.json",
        commitment=directory / "commitment.json",
        failure=directory / "failure.json",
    )


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_write_model(path: Path, model: BaseModel) -> None:
    _atomic_write_bytes(
        path,
        (model.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )


def _reserve_run_directory(run_root: Path, run_id: str) -> RunArtifactPaths:
    root = run_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths = _paths(root, run_id)
    try:
        paths.run_directory.mkdir()
    except FileExistsError as exc:
        raise RunAlreadyExistsError(
            f"run directory already exists and will not be overwritten: {run_id}"
        ) from exc
    return paths


def _write_prelude(paths: RunArtifactPaths, prepared: PreparedExperiment) -> None:
    _atomic_write_bytes(
        paths.manifest,
        canonical_manifest_bytes(prepared.manifest) + b"\n",
    )
    _atomic_write_model(paths.provenance, prepared.provenance)


def _write_failure(paths: RunArtifactPaths, error: BaseException) -> None:
    payload = {
        "schema_version": "qap.experiment.failure.v1",
        "run_id": paths.run_id,
        "error_type": type(error).__name__,
        "message": str(error),
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    _atomic_write_bytes(
        paths.failure,
        (
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8"),
    )


def _write_completed_artifacts(paths: RunArtifactPaths, run: ExperimentRun) -> None:
    _atomic_write_model(paths.result, run.result)
    pq.write_table(
        build_performance_table(run),
        paths.performance,
        compression="zstd",
        version="2.6",
    )
    pq.write_table(
        build_inventory_table(run),
        paths.inventory,
        compression="zstd",
        version="2.6",
    )
    if run.relationship_observations:
        pq.write_table(
            build_evidence_table(run),
            paths.evidence,
            compression="zstd",
            version="2.6",
        )
    write_event_records(paths.events, run)


def _completed_integrity_file_names(paths: RunArtifactPaths) -> tuple[str, ...]:
    names = [
        paths.manifest.name,
        paths.provenance.name,
        paths.result.name,
        paths.performance.name,
        paths.inventory.name,
        paths.events.name,
    ]
    if paths.evidence.is_file():
        names.append(paths.evidence.name)
    if paths.commitment.is_file():
        names.append(paths.commitment.name)
    return tuple(names)


def _write_completed_integrity(paths: RunArtifactPaths) -> None:
    integrity = build_integrity_record(
        paths.run_directory,
        artifact_id=paths.run_id,
        file_names=_completed_integrity_file_names(paths),
    )
    _atomic_write_model(paths.integrity, integrity)


def write_run_artifacts(
    run: ExperimentRun,
    *,
    run_root: str | Path,
) -> RunArtifactPaths:
    """Persist an already completed non-final run without overwriting history."""

    if run.manifest.data_role is DataRole.FINAL_OOS:
        raise ArtifactError(
            "final_oos runs must use run_experiment_to_artifacts so the "
            "commitment exists before replay"
        )
    paths = _reserve_run_directory(Path(run_root), run.provenance.run_id)
    _atomic_write_bytes(
        paths.manifest,
        canonical_manifest_bytes(run.manifest) + b"\n",
    )
    _atomic_write_model(paths.provenance, run.provenance)
    try:
        _write_completed_artifacts(paths, run)
        _write_completed_integrity(paths)
    except BaseException as exc:
        _write_failure(paths, exc)
        raise
    return paths


def run_experiment_to_artifacts(
    manifest: ExperimentManifest,
    *,
    data_root: str | Path,
    repository_root: str | Path,
    run_root: str | Path,
    run_timestamp: datetime | None = None,
) -> RunArtifactPaths:
    """Precommit when required, execute replay, and persist immutable artifacts."""

    prepared = prepare_experiment(
        manifest,
        data_root=data_root,
        repository_root=repository_root,
        run_timestamp=run_timestamp,
    )
    root = Path(run_root)
    commitment: FinalOosCommitment | None = None
    registry_path: Path | None = None
    if manifest.data_role is DataRole.FINAL_OOS:
        _assert_holdout_available(root, prepared)
        commitment = _initial_commitment(prepared)
    paths = _reserve_run_directory(root, prepared.provenance.run_id)
    _write_prelude(paths, prepared)
    if commitment is not None:
        _atomic_write_model(paths.commitment, commitment)
        try:
            registry_path = _reserve_holdout_registry(root, commitment)
        except BaseException as exc:
            _atomic_write_model(
                paths.commitment,
                _reservation_failed_commitment(commitment),
            )
            _write_failure(paths, exc)
            raise

    try:
        permit = (
            issue_final_oos_execution_permit(
                manifest=prepared.manifest,
                provenance=prepared.provenance,
                commitment_path=paths.commitment,
            )
            if commitment is not None
            else None
        )
        run = execute_precommitted_experiment(
            prepared,
            final_oos_permit=permit,
        )
        _write_completed_artifacts(paths, run)
    except BaseException as exc:
        _write_failure(paths, exc)
        if commitment is not None:
            consumed = _consume_commitment(commitment, status="failed")
            _atomic_write_model(paths.commitment, consumed)
            if registry_path is not None:
                _atomic_write_model(registry_path, consumed)
        raise
    if commitment is not None:
        consumed = _consume_commitment(commitment, status="completed")
        _atomic_write_model(paths.commitment, consumed)
        if registry_path is not None:
            _atomic_write_model(registry_path, consumed)
    _write_completed_integrity(paths)
    return paths


def _validate_loaded_commitment(
    *,
    manifest: ExperimentManifest,
    provenance: RunProvenance,
    result: ExperimentResult,
    commitment: FinalOosCommitment | None,
) -> None:
    if manifest.data_role is not DataRole.FINAL_OOS:
        if commitment is not None:
            raise ArtifactError("non-final run must not contain a commitment artifact")
        return
    if commitment is None:
        raise ArtifactError("final_oos run is missing its commitment artifact")
    if not commitment.consumed or commitment.execution_status != "completed":
        raise ArtifactError(
            "completed final_oos result requires a consumed completed commitment"
        )
    matches = (
        commitment.run_id == provenance.run_id,
        commitment.research_family_id == manifest.research_family_id,
        commitment.parent_run_id == manifest.parent_run_id,
        commitment.manifest_sha256 == provenance.manifest_sha256,
        commitment.code_fingerprint == provenance.code_fingerprint,
        commitment.data_fingerprints == provenance.data_fingerprints,
        commitment.data_window_start == manifest.data_window.start,
        commitment.data_window_end == manifest.data_window.end,
        commitment.committed_at == provenance.run_timestamp_utc,
        result.final_oos_consumed,
    )
    if not all(matches):
        raise ArtifactError(
            "final_oos commitment does not match manifest, provenance, and result"
        )


def _validate_event_contract(
    *,
    result: ExperimentResult,
    events: tuple[dict[str, Any], ...],
) -> None:
    expected_roles = tuple(item.role for item in result.roles)
    for role in expected_roles:
        count = sum(
            event.get("event_type") == "initial_state" and event.get("role") == role
            for event in events
        )
        if count != 1:
            raise ArtifactError(
                "event artifact must contain exactly one initial_state per result role"
            )

    if any(
        event.get("event_type") == "initial_state"
        and event.get("role") not in expected_roles
        for event in events
    ):
        raise ArtifactError(
            "event artifact contains initial_state for an unknown result role"
        )


def read_run_artifacts(run_directory: str | Path) -> LoadedRunArtifacts:
    directory = Path(run_directory).resolve()
    paths = _paths(directory.parent, directory.name)
    try:
        read_and_validate_integrity(
            directory,
            artifact_id=directory.name,
            required_files=frozenset(
                {
                    paths.manifest.name,
                    paths.provenance.name,
                    paths.result.name,
                    paths.performance.name,
                    paths.inventory.name,
                    paths.events.name,
                }
            ),
            allowed_files=frozenset(
                {
                    paths.manifest.name,
                    paths.provenance.name,
                    paths.result.name,
                    paths.performance.name,
                    paths.inventory.name,
                    paths.evidence.name,
                    paths.events.name,
                    paths.commitment.name,
                }
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        raise ArtifactError(f"artifact integrity validation failed: {exc}") from exc
    manifest = ExperimentManifest.model_validate_json(
        paths.manifest.read_text(encoding="utf-8")
    )
    provenance = RunProvenance.model_validate_json(
        paths.provenance.read_text(encoding="utf-8")
    )
    result = ExperimentResult.model_validate_json(
        paths.result.read_text(encoding="utf-8")
    )
    if provenance.run_id != directory.name or result.run_id != directory.name:
        raise ArtifactError("artifact run IDs do not match the directory name")
    if manifest_sha256(manifest) != provenance.manifest_sha256:
        raise ArtifactError("artifact manifest hash does not match provenance")
    if (
        provenance.research_family_id != manifest.research_family_id
        or result.research_family_id != manifest.research_family_id
    ):
        raise ArtifactError("artifact research family does not match manifest")
    if (
        provenance.data_role is not manifest.data_role
        or result.data_role is not manifest.data_role
    ):
        raise ArtifactError("artifact data role does not match manifest")
    if result.parent_run_id != manifest.parent_run_id:
        raise ArtifactError("artifact parent run does not match manifest")

    performance: Any = pq.read_table(paths.performance)
    inventory: Any = pq.read_table(paths.inventory)
    evidence: Any | None = (
        pq.read_table(paths.evidence) if paths.evidence.exists() else None
    )
    validate_artifact_table(
        performance,
        expected_schema="qap.experiment.performance.v1",
        run_id=directory.name,
    )
    validate_artifact_table(
        inventory,
        expected_schema="qap.experiment.inventory.v1",
        run_id=directory.name,
    )
    if evidence is not None:
        validate_artifact_table(
            evidence,
            expected_schema="qap.experiment.evidence.v1",
            run_id=directory.name,
        )
    try:
        validate_run_artifact_semantics(
            result=result,
            performance=performance,
            inventory=inventory,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ArtifactError(f"artifact semantic validation failed: {exc}") from exc
    events = read_event_records(paths.events, run_id=directory.name)
    _validate_event_contract(result=result, events=events)
    commitment = (
        FinalOosCommitment.model_validate_json(
            paths.commitment.read_text(encoding="utf-8")
        )
        if paths.commitment.exists()
        else None
    )
    if commitment is not None and commitment.run_id != directory.name:
        raise ArtifactError("commitment run ID does not match the directory name")
    _validate_loaded_commitment(
        manifest=manifest,
        provenance=provenance,
        result=result,
        commitment=commitment,
    )
    return LoadedRunArtifacts(
        manifest=manifest,
        provenance=provenance,
        result=result,
        performance=performance,
        inventory=inventory,
        evidence=evidence,
        events=events,
        commitment=commitment,
    )


def discover_family_runs(
    run_root: str | Path,
    research_family_id: str,
) -> tuple[Path, ...]:
    """Return all durable family attempts, including failed executions."""

    root = Path(run_root).resolve()
    discovered: list[tuple[bool, str, Path]] = []
    if not root.exists():
        return ()
    for manifest_path in root.glob("*/manifest.json"):
        try:
            manifest = ExperimentManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
        except OSError, TypeError, ValueError:
            continue
        if manifest.research_family_id == research_family_id:
            discovered.append(
                (
                    manifest.parent_run_id is not None,
                    manifest_path.parent.name,
                    manifest_path.parent,
                )
            )
    return tuple(path for _, _, path in sorted(discovered))


__all__ = [
    "ArtifactError",
    "FinalOosCommitment",
    "HoldoutAlreadyCommittedError",
    "LoadedRunArtifacts",
    "RunAlreadyExistsError",
    "RunArtifactPaths",
    "discover_family_runs",
    "read_run_artifacts",
    "run_experiment_to_artifacts",
    "write_run_artifacts",
]
