"""Forward-only identity contracts for Scanner-V1 Slice 2."""

import json
import string
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    ProspectiveProtocol,
    prospective_protocol_identity,
)
from qap.scanner.protocol import ScannerHorizon


def _canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


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


class CandidateFreeze(_FrozenModel):
    """One immutable candidate rule frozen before prospective outcomes exist."""

    schema_version: Literal["qap.scanner.candidate-freeze.v1"] = (
        "qap.scanner.candidate-freeze.v1"
    )
    candidate_id: str
    scan_id: str
    scanner_protocol_version: str
    scanner_protocol_identity: str
    prospective_protocol_version: str
    prospective_protocol_identity: str
    automatic_selected: bool
    manual_selected: bool
    frozen_at: datetime
    eligible_information_end: datetime
    forward_start: datetime
    forward_end: datetime
    horizon: ScannerHorizon
    venue: str
    pair_id: str
    orientation: str
    resolution: str
    model_family: str
    template_id: str
    model_parameters: tuple[tuple[str, str], ...]
    source_artifact_fingerprints: tuple[str, ...]
    selection_slice_fingerprints: tuple[str, ...]
    universe_snapshot_id: str
    cost_policy_reference: str
    primary_control_reference: str
    candidate_deep_replay_run_id: str
    candidate_deep_replay_gate_status: Literal["deep_replay_survivor"]

    @field_validator(
        "candidate_id",
        "scan_id",
        "scanner_protocol_identity",
        "prospective_protocol_identity",
        "universe_snapshot_id",
    )
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator(
        "scanner_protocol_version",
        "prospective_protocol_version",
        "venue",
        "pair_id",
        "orientation",
        "resolution",
        "model_family",
        "template_id",
        "cost_policy_reference",
        "primary_control_reference",
        "candidate_deep_replay_run_id",
    )
    @classmethod
    def validate_text(cls, value: str, info: object) -> str:
        return _text(value, field=getattr(info, "field_name", "value"))

    @field_validator(
        "frozen_at",
        "eligible_information_end",
        "forward_start",
        "forward_end",
    )
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("source_artifact_fingerprints", "selection_slice_fingerprints")
    @classmethod
    def validate_fingerprints(
        cls, values: tuple[str, ...], info: object
    ) -> tuple[str, ...]:
        field = getattr(info, "field_name", "fingerprints")
        if not values:
            raise ValueError(f"{field} must not be empty")
        normalized = tuple(_fingerprint(value, field=field) for value in values)
        if len(set(normalized)) != len(normalized):
            raise ValueError(f"{field} must be unique")
        return normalized

    @field_validator("model_parameters")
    @classmethod
    def validate_model_parameters(
        cls, values: tuple[tuple[str, str], ...]
    ) -> tuple[tuple[str, str], ...]:
        normalized = tuple(
            sorted(
                (
                    _text(key, field="model parameter key"),
                    _text(value, field="model parameter value"),
                )
                for key, value in values
            )
        )
        if len({key for key, _value in normalized}) != len(normalized):
            raise ValueError("model parameter keys must be unique")
        return normalized

    @model_validator(mode="after")
    def validate_freeze(self) -> Self:
        if not self.automatic_selected and not self.manual_selected:
            raise ValueError(
                "candidate freeze must preserve automatic or manual selection"
            )
        if len(self.source_artifact_fingerprints) != len(
            self.selection_slice_fingerprints
        ):
            raise ValueError("source and selection fingerprint counts must match")
        if self.eligible_information_end > self.frozen_at:
            raise ValueError("eligible_information_end must not exceed frozen_at")
        if self.forward_start <= self.frozen_at:
            raise ValueError("forward_start must be strictly after frozen_at")
        expected_end = self.forward_start + PROSPECTIVE_V1.forward_window(self.horizon)
        if self.forward_end != expected_end:
            raise ValueError("forward_end must equal the frozen horizon window")
        return self

    @property
    def semantic_rule_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.prospective-rule.v1",
            "scanner_protocol_version": self.scanner_protocol_version,
            "scanner_protocol_identity": self.scanner_protocol_identity,
            "prospective_protocol_version": self.prospective_protocol_version,
            "prospective_protocol_identity": self.prospective_protocol_identity,
            "venue": self.venue,
            "pair_id": self.pair_id,
            "orientation": self.orientation,
            "horizon": self.horizon.value,
            "resolution": self.resolution,
            "model_family": self.model_family,
            "template_id": self.template_id,
            "model_parameters": list(self.model_parameters),
            "cost_policy_reference": self.cost_policy_reference,
            "primary_control_reference": self.primary_control_reference,
        }
        return sha256(_canonical_json(payload)).hexdigest()

    @property
    def freeze_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.candidate-freeze-identity.v1",
            "candidate_id": self.candidate_id,
            "scan_id": self.scan_id,
            "semantic_rule_id": self.semantic_rule_id,
            "automatic_selected": self.automatic_selected,
            "manual_selected": self.manual_selected,
            "frozen_at": self.frozen_at.isoformat(),
            "eligible_information_end": self.eligible_information_end.isoformat(),
            "forward_start": self.forward_start.isoformat(),
            "forward_end": self.forward_end.isoformat(),
            "source_artifact_fingerprints": list(self.source_artifact_fingerprints),
            "selection_slice_fingerprints": list(self.selection_slice_fingerprints),
            "universe_snapshot_id": self.universe_snapshot_id,
            "candidate_deep_replay_run_id": self.candidate_deep_replay_run_id,
            "candidate_deep_replay_gate_status": (
                self.candidate_deep_replay_gate_status
            ),
        }
        return sha256(_canonical_json(payload)).hexdigest()


