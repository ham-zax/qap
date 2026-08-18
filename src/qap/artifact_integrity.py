"""Exact file-set and digest integrity for immutable QAP artifact directories."""

import hashlib
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

INTEGRITY_FILE = "integrity.json"


class ArtifactIntegrity(BaseModel):
    """Immutable digests for authoritative files in one artifact directory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qap.artifact.integrity.v1"] = "qap.artifact.integrity.v1"
    artifact_id: str
    files: dict[str, str]

    @field_validator("artifact_id")
    @classmethod
    def validate_artifact_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("artifact_id must not be empty")
        return normalized

    @field_validator("files")
    @classmethod
    def validate_files(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("integrity record must contain at least one file")
        normalized: dict[str, str] = {}
        for name, digest in value.items():
            if not name or Path(name).name != name or name == INTEGRITY_FILE:
                raise ValueError(
                    "integrity file names must be plain sibling file names"
                )
            lowered = digest.strip().lower()
            if len(lowered) != 64 or any(
                character not in "0123456789abcdef" for character in lowered
            ):
                raise ValueError(f"invalid SHA-256 digest for {name}")
            normalized[name] = lowered
        return dict(sorted(normalized.items()))

    @model_validator(mode="after")
    def validate_no_duplicate_names(self) -> Self:
        if len(self.files) != len(set(self.files)):
            raise ValueError("integrity file names must be unique")
        return self


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_integrity_record(
    directory: Path,
    *,
    artifact_id: str,
    file_names: tuple[str, ...],
) -> ArtifactIntegrity:
    root = directory.resolve()
    digests: dict[str, str] = {}
    for name in file_names:
        path = root / name
        if not path.is_file():
            raise ValueError(f"authoritative artifact file is missing: {name}")
        digests[name] = sha256_file(path)
    return ArtifactIntegrity(artifact_id=artifact_id, files=digests)


def read_and_validate_integrity(
    directory: Path,
    *,
    artifact_id: str,
    required_files: frozenset[str],
    allowed_files: frozenset[str],
    ignored_files: frozenset[str] = frozenset(),
) -> ArtifactIntegrity:
    root = directory.resolve()
    path = root / INTEGRITY_FILE
    if not path.is_file():
        raise ValueError("artifact integrity record is missing")
    integrity = ArtifactIntegrity.model_validate_json(path.read_text(encoding="utf-8"))
    if integrity.artifact_id != artifact_id:
        raise ValueError("artifact integrity identity does not match")
    declared = frozenset(integrity.files)
    if not required_files.issubset(declared):
        missing = ", ".join(sorted(required_files - declared))
        raise ValueError(
            f"artifact integrity record is missing required files: {missing}"
        )
    if not declared.issubset(allowed_files):
        unexpected = ", ".join(sorted(declared - allowed_files))
        raise ValueError(
            f"artifact integrity record contains unexpected files: {unexpected}"
        )
    physical_authoritative = frozenset(
        candidate.name
        for candidate in root.iterdir()
        if candidate.is_file()
        and candidate.name != INTEGRITY_FILE
        and candidate.name not in ignored_files
    )
    if physical_authoritative != declared:
        undeclared = ", ".join(sorted(physical_authoritative - declared))
        missing = ", ".join(sorted(declared - physical_authoritative))
        detail: list[str] = []
        if undeclared:
            detail.append(f"undeclared authoritative files: {undeclared}")
        if missing:
            detail.append(f"declared authoritative files missing: {missing}")
        raise ValueError("artifact integrity file set mismatch: " + "; ".join(detail))
    for name, expected in integrity.files.items():
        candidate = root / name
        if not candidate.is_file():
            raise ValueError(f"artifact integrity file is missing: {name}")
        if sha256_file(candidate) != expected:
            raise ValueError(f"artifact integrity digest mismatch: {name}")
    return integrity


__all__ = [
    "ArtifactIntegrity",
    "INTEGRITY_FILE",
    "build_integrity_record",
    "read_and_validate_integrity",
    "sha256_file",
]
