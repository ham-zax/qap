"""Deterministic experiment provenance and run identity."""

import hashlib
import json
import struct
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from typing_extensions import Annotated

from qap.experiment.manifest import DataRole, ExperimentManifest

_FINGERPRINT_LENGTH = 64
_EXCLUDED_DIRECTORY_NAMES = frozenset({"__pycache__"})
_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ProvenanceError(RuntimeError):
    """Raised when authoritative or supplemental provenance cannot be captured."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validated_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != _FINGERPRINT_LENGTH:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex")
    try:
        bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex") from exc
    return normalized


class DatasetFingerprint(_FrozenModel):
    dataset_id: Identifier
    fingerprint: str

    @field_validator("fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return _validated_sha256(value, field="dataset fingerprint")


class RunProvenance(_FrozenModel):
    schema_version: Literal["qap.experiment.provenance.v1"] = (
        "qap.experiment.provenance.v1"
    )
    run_id: Identifier
    manifest_sha256: str
    data_fingerprints: tuple[DatasetFingerprint, ...]
    code_fingerprint: str
    git_commit: Identifier
    git_dirty: bool
    qap_version: Identifier
    run_timestamp_utc: datetime
    research_family_id: Identifier
    data_role: DataRole

    @field_validator("manifest_sha256", "code_fingerprint")
    @classmethod
    def validate_sha256(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "fingerprint")
        return _validated_sha256(value, field=str(field_name))

    @field_validator("run_timestamp_utc")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("run_timestamp_utc must be timezone-aware UTC")
        return value.astimezone(UTC)


def canonical_manifest_bytes(manifest: ExperimentManifest) -> bytes:
    """Serialize one validated manifest independently of input JSON key ordering."""

    if not isinstance(cast(object, manifest), ExperimentManifest):
        raise TypeError("manifest must be an ExperimentManifest")
    payload = manifest.model_dump(mode="json", exclude_none=False)
    if not manifest.relationship_instrument_ids:
        payload.pop("relationship_instrument_ids", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def manifest_sha256(manifest: ExperimentManifest) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def _authoritative_code_paths(repository_root: Path) -> tuple[Path, ...]:
    source_root = repository_root / "src" / "qap"
    required = (
        source_root,
        repository_root / "pyproject.toml",
        repository_root / "uv.lock",
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise ProvenanceError(f"authoritative code inputs are missing: {formatted}")

    source_files = tuple(
        path
        for path in source_root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not any(part in _EXCLUDED_DIRECTORY_NAMES for part in path.parts)
        and path.suffix not in _EXCLUDED_SUFFIXES
    )
    return tuple(
        sorted(
            (
                *source_files,
                repository_root / "pyproject.toml",
                repository_root / "uv.lock",
            ),
            key=lambda path: path.relative_to(repository_root).as_posix(),
        )
    )


def code_fingerprint(repository_root: str | Path) -> str:
    """Hash sorted authoritative relative paths and bytes, excluding caches."""

    root = Path(repository_root).resolve()
    digest = hashlib.sha256(b"QAP-CODE-FINGERPRINT\x00")
    for path in _authoritative_code_paths(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(struct.pack(">I", len(relative)))
        digest.update(relative)
        digest.update(struct.pack(">Q", len(content)))
        digest.update(content)
    return digest.hexdigest()


def _ordered_data_fingerprints(
    values: object,
) -> tuple[DatasetFingerprint, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("data_fingerprints must be iterable")
    copied: list[DatasetFingerprint] = []
    for position, item in enumerate(cast(Iterable[object], values)):
        if not isinstance(item, DatasetFingerprint):
            raise TypeError(f"data fingerprint {position} must be a DatasetFingerprint")
        copied.append(item)
    result = tuple(copied)
    if not result:
        raise ValueError("at least one dataset fingerprint is required")
    identifiers = tuple(item.dataset_id for item in result)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("dataset fingerprint identifiers must be unique")
    return result


def deterministic_run_id(
    *,
    manifest_sha256: str,
    data_fingerprints: Iterable[DatasetFingerprint],
    code_fingerprint: str,
) -> str:
    """Derive run identity only from validated manifest, data, and code bytes."""

    manifest_hash = _validated_sha256(
        manifest_sha256,
        field="manifest_sha256",
    )
    code_hash = _validated_sha256(code_fingerprint, field="code_fingerprint")
    data = _ordered_data_fingerprints(data_fingerprints)
    payload = {
        "manifest_sha256": manifest_hash,
        "data_fingerprints": [item.model_dump(mode="json") for item in data],
        "code_fingerprint": code_hash,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"run-{hashlib.sha256(encoded).hexdigest()[:24]}"


def _git_output(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise ProvenanceError(
            f"Git provenance command failed ({' '.join(arguments)}): {detail}"
        )
    return completed.stdout.strip()


def _package_version() -> str:
    try:
        return version("qap")
    except PackageNotFoundError as exc:
        raise ProvenanceError("installed QAP package version is unavailable") from exc


def capture_run_provenance(
    *,
    manifest: ExperimentManifest,
    data_fingerprints: Iterable[DatasetFingerprint],
    repository_root: str | Path,
    run_timestamp: datetime | None = None,
) -> RunProvenance:
    """Capture authoritative run identity plus supplemental local Git context."""

    if not isinstance(cast(object, manifest), ExperimentManifest):
        raise TypeError("manifest must be an ExperimentManifest")
    root = Path(repository_root).resolve()
    data = _ordered_data_fingerprints(data_fingerprints)
    expected = tuple(
        DatasetFingerprint(
            dataset_id=source.dataset_id,
            fingerprint=source.expected_semantic_fingerprint,
        )
        for source in manifest.data_sources
    )
    if data != expected:
        raise ProvenanceError(
            "loaded dataset fingerprints do not match the ordered manifest commitments"
        )

    manifest_hash = manifest_sha256(manifest)
    code_hash = code_fingerprint(root)
    timestamp = datetime.now(UTC) if run_timestamp is None else run_timestamp
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError("run_timestamp must be timezone-aware UTC")
    timestamp = timestamp.astimezone(UTC)
    return RunProvenance(
        run_id=deterministic_run_id(
            manifest_sha256=manifest_hash,
            data_fingerprints=data,
            code_fingerprint=code_hash,
        ),
        manifest_sha256=manifest_hash,
        data_fingerprints=data,
        code_fingerprint=code_hash,
        git_commit=_git_output(root, "rev-parse", "HEAD"),
        git_dirty=bool(
            _git_output(root, "status", "--porcelain", "--untracked-files=normal")
        ),
        qap_version=_package_version(),
        run_timestamp_utc=timestamp,
        research_family_id=manifest.research_family_id,
        data_role=manifest.data_role,
    )


__all__ = [
    "DatasetFingerprint",
    "ProvenanceError",
    "RunProvenance",
    "canonical_manifest_bytes",
    "capture_run_provenance",
    "code_fingerprint",
    "deterministic_run_id",
    "manifest_sha256",
]