class ReselectionRecord(_FrozenModel):
    active_freeze_id: str
    candidate_id: str
    source_scan_id: str
    automatic_selected: bool
    manual_selected: bool
    reselected_at: datetime

    @field_validator("active_freeze_id", "candidate_id", "source_scan_id")
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator("reselected_at")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return _utc(value, field="reselected_at")

    @model_validator(mode="after")
    def validate_selection(self) -> Self:
        if not self.automatic_selected and not self.manual_selected:
            raise ValueError("reselection must preserve automatic or manual selection")
        return self


class ForwardCohort(_FrozenModel):
    schema_version: Literal["qap.scanner.forward-cohort.v1"] = (
        "qap.scanner.forward-cohort.v1"
    )
    prospective_protocol_version: str
    prospective_protocol_identity: str
    source_scan_id: str
    horizon: ScannerHorizon
    freeze_at: datetime
    candidate_freezes: tuple[CandidateFreeze, ...] = ()
    reselections: tuple[ReselectionRecord, ...] = ()
    automatic_member_count: int = 0
    manual_member_count: int = 0
    created_at: datetime

    @field_validator("prospective_protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        return _text(value, field="prospective_protocol_version")

    @field_validator("prospective_protocol_identity", "source_scan_id")
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator("freeze_at", "created_at")
    @classmethod
    def validate_timestamp(cls, value: datetime, info: object) -> datetime:
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("automatic_member_count", "manual_member_count")
    @classmethod
    def validate_count(cls, value: int, info: object) -> int:
        if isinstance(cast(object, value), bool) or value < 0:
            raise ValueError(
                f"{getattr(info, 'field_name', 'count')} must be non-negative"
            )
        return value

    @model_validator(mode="after")
    def validate_cohort(self) -> Self:
        freezes = tuple(sorted(self.candidate_freezes, key=lambda item: item.freeze_id))
        reselections = tuple(
            sorted(self.reselections, key=lambda item: item.active_freeze_id)
        )
        freeze_ids = tuple(item.freeze_id for item in freezes)
        if len(set(freeze_ids)) != len(freeze_ids):
            raise ValueError("candidate freeze IDs must be unique")
        reselected_ids = tuple(item.active_freeze_id for item in reselections)
        if len(set(reselected_ids)) != len(reselected_ids):
            raise ValueError("reselected active freeze IDs must be unique")
        if set(freeze_ids) & set(reselected_ids):
            raise ValueError("new and reselected freeze IDs must be disjoint")
        for freeze in freezes:
            if freeze.scan_id != self.source_scan_id:
                raise ValueError("candidate freeze source scan mismatch")
            if freeze.horizon is not self.horizon:
                raise ValueError("candidate freeze horizon mismatch")
            if freeze.frozen_at > self.freeze_at:
                raise ValueError("candidate freeze cannot occur after cohort freeze")
        for reselection in reselections:
            if reselection.source_scan_id != self.source_scan_id:
                raise ValueError("reselection source scan mismatch")
            if reselection.reselected_at != self.freeze_at:
                raise ValueError("reselection timestamp must equal cohort freeze")
        expected_automatic = sum(item.automatic_selected for item in freezes) + sum(
            item.automatic_selected for item in reselections
        )
        expected_manual = sum(item.manual_selected for item in freezes) + sum(
            item.manual_selected for item in reselections
        )
        if self.automatic_member_count != expected_automatic:
            raise ValueError("automatic_member_count does not reconcile")
        if self.manual_member_count != expected_manual:
            raise ValueError("manual_member_count does not reconcile")
        if self.created_at < self.freeze_at:
            raise ValueError("created_at must be at or after freeze_at")
        object.__setattr__(self, "candidate_freezes", freezes)
        object.__setattr__(self, "reselections", reselections)
        return self

    @property
    def candidate_freeze_ids(self) -> tuple[str, ...]:
        return tuple(item.freeze_id for item in self.candidate_freezes)

    @property
    def reselected_active_freeze_ids(self) -> tuple[str, ...]:
        return tuple(item.active_freeze_id for item in self.reselections)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                [item.candidate_id for item in self.candidate_freezes]
                + [item.candidate_id for item in self.reselections]
            )
        )

    @property
    def cohort_id(self) -> str:
        payload = {
            "identity_version": "qap.scanner.forward-cohort-identity.v1",
            "prospective_protocol_version": self.prospective_protocol_version,
            "prospective_protocol_identity": self.prospective_protocol_identity,
            "source_scan_id": self.source_scan_id,
            "horizon": self.horizon.value,
            "freeze_at": self.freeze_at.isoformat(),
            "candidate_freeze_ids": list(self.candidate_freeze_ids),
            "reselections": [
                item.model_dump(mode="json") for item in self.reselections
            ],
            "automatic_member_count": self.automatic_member_count,
            "manual_member_count": self.manual_member_count,
        }
        return sha256(_canonical_json(payload)).hexdigest()


