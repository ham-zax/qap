"""Immutable append-only qualification evidence for prospective candidates."""

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import cast

from qap.artifact_integrity import (
    INTEGRITY_FILE,
    build_integrity_record,
    read_and_validate_integrity,
)
from qap.scanner.prospective_artifact_schemas import CHECKPOINT_TABLE
from qap.scanner.prospective_integrity import (
    completed_generation_dirs,
    validate_completed_generation,
)
from qap.scanner.qualification import QualificationDecision

QUALIFICATION_DIRECTORY = "qualification-generations"
QUALIFICATION_FILE = "qualification.json"
QUALIFICATION_AUTHORITATIVE_FILES = frozenset({QUALIFICATION_FILE})


class QualificationArtifactError(ValueError):
    """Raised when qualification evidence is malformed or violates lineage."""


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _identity(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise QualificationArtifactError(f"{field} must be a SHA-256 fingerprint")
    return normalized


@dataclass(frozen=True, slots=True)
class QualificationEvidence:
    checkpoint_id: str
    decision: QualificationDecision
    q_star_buy: Decimal | None
    q_safe_buy: Decimal | None
    q_star_sell: Decimal | None
    q_safe_sell: Decimal | None
    current_base_weight: Decimal | None
    required_buy_fraction: Decimal | None
    required_sell_fraction: Decimal | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checkpoint_id",
            _identity(self.checkpoint_id, field="checkpoint_id"),
        )
        positive_values = (
            self.q_star_buy,
            self.q_safe_buy,
            self.q_star_sell,
            self.q_safe_sell,
            self.required_buy_fraction,
            self.required_sell_fraction,
        )
        for value in positive_values:
            if value is not None and (not value.is_finite() or value <= 0):
                raise QualificationArtifactError(
                    "qualification numeric evidence must be positive finite"
                )
        if self.current_base_weight is not None and (
            not self.current_base_weight.is_finite()
            or not Decimal("0") <= self.current_base_weight <= Decimal("1")
        ):
            raise QualificationArtifactError(
                "current_base_weight must be within [0, 1]"
            )
        all_values = (*positive_values, self.current_base_weight)
        if self.decision.request.candidate_capital_ceiling is not None and any(
            value is None for value in all_values
        ):
            raise QualificationArtifactError(
                "known capital ceiling requires directional capacity evidence"
            )

    @property
    def qualification_id(self) -> str:
        return sha256(_canonical_bytes(_payload(self))).hexdigest()


def _request_payload(evidence: QualificationEvidence) -> dict[str, object]:
    request = evidence.decision.request
    return {
        "candidate_id": request.candidate_id,
        "freeze_id": request.freeze_id,
        "as_of": request.as_of.isoformat(),
        "requested_capital": _decimal_text(request.requested_capital),
        "prospective_protocol_version": request.prospective_protocol_version,
        "prospective_protocol_identity": request.prospective_protocol_identity,
        "capture_snapshot_ids": list(request.capture_snapshot_ids),
        "market_metadata_fingerprint": request.market_metadata_fingerprint,
        "eligibility_resolved": request.eligibility_resolved,
        "capture_contract_satisfied": request.capture_contract_satisfied,
        "current_two_way_trading": request.current_two_way_trading,
        "order_constraints_satisfied": request.order_constraints_satisfied,
        "candidate_capital_ceiling": _decimal_text(request.candidate_capital_ceiling),
        "requested_capital_qap_run_id": request.requested_capital_qap_run_id,
        "requested_baseline_gate_passed": request.requested_baseline_gate_passed,
        "requested_adverse_gate_passed": request.requested_adverse_gate_passed,
        "lower_tested_capital": _decimal_text(request.lower_tested_capital),
        "lower_capital_qap_run_id": request.lower_capital_qap_run_id,
        "lower_baseline_gate_passed": request.lower_baseline_gate_passed,
        "lower_adverse_gate_passed": request.lower_adverse_gate_passed,
    }


