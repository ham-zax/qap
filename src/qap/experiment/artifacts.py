# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Immutable experiment run directories and final-OOS commitment discipline."""

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Self

import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.experiment.events import read_event_records, write_event_records
from qap.experiment.manifest import DataRole, ExperimentManifest
from qap.experiment.provenance import (
    DatasetFingerprint,
    RunProvenance,
    canonical_manifest_bytes,
    manifest_sha256,
)
from qap.experiment.result import ExperimentResult
from qap.experiment.runner import (
    ExperimentRun,
    PreparedExperiment,
    prepare_experiment,
)
from qap.experiment.runner import (
    execute_precommitted_experiment as execute_prepared_experiment,
)
from qap.experiment.tables import (
    build_inventory_table,
    build_performance_table,
    validate_artifact_table,
)

_FINAL_OOS_REGISTRY = ".final-oos-commitments"


class ArtifactError(RuntimeError):
    """Base error for immutable experiment artifact operations."""


class RunAlreadyExistsError(ArtifactError):
    """Raised when a run ID already has a directory and cannot be overwritten."""


class HoldoutAlreadyCommittedError(ArtifactError):
    """Raised when a research family already committed the same final holdout."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FinalOosCommitment(_FrozenModel):
    schema_version: Literal["qap.experiment.final_oos_commitment.v1"] = (
        "qap.experiment.final_oos_commitment.v1"
    )
    run_id: str
    research_family_id: str
    parent_run_id: str | None = None
    holdout_id: str
    manifest_sha256: str
    code_fingerprint: str
    data_fingerprints: tuple[DatasetFingerprint, ...]
    data_window_start: datetime
    data_window_end: datetime
    committed_at: datetime
    consumed: bool
    execution_status: Literal["committed", "completed", "failed"]
    consumed_at: datetime | None = None

    @field_validator(
        "data_window_start",
        "data_window_end",
        "committed_at",
        "consumed_at",
    )
    @classmethod
    def validate_utc(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("commitment timestamps must be timezone-aware UTC")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.data_window_start >= self.data_window_end:
            raise ValueError("commitment data window must be ordered")
        if self.execution_status == "committed":
            if self.consumed or self.consumed_at is not None:
                raise ValueError("unexecuted commitment cannot be consumed")
        elif not self.consumed or self.consumed_at is None:
            raise ValueError("completed or failed commitment must be consumed")
        return self


@dataclass(frozen=True, slots=True)
class RunArtifactPaths:
    run_id: str
    run_directory: Path
    manifest: Path
    provenance: Path
    result: Path
    performance: Path
    inventory: Path
    events: Path
    commitment: Path
    failure: Path


@dataclass(frozen=True, slots=True)
class LoadedRunArtifacts:
    manifest: ExperimentManifest
    provenance: RunProvenance
    result: ExperimentResult
    performance: Any
    inventory: Any
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
        events=directory / "events.jsonl",
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


def _holdout_id(prepared: PreparedExperiment) -> str:
    payload = {
        "data_fingerprints": [
            item.model_dump(mode="json") for item in prepared.loaded.data_fingerprints
        ],
        "data_window_start": prepared.manifest.data_window.start.isoformat(),
        "data_window_end": prepared.manifest.data_window.end.isoformat(),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"holdout-{hashlib.sha256(encoded).hexdigest()[:24]}"


def _holdout_registry_path(
    run_root: Path,
    commitment: FinalOosCommitment,
) -> Path:
    identity = (f"{commitment.research_family_id}\0{commitment.holdout_id}").encode(
        "utf-8"
    )
    filename = f"{hashlib.sha256(identity).hexdigest()}.json"
    return run_root.resolve() / _FINAL_OOS_REGISTRY / filename


def _reserve_holdout_registry(
    run_root: Path,
    commitment: FinalOosCommitment,
) -> Path:
    """Atomically reserve one family/holdout pair before replay can begin."""

    root = run_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    registry = root / _FINAL_OOS_REGISTRY
    registry.mkdir(exist_ok=True)
    path = _holdout_registry_path(root, commitment)
    payload = (commitment.model_dump_json(indent=2) + "\n").encode("utf-8")
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError as exc:
        raise HoldoutAlreadyCommittedError(
            "final OOS holdout is already committed for research family "
            f"{commitment.research_family_id}: {commitment.holdout_id}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        directory_descriptor = os.open(registry, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _existing_commitments(run_root: Path) -> tuple[FinalOosCommitment, ...]:
    commitments: list[FinalOosCommitment] = []
    if not run_root.exists():
        return ()
    for path in sorted(run_root.glob("*/commitment.json")):
        commitments.append(
            FinalOosCommitment.model_validate_json(path.read_text(encoding="utf-8"))
        )
    return tuple(commitments)


def _assert_holdout_available(
    run_root: Path,
    prepared: PreparedExperiment,
) -> None:
    holdout_id = _holdout_id(prepared)
    for commitment in _existing_commitments(run_root.resolve()):
        if (
            commitment.research_family_id == prepared.manifest.research_family_id
            and commitment.holdout_id == holdout_id
        ):
            raise HoldoutAlreadyCommittedError(
                "final OOS holdout is already committed for research family "
                f"{prepared.manifest.research_family_id}: {holdout_id}"
            )


def _initial_commitment(prepared: PreparedExperiment) -> FinalOosCommitment:
    return FinalOosCommitment(
        run_id=prepared.provenance.run_id,
        research_family_id=prepared.manifest.research_family_id,
        parent_run_id=prepared.manifest.parent_run_id,
        holdout_id=_holdout_id(prepared),
        manifest_sha256=prepared.provenance.manifest_sha256,
        code_fingerprint=prepared.provenance.code_fingerprint,
        data_fingerprints=prepared.loaded.data_fingerprints,
        data_window_start=prepared.manifest.data_window.start,
        data_window_end=prepared.manifest.data_window.end,
        committed_at=prepared.provenance.run_timestamp_utc,
        consumed=False,
        execution_status="committed",
        consumed_at=None,
    )


def _consume_commitment(
    commitment: FinalOosCommitment,
    *,
    status: Literal["completed", "failed"],
) -> FinalOosCommitment:
    return commitment.model_copy(
        update={
            "consumed": True,
            "execution_status": status,
            "consumed_at": datetime.now(UTC),
        }
    )


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
    write_event_records(paths.events, run)


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
        registry_path = _reserve_holdout_registry(root, commitment)
    paths = _reserve_run_directory(root, prepared.provenance.run_id)
    _write_prelude(paths, prepared)
    if commitment is not None:
        _atomic_write_model(paths.commitment, commitment)

    try:
        run = execute_prepared_experiment(prepared)
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


def read_run_artifacts(run_directory: str | Path) -> LoadedRunArtifacts:
    directory = Path(run_directory).resolve()
    paths = _paths(directory.parent, directory.name)
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
    events = read_event_records(paths.events, run_id=directory.name)
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
        events=events,
        commitment=commitment,
    )


def discover_family_runs(
    run_root: str | Path,
    research_family_id: str,
) -> tuple[Path, ...]:
    """Return root runs before descendants for one explicit research family."""

    root = Path(run_root).resolve()
    discovered: list[tuple[bool, str, Path]] = []
    if not root.exists():
        return ()
    for result_path in root.glob("*/result.json"):
        result = ExperimentResult.model_validate_json(
            result_path.read_text(encoding="utf-8")
        )
        if result.research_family_id == research_family_id:
            discovered.append(
                (
                    result.parent_run_id is not None,
                    result.run_id,
                    result_path.parent,
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
