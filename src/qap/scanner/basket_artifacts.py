# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Immutable manual-basket definitions and replay-attempt lineage."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from qap.artifact_integrity import (
    INTEGRITY_FILE,
    build_integrity_record,
    read_and_validate_integrity,
)
from qap.scanner.basket import BasketDefinition

DEFINITION = "definition.json"
REPLAY_ATTEMPT = "replay_attempt.json"
MANIFEST = "manifest.json"
AUTHORITATIVE_FILES = frozenset({DEFINITION, REPLAY_ATTEMPT, MANIFEST})


class BasketArtifactError(ValueError):
    """Raised when basket search evidence cannot be persisted or reconciled."""


class BasketReplayStatus(StrEnum):
    ENUMERATED = "enumerated"
    SETUP_FAILED = "setup_failed"
    REPLAY_FAILED = "replay_failed"
    COMPLETED = "completed"


class BasketEconomicGateStatus(StrEnum):
    DEVELOPMENT_SURVIVOR = "basket_development_survivor"
    DEVELOPMENT_REJECTED = "basket_development_rejected"


class BasketReplayAttempt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    schema_version: str = "qap.scanner.basket-replay-attempt.v1"
    attempt_id: str
    basket_id: str
    status: BasketReplayStatus
    failure_stage: str | None = None
    failure_reason: str | None = None
    qap_run_id: str | None = None
    economic_gate_status: BasketEconomicGateStatus | None = None

    @model_validator(mode="after")
    def validate_state(self) -> "BasketReplayAttempt":
        if self.status is BasketReplayStatus.ENUMERATED:
            if any(
                value is not None
                for value in (
                    self.failure_stage,
                    self.failure_reason,
                    self.qap_run_id,
                    self.economic_gate_status,
                )
            ):
                raise ValueError(
                    "enumerated basket attempt cannot carry outcome fields"
                )
            return self
        if self.status is BasketReplayStatus.COMPLETED:
            if not self.qap_run_id:
                raise ValueError("completed basket attempt requires QAP run ID")
            if self.economic_gate_status is None:
                raise ValueError(
                    "completed basket attempt requires economic gate status"
                )
            if self.failure_stage is not None or self.failure_reason is not None:
                raise ValueError("completed basket attempt cannot carry failure fields")
            return self
        if not self.failure_stage or not self.failure_reason:
            raise ValueError("failed basket attempt requires failure stage/reason")
        if self.qap_run_id is not None:
            raise ValueError("failed basket attempt cannot carry QAP run ID")
        if self.economic_gate_status is not None:
            raise ValueError("failed basket attempt cannot carry economic gate status")
        return self


@dataclass(frozen=True, slots=True)
class BasketArtifactGeneration:
    root: Path
    definition: BasketDefinition
    staging_directory: Path
    final_directory: Path

    @property
    def attempt_path(self) -> Path:
        return self.staging_directory / REPLAY_ATTEMPT


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _definition_payload(definition: BasketDefinition) -> dict[str, object]:
    payload = definition.model_dump(mode="json")
    payload["basket_id"] = definition.basket_id
    payload["research_family_id"] = definition.research_family_id
    return payload


def _attempt_id(basket_id: str) -> str:
    payload = f"qap.scanner.basket-attempt.v1\0{basket_id}\0replay".encode()
    return sha256(payload).hexdigest()


def _enumerated_attempt(definition: BasketDefinition) -> BasketReplayAttempt:
    return BasketReplayAttempt(
        attempt_id=_attempt_id(definition.basket_id),
        basket_id=definition.basket_id,
        status=BasketReplayStatus.ENUMERATED,
    )


def _read_definition(path: Path) -> BasketDefinition:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BasketArtifactError("basket definition is malformed") from exc
    if not isinstance(payload, dict):
        raise BasketArtifactError("basket definition must be a JSON object")
    declared_id = payload.pop("basket_id", None)
    declared_family = payload.pop("research_family_id", None)
    try:
        definition = BasketDefinition.model_validate(payload)
    except ValueError as exc:
        raise BasketArtifactError("basket definition is invalid") from exc
    if declared_id != definition.basket_id:
        raise BasketArtifactError("basket definition identity mismatch")
    if declared_family != definition.research_family_id:
        raise BasketArtifactError("basket family identity mismatch")
    return definition


def _read_attempt(path: Path) -> BasketReplayAttempt:
    try:
        return BasketReplayAttempt.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BasketArtifactError("basket replay attempt is malformed") from exc


def start_basket_generation(
    run_root: str | Path,
    definition: BasketDefinition,
) -> BasketArtifactGeneration:
    """Create/resume one basket staging generation with attempt already enumerated."""

    root = Path(run_root).resolve() / "baskets"
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{definition.basket_id}.partial"
    final = root / definition.basket_id
    if final.exists():
        raise BasketArtifactError("completed basket generation already exists")
    if staging.exists():
        stored = _read_definition(staging / DEFINITION)
        requested = definition.model_copy(update={"created_at": stored.created_at})
        if stored != requested:
            raise BasketArtifactError("partial basket definition mismatch")
        attempt = _read_attempt(staging / REPLAY_ATTEMPT)
        if attempt.basket_id != stored.basket_id:
            raise BasketArtifactError("partial basket attempt identity mismatch")
        return BasketArtifactGeneration(root, stored, staging, final)

    staging.mkdir()
    generation = BasketArtifactGeneration(root, definition, staging, final)
    _atomic_write(staging / DEFINITION, _json_bytes(_definition_payload(definition)))
    _atomic_write(
        staging / REPLAY_ATTEMPT,
        _enumerated_attempt(definition).model_dump_json().encode("utf-8"),
    )
    return generation