def _payload(evidence: QualificationEvidence) -> dict[str, object]:
    return {
        "schema_version": "qap.scanner.qualification-evidence.v1",
        "checkpoint_id": evidence.checkpoint_id,
        "state": evidence.decision.state.value,
        "reason": evidence.decision.reason.value,
        "liquidity_policy_version": evidence.decision.liquidity_policy_version,
        "request": _request_payload(evidence),
        "directional_capacity": {
            "q_star_buy": _decimal_text(evidence.q_star_buy),
            "q_safe_buy": _decimal_text(evidence.q_safe_buy),
            "q_star_sell": _decimal_text(evidence.q_star_sell),
            "q_safe_sell": _decimal_text(evidence.q_safe_sell),
            "current_base_weight": _decimal_text(evidence.current_base_weight),
            "required_buy_fraction": _decimal_text(evidence.required_buy_fraction),
            "required_sell_fraction": _decimal_text(evidence.required_sell_fraction),
        },
    }


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _checkpoint_lineage(
    cohort_root: Path,
    checkpoint_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    for directory in completed_generation_dirs(cohort_root):
        manifest, tables = validate_completed_generation(directory)
        if manifest.get("checkpoint_id") != checkpoint_id:
            continue
        rows = tables[CHECKPOINT_TABLE].to_pylist()
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise QualificationArtifactError("qualification checkpoint is malformed")
        return manifest, cast(dict[str, object], rows[0])
    raise QualificationArtifactError("qualification checkpoint is not completed")


def publish_qualification(
    cohort_root: str | Path,
    evidence: QualificationEvidence,
) -> Path:
    """Atomically publish one immutable explicit-capital qualification record."""

    root = Path(cohort_root).resolve()
    manifest, checkpoint = _checkpoint_lineage(root, evidence.checkpoint_id)
    request = evidence.decision.request
    if (
        manifest.get("candidate_id") != request.candidate_id
        or manifest.get("freeze_id") != request.freeze_id
        or checkpoint.get("information_end") != request.as_of
    ):
        raise QualificationArtifactError("qualification checkpoint lineage mismatch")

    payload = _payload(evidence)
    identity = evidence.qualification_id
    document = {"qualification_id": identity, **payload}
    parent = root / QUALIFICATION_DIRECTORY
    final = parent / identity
    staging = parent / f"{identity}.partial"
    if final.exists():
        existing = read_qualification(final)
        if existing != document:
            raise QualificationArtifactError("qualification identity collision")
        return final
    if staging.exists():
        raise QualificationArtifactError(
            "qualification partial generation already exists"
        )
    staging.mkdir(parents=True, exist_ok=False)
    try:
        target = staging / QUALIFICATION_FILE
        target.write_bytes(_canonical_bytes(document))
        integrity = build_integrity_record(
            staging,
            artifact_id=identity,
            file_names=(QUALIFICATION_FILE,),
        )
        (staging / INTEGRITY_FILE).write_text(
            integrity.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        read_qualification(staging)
        os.replace(staging, final)
        read_qualification(final)
    except BaseException:
        if staging.exists():
            for path in staging.iterdir():
                path.unlink(missing_ok=True)
            staging.rmdir()
        raise
    return final


def read_qualification(directory: str | Path) -> dict[str, object]:
    """Read and validate one immutable qualification evidence generation."""

    root = Path(directory).resolve()
    identity = _identity(
        root.name.removesuffix(".partial"),
        field="qualification_id",
    )
    try:
        read_and_validate_integrity(
            root,
            artifact_id=identity,
            required_files=QUALIFICATION_AUTHORITATIVE_FILES,
            allowed_files=QUALIFICATION_AUTHORITATIVE_FILES,
        )
    except ValueError as exc:
        raise QualificationArtifactError(str(exc)) from exc
    try:
        raw = json.loads((root / QUALIFICATION_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualificationArtifactError("qualification record is malformed") from exc
    if not isinstance(raw, dict):
        raise QualificationArtifactError("qualification record is malformed")
    document = cast(dict[str, object], raw)
    declared_identity = document.get("qualification_id")
    if not isinstance(declared_identity, str):
        raise QualificationArtifactError("qualification identity is missing")
    payload = dict(document)
    payload.pop("qualification_id")
    expected = sha256(_canonical_bytes(payload)).hexdigest()
    if declared_identity != identity or identity != expected:
        raise QualificationArtifactError("qualification identity mismatch")
    return document


def read_qualifications(cohort_root: str | Path) -> tuple[dict[str, object], ...]:
    """Read all completed qualification generations in deterministic order."""

    root = Path(cohort_root).resolve() / QUALIFICATION_DIRECTORY
    if not root.is_dir():
        return ()
    records = [
        read_qualification(path)
        for path in root.iterdir()
        if path.is_dir() and not path.name.endswith(".partial")
    ]
    return tuple(sorted(records, key=lambda item: str(item["qualification_id"])))


__all__ = [
    "QualificationArtifactError",
    "QualificationEvidence",
    "publish_qualification",
    "read_qualification",
    "read_qualifications",
]