def enroll_forward_cohort(
    *,
    source_scan_id: str,
    horizon: ScannerHorizon,
    freeze_at: datetime,
    selected_freezes: tuple[CandidateFreeze, ...],
    active_freezes: tuple[CandidateFreeze, ...] = (),
    protocol: ProspectiveProtocol = PROSPECTIVE_V1,
    created_at: datetime | None = None,
) -> ForwardCohort:
    """Enroll selections while deduplicating only active identical semantic rules."""

    source_scan = _fingerprint(source_scan_id, field="source_scan_id")
    frozen_at = _utc(freeze_at, field="freeze_at")
    protocol_identity = prospective_protocol_identity(protocol)
    if not isinstance(cast(object, horizon), ScannerHorizon):
        raise TypeError("horizon must be a ScannerHorizon")
    active_by_rule: dict[str, CandidateFreeze] = {}
    for active in active_freezes:
        if active.horizon is not horizon or active.forward_end <= frozen_at:
            continue
        if active.semantic_rule_id in active_by_rule:
            raise ValueError("multiple active freezes share one semantic rule")
        active_by_rule[active.semantic_rule_id] = active

    new_freezes: list[CandidateFreeze] = []
    reselections: list[ReselectionRecord] = []
    selected_ids: set[str] = set()
    for selected in sorted(selected_freezes, key=lambda item: item.candidate_id):
        if selected.candidate_id in selected_ids:
            raise ValueError("selected candidate IDs must be unique")
        selected_ids.add(selected.candidate_id)
        if selected.scan_id != source_scan:
            raise ValueError("selected freeze source scan mismatch")
        if selected.prospective_protocol_version != protocol.protocol_id:
            raise ValueError("selected freeze prospective protocol version mismatch")
        if selected.prospective_protocol_identity != protocol_identity:
            raise ValueError("selected freeze prospective protocol identity mismatch")
        if selected.cost_policy_reference != protocol.adverse_cost_reference:
            raise ValueError("selected freeze cost policy mismatch")
        if selected.primary_control_reference != protocol.primary_control_reference:
            raise ValueError("selected freeze primary control mismatch")
        if selected.horizon is not horizon:
            raise ValueError("selected freeze horizon mismatch")
        if selected.frozen_at > frozen_at:
            raise ValueError("selected freeze cannot occur after cohort freeze")
        active = active_by_rule.get(selected.semantic_rule_id)
        if active is None:
            new_freezes.append(selected)
            continue
        reselections.append(
            ReselectionRecord(
                active_freeze_id=active.freeze_id,
                candidate_id=selected.candidate_id,
                source_scan_id=source_scan,
                automatic_selected=selected.automatic_selected,
                manual_selected=selected.manual_selected,
                reselected_at=frozen_at,
            )
        )

    automatic_count = sum(item.automatic_selected for item in selected_freezes)
    manual_count = sum(item.manual_selected for item in selected_freezes)
    return ForwardCohort(
        prospective_protocol_version=protocol.protocol_id,
        prospective_protocol_identity=protocol_identity,
        source_scan_id=source_scan,
        horizon=horizon,
        freeze_at=frozen_at,
        candidate_freezes=tuple(new_freezes),
        reselections=tuple(reselections),
        automatic_member_count=automatic_count,
        manual_member_count=manual_count,
        created_at=(
            frozen_at if created_at is None else _utc(created_at, field="created_at")
        ),
    )


