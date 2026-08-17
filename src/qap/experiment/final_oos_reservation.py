"""Durable final-OOS commitment state and atomic family/holdout reservation."""

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.experiment.provenance import DatasetFingerprint
from qap.experiment.runner import PreparedExperiment
from qap.market import fingerprint_bar_series, validate_bar_series

FINAL_OOS_REGISTRY = ".final-oos-commitments"


class HoldoutAlreadyCommittedError(RuntimeError):
    """Raised when one research family already reserved the same holdout."""


class FinalOosCommitment(BaseModel):
    """Durable information-state record for one final-OOS attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    execution_status: Literal[
        "committed",
        "reservation_failed",
        "completed",
        "failed",
    ]
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
        if self.execution_status in {"committed", "reservation_failed"}:
            if self.consumed or self.consumed_at is not None:
                raise ValueError(
                    "unconsumed commitment state cannot declare consumption"
                )
        elif not self.consumed or self.consumed_at is None:
            raise ValueError(
                "completed/failed final-OOS commitment must be marked consumed"
            )
        return self


def holdout_id(prepared: PreparedExperiment) -> str:
    evaluated_slice_fingerprints = tuple(
        sorted(
            fingerprint_bar_series(validate_bar_series(item.bars))
            for item in prepared.loaded.aligned.series
        )
    )
    payload = {
        "evaluated_slice_fingerprints": evaluated_slice_fingerprints,
        "data_window_start": prepared.manifest.data_window.start.isoformat(),
        "data_window_end": prepared.manifest.data_window.end.isoformat(),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"holdout-{hashlib.sha256(encoded).hexdigest()[:24]}"


def holdout_registry_path(
    run_root: Path,
    commitment: FinalOosCommitment,
) -> Path:
    identity = (f"{commitment.research_family_id}\0{commitment.holdout_id}").encode(
        "utf-8"
    )
    filename = f"{hashlib.sha256(identity).hexdigest()}.json"
    return run_root.resolve() / FINAL_OOS_REGISTRY / filename


def reserve_holdout_registry(
    run_root: Path,
    commitment: FinalOosCommitment,
) -> Path:
    """Atomically reserve one family/holdout pair before replay can begin."""

    root = run_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    registry = root / FINAL_OOS_REGISTRY
    registry.mkdir(exist_ok=True)
    path = holdout_registry_path(root, commitment)
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


def existing_commitments(run_root: Path) -> tuple[FinalOosCommitment, ...]:
    commitments: list[FinalOosCommitment] = []
    if not run_root.exists():
        return ()
    for path in sorted(run_root.glob("*/commitment.json")):
        commitments.append(
            FinalOosCommitment.model_validate_json(path.read_text(encoding="utf-8"))
        )
    return tuple(commitments)


def assert_holdout_available(
    run_root: Path,
    prepared: PreparedExperiment,
) -> None:
    candidate_holdout_id = holdout_id(prepared)
    for commitment in existing_commitments(run_root.resolve()):
        if (
            commitment.research_family_id != prepared.manifest.research_family_id
            or commitment.holdout_id != candidate_holdout_id
        ):
            continue
        if commitment.execution_status == "reservation_failed":
            continue
        if commitment.execution_status == "committed":
            registry_path = holdout_registry_path(run_root, commitment)
            if not registry_path.is_file():
                continue
        raise HoldoutAlreadyCommittedError(
            "final OOS holdout is already committed for research family "
            f"{prepared.manifest.research_family_id}: {candidate_holdout_id}"
        )


def initial_commitment(prepared: PreparedExperiment) -> FinalOosCommitment:
    return FinalOosCommitment(
        run_id=prepared.provenance.run_id,
        research_family_id=prepared.manifest.research_family_id,
        parent_run_id=prepared.manifest.parent_run_id,
        holdout_id=holdout_id(prepared),
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


def reservation_failed_commitment(
    commitment: FinalOosCommitment,
) -> FinalOosCommitment:
    return commitment.model_copy(update={"execution_status": "reservation_failed"})


def consume_commitment(
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


__all__ = [
    "FINAL_OOS_REGISTRY",
    "FinalOosCommitment",
    "HoldoutAlreadyCommittedError",
    "assert_holdout_available",
    "consume_commitment",
    "holdout_id",
    "holdout_registry_path",
    "initial_commitment",
    "reservation_failed_commitment",
    "reserve_holdout_registry",
]
