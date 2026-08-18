"""Exact physical file-set integrity for immutable scanner artifacts."""

import hashlib
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

INTEGRITY_FILE = "integrity.json"


class ScannerArtifactIntegrity(BaseModel):
    """Immutable byte digests for one completed scanner generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qap.scanner.integrity.v1"] = "qap.scanner.integrity.v1"
    scan_id: str
    files: dict[str, str]

    @field_validator("scan_id")
    @classmethod
    def validate_scan_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("scan_id must be a SHA-256 fingerprint")
        return normalized

    @field_validator("files")
    @classmethod
    def validate_files(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("scanner integrity must contain authoritative files")
        normalized: dict[str, str] = {}
        for name, digest in value.items():
            if not name or Path(name).name != name or name == INTEGRITY_FILE:
                raise ValueError("scanner integrity names must be sibling files")
            lowered = digest.strip().lower()
            if len(lowered) != 64 or any(
                character not in "0123456789abcdef" for character in lowered
            ):
                raise ValueError(f"invalid SHA-256 digest for {name}")
            normalized[name] = lowered
        return dict(sorted(normalized.items()))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(record: ScannerArtifactIntegrity) -> bytes:
    return (
        json.dumps(
            record.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_scanner_integrity(
    directory: Path,
    *,
    scan_id: str,
    authoritative_files: frozenset[str],
) -> ScannerArtifactIntegrity:
    root = directory.resolve()
    digests: dict[str, str] = {}
    for name in sorted(authoritative_files):
        path = root / name
        if not path.is_file():
            raise ValueError(f"scanner authoritative file is missing: {name}")
        digests[name] = sha256_file(path)
    record = ScannerArtifactIntegrity(scan_id=scan_id, files=digests)
    target = root / INTEGRITY_FILE
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("wb") as handle:
            handle.write(_canonical_bytes(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return record


def validate_scanner_integrity(
    directory: Path,
    *,
    scan_id: str,
    authoritative_files: frozenset[str],
) -> ScannerArtifactIntegrity:
    root = directory.resolve()
    path = root / INTEGRITY_FILE
    if not path.is_file():
        raise ValueError("scanner integrity record is missing")
    try:
        record = ScannerArtifactIntegrity.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise ValueError("scanner integrity record is malformed") from exc
    if record.scan_id != scan_id:
        raise ValueError("scanner integrity identity does not match")
    expected = frozenset(authoritative_files)
    declared = frozenset(record.files)
    physical = frozenset(
        candidate.name
        for candidate in root.iterdir()
        if candidate.is_file() and candidate.name != INTEGRITY_FILE
    )
    if declared != expected or physical != expected:
        missing = sorted(expected - physical)
        unexpected = sorted(physical - expected)
        detail: list[str] = []
        if missing:
            detail.append(f"missing={missing}")
        if unexpected:
            detail.append(f"unexpected={unexpected}")
        if declared != expected:
            detail.append("declared set differs from authoritative contract")
        raise ValueError("scanner integrity file set mismatch: " + "; ".join(detail))
    for name, expected_digest in record.files.items():
        if sha256_file(root / name) != expected_digest:
            raise ValueError(f"scanner integrity digest mismatch: {name}")
    return record


__all__ = [
    "INTEGRITY_FILE",
    "ScannerArtifactIntegrity",
    "sha256_file",
    "validate_scanner_integrity",
    "write_scanner_integrity",
]