class ForwardCheckpoint(_FrozenModel):
    schema_version: Literal["qap.scanner.forward-checkpoint.v1"] = (
        "qap.scanner.forward-checkpoint.v1"
    )
    cohort_id: str
    candidate_id: str
    freeze_id: str
    checkpoint_index: int
    freeze_at: datetime
    eligible_information_end: datetime
    forward_start: datetime
    first_outcome_complete_at: datetime
    evidence_window_start: datetime
    evidence_window_end: datetime
    information_end: datetime
    forward_slices: tuple[ScanInputIdentity, ...]
    evidence_role: Literal["prospective"]
    prospective_protocol_version: str
    prospective_protocol_identity: str
    created_at: datetime

    @field_validator(
        "cohort_id", "candidate_id", "freeze_id", "prospective_protocol_identity"
    )
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator("prospective_protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        return _text(value, field="prospective_protocol_version")

    @field_validator(
        "freeze_at",
        "eligible_information_end",
        "forward_start",
        "first_outcome_complete_at",
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
        if self.eligible_information_end > self.freeze_at:
            raise ValueError("eligible_information_end must not exceed freeze_at")
        if self.forward_start <= self.freeze_at:
            raise ValueError("forward_start must be strictly after freeze_at")
        if self.first_outcome_complete_at <= self.forward_start:
            raise ValueError(
                "first_outcome_complete_at must be strictly after forward_start"
            )
        if self.evidence_window_start != self.forward_start:
            raise ValueError("evidence_window_start must equal forward_start")
        if self.evidence_window_end <= self.evidence_window_start:
            raise ValueError("evidence window must end after start")
        if self.first_outcome_complete_at > self.evidence_window_end:
            raise ValueError("first outcome must fall within evidence window")
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
            "identity_version": "qap.scanner.forward-checkpoint-identity.v1",
            "cohort_id": self.cohort_id,
            "candidate_id": self.candidate_id,
            "freeze_id": self.freeze_id,
            "checkpoint_index": self.checkpoint_index,
            "freeze_at": self.freeze_at.isoformat(),
            "eligible_information_end": self.eligible_information_end.isoformat(),
            "forward_start": self.forward_start.isoformat(),
            "first_outcome_complete_at": self.first_outcome_complete_at.isoformat(),
            "evidence_window_start": self.evidence_window_start.isoformat(),
            "evidence_window_end": self.evidence_window_end.isoformat(),
            "information_end": self.information_end.isoformat(),
            "forward_slices": [
                item.model_dump(mode="json") for item in self.forward_slices
            ],
            "evidence_role": self.evidence_role,
            "prospective_protocol_version": self.prospective_protocol_version,
            "prospective_protocol_identity": self.prospective_protocol_identity,
        }
        return sha256(_canonical_json(payload)).hexdigest()


class ForwardOutcomeStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    MATURED = "matured"
    INVALID = "invalid"


class ForwardOutcome(_FrozenModel):
    schema_version: Literal["qap.scanner.forward-outcome.v1"] = (
        "qap.scanner.forward-outcome.v1"
    )
    freeze_id: str
    candidate_id: str
    checkpoint_id: str
    prospective_protocol_version: str
    prospective_protocol_identity: str
    status: ForwardOutcomeStatus
    through: datetime
    matured_at: datetime | None = None
    qap_run_id: str | None = None
    primary_control_reference: str
    cost_policy_reference: str
    strategy_vs_hodl: Decimal | None = None
    strategy_vs_primary_control: Decimal | None = None
    baseline_economic_gates_passed: bool | None = None
    adverse_economic_gates_passed: bool | None = None
    failure_reason: str | None = None

    @field_validator(
        "freeze_id",
        "candidate_id",
        "checkpoint_id",
        "prospective_protocol_identity",
    )
    @classmethod
    def validate_outcome_fingerprint(cls, value: str, info: object) -> str:
        return _fingerprint(value, field=getattr(info, "field_name", "fingerprint"))

    @field_validator(
        "prospective_protocol_version",
        "primary_control_reference",
        "cost_policy_reference",
    )
    @classmethod
    def validate_outcome_text(cls, value: str, info: object) -> str:
        return _text(value, field=getattr(info, "field_name", "text"))

    @field_validator("through", "matured_at")
    @classmethod
    def validate_outcome_time(
        cls,
        value: datetime | None,
        info: object,
    ) -> datetime | None:
        if value is None:
            return None
        return _utc(value, field=getattr(info, "field_name", "timestamp"))

    @field_validator("strategy_vs_hodl", "strategy_vs_primary_control")
    @classmethod
    def validate_outcome_decimal(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not value.is_finite():
            raise ValueError("forward outcome financial values must be finite")
        return value

    @model_validator(mode="after")
    def validate_outcome_state(self) -> Self:
        has_economics = self.status in {
            ForwardOutcomeStatus.PARTIAL,
            ForwardOutcomeStatus.MATURED,
        }
        if has_economics and (
            self.qap_run_id is None
            or self.strategy_vs_hodl is None
            or self.strategy_vs_primary_control is None
            or self.baseline_economic_gates_passed is None
            or self.adverse_economic_gates_passed is None
        ):
            raise ValueError(
                "observed forward outcome requires authoritative QAP economics"
            )
        if self.status is ForwardOutcomeStatus.MATURED and self.matured_at is None:
            raise ValueError("matured forward outcome requires matured_at")
        if (
            self.status is not ForwardOutcomeStatus.MATURED
            and self.matured_at is not None
        ):
            raise ValueError("only matured forward outcome may set matured_at")
        if self.status is ForwardOutcomeStatus.INVALID and not self.failure_reason:
            raise ValueError("invalid forward outcome requires failure_reason")
        if self.status is ForwardOutcomeStatus.PENDING and self.qap_run_id is not None:
            raise ValueError("pending forward outcome cannot have a QAP run")
        return self

    @property
    def outcome_id(self) -> str:
        payload = self.model_dump(mode="json")
        payload["identity_version"] = "qap.scanner.forward-outcome-identity.v1"
        return sha256(_canonical_json(payload)).hexdigest()


__all__ = [
    "CandidateFreeze",
    "ForwardCheckpoint",
    "ForwardCohort",
    "ForwardOutcome",
    "ForwardOutcomeStatus",
    "ReselectionRecord",
    "enroll_forward_cohort",
]