def read_basket_attempt(generation: BasketArtifactGeneration) -> BasketReplayAttempt:
    attempt = _read_attempt(generation.attempt_path)
    if attempt.basket_id != generation.definition.basket_id:
        raise BasketArtifactError("basket replay attempt identity mismatch")
    return attempt


def transition_basket_attempt(
    generation: BasketArtifactGeneration,
    *,
    status: BasketReplayStatus,
    failure_stage: str | None = None,
    failure_reason: str | None = None,
    qap_run_id: str | None = None,
    economic_gate_status: BasketEconomicGateStatus | None = None,
) -> BasketReplayAttempt:
    """Move the single enumerated attempt to one terminal state exactly once."""

    if status is BasketReplayStatus.ENUMERATED:
        raise BasketArtifactError("basket attempt transition requires terminal status")
    current = read_basket_attempt(generation)
    replacement = BasketReplayAttempt(
        attempt_id=current.attempt_id,
        basket_id=current.basket_id,
        status=status,
        failure_stage=failure_stage,
        failure_reason=failure_reason,
        qap_run_id=qap_run_id,
        economic_gate_status=economic_gate_status,
    )
    if current.status is not BasketReplayStatus.ENUMERATED:
        if current == replacement:
            return current
        raise BasketArtifactError("basket replay attempt is already terminal")
    _atomic_write(
        generation.attempt_path,
        replacement.model_dump_json().encode("utf-8"),
    )
    return replacement


def publish_basket_generation(generation: BasketArtifactGeneration) -> Path:
    """Seal and atomically publish one terminal basket search generation."""

    if generation.final_directory.exists():
        raise BasketArtifactError("completed basket generation already exists")
    stored = _read_definition(generation.staging_directory / DEFINITION)
    if stored != generation.definition:
        raise BasketArtifactError("basket definition changed before publication")
    attempt = read_basket_attempt(generation)
    if attempt.status is BasketReplayStatus.ENUMERATED:
        raise BasketArtifactError("cannot publish an enumerated basket attempt")
    manifest = {
        "schema_version": "qap.scanner.basket-manifest.v1",
        "basket_id": stored.basket_id,
        "research_family_id": stored.research_family_id,
        "attempt_id": attempt.attempt_id,
        "attempt_status": attempt.status.value,
        "qap_run_id": attempt.qap_run_id,
        "economic_gate_status": (
            None
            if attempt.economic_gate_status is None
            else attempt.economic_gate_status.value
        ),
        "forensic": stored.forensic,
        "published_at": datetime.now(UTC).isoformat(),
    }
    _atomic_write(generation.staging_directory / MANIFEST, _json_bytes(manifest))
    try:
        integrity = build_integrity_record(
            generation.staging_directory,
            artifact_id=stored.basket_id,
            file_names=tuple(sorted(AUTHORITATIVE_FILES)),
        )
        _atomic_write(
            generation.staging_directory / INTEGRITY_FILE,
            integrity.model_dump_json().encode("utf-8"),
        )
        read_and_validate_integrity(
            generation.staging_directory,
            artifact_id=stored.basket_id,
            required_files=AUTHORITATIVE_FILES,
            allowed_files=AUTHORITATIVE_FILES,
        )
        os.replace(generation.staging_directory, generation.final_directory)
    except (OSError, ValueError) as exc:
        raise BasketArtifactError("failed to publish basket generation") from exc
    return generation.final_directory


def read_basket_generation(
    directory: str | Path,
) -> tuple[BasketDefinition, BasketReplayAttempt, dict[str, object]]:
    """Read and reconcile one completed immutable basket generation."""

    root = Path(directory).resolve()
    try:
        read_and_validate_integrity(
            root,
            artifact_id=root.name,
            required_files=AUTHORITATIVE_FILES,
            allowed_files=AUTHORITATIVE_FILES,
        )
    except ValueError as exc:
        raise BasketArtifactError(str(exc)) from exc
    definition = _read_definition(root / DEFINITION)
    attempt = _read_attempt(root / REPLAY_ATTEMPT)
    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BasketArtifactError("basket manifest is malformed") from exc
    if not isinstance(manifest, dict):
        raise BasketArtifactError("basket manifest must be a JSON object")
    if definition.basket_id != root.name or attempt.basket_id != root.name:
        raise BasketArtifactError("basket artifact identity mismatch")
    if manifest.get("basket_id") != root.name:
        raise BasketArtifactError("basket manifest identity mismatch")
    if manifest.get("research_family_id") != definition.research_family_id:
        raise BasketArtifactError("basket manifest family mismatch")
    if manifest.get("attempt_id") != attempt.attempt_id:
        raise BasketArtifactError("basket manifest attempt mismatch")
    if manifest.get("attempt_status") != attempt.status.value:
        raise BasketArtifactError("basket manifest status mismatch")
    if manifest.get("qap_run_id") != attempt.qap_run_id:
        raise BasketArtifactError("basket manifest QAP run mismatch")
    expected_gate = (
        None
        if attempt.economic_gate_status is None
        else attempt.economic_gate_status.value
    )
    if manifest.get("economic_gate_status") != expected_gate:
        raise BasketArtifactError("basket manifest economic gate mismatch")
    return definition, attempt, manifest


__all__ = [
    "BasketArtifactError",
    "BasketArtifactGeneration",
    "BasketEconomicGateStatus",
    "BasketReplayAttempt",
    "BasketReplayStatus",
    "publish_basket_generation",
    "read_basket_attempt",
    "read_basket_generation",
    "start_basket_generation",
    "transition_basket_attempt",
]
