"""Forward-only identity contracts for Scanner-V1 Slice 2."""

import json
import string
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.scanner.models import ScanInputIdentity
from qap.scanner.protocol import SCANNER_V1_SLICE1


@dataclass(frozen=True, slots=True)
class ProspectiveProtocol:
    protocol_id: str = "scanner-v1-s2"
    checkpoint_policy_version: str = "scanner-v1-prospective-checkpoints-v1"
    microstructure_policy_version: str = "scanner-v1-public-microstructure-v1"
    liquidity_policy_version: str = "scanner-v1-liquidity-evidence-v1"
    capacity_policy_version: str = "scanner-v1-conservative-capacity-v1"
    qualification_policy_version: str = "scanner-v1-qualification-v1"
    adverse_cost_reference: str = SCANNER_V1_SLICE1.cost_policy.policy_id


SLICE2_PROTOCOL = ProspectiveProtocol()


def _canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def prospective_protocol_identity(protocol: ProspectiveProtocol) -> str:
    if not isinstance(cast(object, protocol), ProspectiveProtocol):
        raise TypeError("protocol must be a ProspectiveProtocol")
    return sha256(_canonical_json(asdict(protocol))).hexdigest()


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _fingerprint(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(
        character not in string.hexdigits.lower() for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex fingerprint")
    return normalized


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class FrozenCandidateAttachment(_FrozenModel):
    candidate_id: str
    deep_replay_run_id: str
    slice1_economic_gate_status: str

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, value: str) -> str:
        return _fingerprint(value, field="candidate_id")

    @field_validator("deep_replay_run_id", "slice1_economic_gate_status")
    @classmethod
    def validate_text(cls, value: str, info: object) -> str:
        return _text(value, field=getattr(info, "field_name", "value"))


class ProspectiveCohort(_FrozenModel):
    schema_version: Literal["qap.scanner.prospective-cohort.v1"]
    slice2_protocol_version: str
    protocol_identity: str
    source_scan_id: str
    freeze_at: datetime
    candidates: tuple[FrozenCandidateAttachment, ...]
    created_at: datetime

    @field_validator("slice2_protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        return _text(value, field="slice2_protocol_version")

    @field_validator("protocol_identity", "source_scan_id")
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator("freeze_at", "created_at")
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @model_validator(mode="after")
    def validate_candidates(self) -> Self:
        if not self.candidates:
            raise ValueError("prospective cohort requires at least one candidate")
        copied = tuple(sorted(self.candidates, key=lambda item: item.candidate_id))
        ids = tuple(item.candidate_id for item in copied)
        if len(set(ids)) != len(ids):
            raise ValueError("prospective cohort candidate IDs must be unique")
        if any(
            item.slice1_economic_gate_status != "deep_replay_survivor"
            for item in copied
        ):
            raise ValueError(
                "prospective cohort accepts only Slice-1 deep_replay_survivor candidates"
            )
        if self.created_at < self.freeze_at:
            raise ValueError("created_at must be at or after freeze_at")
        object.__setattr__(self, "candidates", copied)
        return self

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(item.candidate_id for item in self.candidates)

    @property
    def cohort_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.prospective-cohort-identity.v1",
            "slice2_protocol_version": self.slice2_protocol_version,
            "protocol_identity": self.protocol_identity,
            "source_scan_id": self.source_scan_id,
            "freeze_at": self.freeze_at.isoformat(),
            "candidates": [
                {
                    "candidate_id": item.candidate_id,
                    "deep_replay_run_id": item.deep_replay_run_id,
                    "slice1_economic_gate_status": (
                        item.slice1_economic_gate_status
                    ),
                }
                for item in self.candidates
            ],
        }
        return sha256(_canonical_json(payload)).hexdigest()


class ProspectiveCheckpoint(_FrozenModel):
    schema_version: Literal["qap.scanner.prospective-checkpoint.v1"]
    cohort_id: str
    candidate_id: str
    checkpoint_index: int
    freeze_at: datetime
    evidence_window_start: datetime
    evidence_window_end: datetime
    information_end: datetime
    forward_slices: tuple[ScanInputIdentity, ...]
    evidence_role: Literal["prospective"]
    slice2_protocol_version: str
    protocol_identity: str
    created_at: datetime

    @field_validator("cohort_id", "candidate_id", "protocol_identity")
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator("slice2_protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        return _text(value, field="slice2_protocol_version")

    @field_validator(
        "freeze_at",
        "evidence_window_start",
        "evidence_window_end",
        "information_end",
        "created_at",
    )
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("checkpoint_index")
    @classmethod
    def validate_index(cls, value: int) -> int:
        if isinstance(cast(object, value), bool) or value < 1:
            raise ValueError("checkpoint_index must be a positive integer")
        return value

    @model_validator(mode="after")
    def validate_forward_window(self) -> Self:
        if self.evidence_window_start < self.freeze_at:
            raise ValueError("evidence_window_start must be at or after freeze_at")
        if self.evidence_window_end <= self.evidence_window_start:
            raise ValueError("evidence window must end after start")
        if self.information_end < self.evidence_window_end:
            raise ValueError("information_end must cover evidence_window_end")
        if self.created_at < self.information_end:
            raise ValueError("created_at must be at or after information_end")
        if not self.forward_slices:
            raise ValueError("forward_slices must not be empty")
        slices = tuple(
            sorted(
                self.forward_slices,
                key=lambda item: (
                    item.dataset_id,
                    item.source_artifact_fingerprint,
                    item.selection_slice_fingerprint,
                ),
            )
        )
        identities = tuple(
            (
                item.dataset_id,
                item.source_artifact_fingerprint,
                item.selection_slice_fingerprint,
            )
            for item in slices
        )
        if len(set(identities)) != len(identities):
            raise ValueError("forward_slices must be unique exact slice identities")
        object.__setattr__(self, "forward_slices", slices)
        return self

    @property
    def checkpoint_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.prospective-checkpoint-identity.v1",
            "cohort_id": self.cohort_id,
            "candidate_id": self.candidate_id,
            "checkpoint_index": self.checkpoint_index,
            "freeze_at": self.freeze_at.isoformat(),
            "evidence_window_start": self.evidence_window_start.isoformat(),
            "evidence_window_end": self.evidence_window_end.isoformat(),
            "information_end": self.information_end.isoformat(),
            "forward_slices": [
                item.model_dump(mode="json") for item in self.forward_slices
            ],
            "evidence_role": self.evidence_role,
            "slice2_protocol_version": self.slice2_protocol_version,
            "protocol_identity": self.protocol_identity,
        }
        return sha256(_canonical_json(payload)).hexdigest()


__all__ = [
    "FrozenCandidateAttachment",
    "ProspectiveCheckpoint",
    "ProspectiveCohort",
    "ProspectiveProtocol",
    "SLICE2_PROTOCOL",
    "prospective_protocol_identity",
]
