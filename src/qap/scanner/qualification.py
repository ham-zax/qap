"""Evidence-bound actionability qualification for scanner prospective candidates."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import cast

from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)

_ZERO = Decimal("0")


class QualificationState(StrEnum):
    RESEARCH_ONLY = "research_only"
    SMALL_CAPACITY = "small_capacity"
    TRADABLE_NOW = "tradable_now"


class QualificationReason(StrEnum):
    ALL_CURRENT_EVIDENCE_SATISFIED = "all_current_evidence_satisfied"
    ELIGIBILITY_UNRESOLVED = "eligibility_unresolved"
    MICROSTRUCTURE_COVERAGE_INSUFFICIENT = "microstructure_coverage_insufficient"
    INSTRUMENT_NOT_TWO_WAY_TRADABLE = "instrument_not_two_way_tradable"
    CAPACITY_UNKNOWN = "capacity_unknown"
    ORDER_CONSTRAINTS_UNSATISFIED = "order_constraints_unsatisfied"
    ECONOMIC_GATES_FAILED = "economic_gates_failed"
    REQUESTED_CAPITAL_ABOVE_CEILING = "requested_capital_above_ceiling"
    NO_SUPPORTED_LOWER_CAPITAL = "no_supported_lower_capital"


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be a Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError(f"{field} must be positive finite")
    return value


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _identity(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 fingerprint")
    return normalized


def _optional_run_id(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field} must be a non-empty string when present")
    return value.strip()


@dataclass(frozen=True, slots=True)
class QualificationRequest:
    candidate_id: str
    freeze_id: str
    as_of: datetime
    requested_capital: Decimal
    prospective_protocol_version: str
    prospective_protocol_identity: str
    capture_snapshot_ids: tuple[str, ...]
    market_metadata_fingerprint: str | None
    eligibility_resolved: bool
    capture_contract_satisfied: bool
    current_two_way_trading: bool
    order_constraints_satisfied: bool
    candidate_capital_ceiling: Decimal | None
    requested_capital_qap_run_id: str | None
    requested_baseline_gate_passed: bool
    requested_adverse_gate_passed: bool
    lower_tested_capital: Decimal | None = None
    lower_capital_qap_run_id: str | None = None
    lower_baseline_gate_passed: bool = False
    lower_adverse_gate_passed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "candidate_id", _identity(self.candidate_id, field="candidate_id")
        )
        object.__setattr__(
            self, "freeze_id", _identity(self.freeze_id, field="freeze_id")
        )
        object.__setattr__(self, "as_of", _utc(self.as_of, field="as_of"))
        object.__setattr__(
            self,
            "requested_capital",
            _positive_decimal(self.requested_capital, field="requested_capital"),
        )
        if self.prospective_protocol_version != PROSPECTIVE_V1.protocol_id or (
            self.prospective_protocol_identity
            != prospective_protocol_identity(PROSPECTIVE_V1)
        ):
            raise ValueError(
                "qualification prospective protocol does not match current authority"
            )
        object.__setattr__(
            self,
            "prospective_protocol_identity",
            _identity(
                self.prospective_protocol_identity,
                field="prospective_protocol_identity",
            ),
        )
        metadata_fingerprint = (
            None
            if self.market_metadata_fingerprint is None
            else _identity(
                self.market_metadata_fingerprint,
                field="market_metadata_fingerprint",
            )
        )
        object.__setattr__(
            self,
            "market_metadata_fingerprint",
            metadata_fingerprint,
        )
        snapshots = tuple(
            _identity(item, field="capture_snapshot_id")
            for item in self.capture_snapshot_ids
        )
        if len(set(snapshots)) != len(snapshots):
            raise ValueError("capture_snapshot_ids must be unique")
        if self.capture_contract_satisfied and (
            not snapshots or metadata_fingerprint is None
        ):
            raise ValueError(
                "satisfied capture contract requires snapshot and metadata evidence"
            )
        object.__setattr__(self, "capture_snapshot_ids", snapshots)
        ceiling = (
            None
            if self.candidate_capital_ceiling is None
            else _positive_decimal(
                self.candidate_capital_ceiling, field="candidate_capital_ceiling"
            )
        )
        lower = (
            None
            if self.lower_tested_capital is None
            else _positive_decimal(
                self.lower_tested_capital, field="lower_tested_capital"
            )
        )
        object.__setattr__(self, "candidate_capital_ceiling", ceiling)
        object.__setattr__(self, "lower_tested_capital", lower)
        object.__setattr__(
            self,
            "requested_capital_qap_run_id",
            _optional_run_id(
                self.requested_capital_qap_run_id,
                field="requested_capital_qap_run_id",
            ),
        )
        object.__setattr__(
            self,
            "lower_capital_qap_run_id",
            _optional_run_id(
                self.lower_capital_qap_run_id,
                field="lower_capital_qap_run_id",
            ),
        )
        for field in (
            "eligibility_resolved",
            "capture_contract_satisfied",
            "current_two_way_trading",
            "order_constraints_satisfied",
            "requested_baseline_gate_passed",
            "requested_adverse_gate_passed",
            "lower_baseline_gate_passed",
            "lower_adverse_gate_passed",
        ):
            if not isinstance(cast(object, getattr(self, field)), bool):
                raise TypeError(f"{field} must be a boolean")
        if (
            self.requested_baseline_gate_passed or self.requested_adverse_gate_passed
        ) and self.requested_capital_qap_run_id is None:
            raise ValueError(
                "requested-capital economic gates require a QAP run reference"
            )
        if (self.lower_baseline_gate_passed or self.lower_adverse_gate_passed) and (
            lower is None or self.lower_capital_qap_run_id is None
        ):
            raise ValueError(
                "lower-capital economic gates require capital and QAP run reference"
            )

    @property
    def requested_economic_gates_passed(self) -> bool:
        return (
            self.requested_baseline_gate_passed and self.requested_adverse_gate_passed
        )

    @property
    def lower_economic_gates_passed(self) -> bool:
        return self.lower_baseline_gate_passed and self.lower_adverse_gate_passed


@dataclass(frozen=True, slots=True)
class QualificationDecision:
    state: QualificationState
    reason: QualificationReason
    request: QualificationRequest

    @property
    def as_of(self) -> datetime:
        return self.request.as_of

    @property
    def requested_capital(self) -> Decimal:
        return self.request.requested_capital

    @property
    def estimated_capital_ceiling(self) -> Decimal | None:
        return self.request.candidate_capital_ceiling

    @property
    def liquidity_policy_version(self) -> str:
        return PROSPECTIVE_V1.liquidity_policy_version


def _decision(
    request: QualificationRequest,
    state: QualificationState,
    reason: QualificationReason,
) -> QualificationDecision:
    return QualificationDecision(state=state, reason=reason, request=request)


def qualify_candidate(request: QualificationRequest) -> QualificationDecision:
    """Classify one immutable prospective qualification request."""

    if not isinstance(cast(object, request), QualificationRequest):
        raise TypeError("request must be a QualificationRequest")
    ceiling = request.candidate_capital_ceiling
    if not request.eligibility_resolved:
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ELIGIBILITY_UNRESOLVED,
        )
    if not request.capture_contract_satisfied:
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.MICROSTRUCTURE_COVERAGE_INSUFFICIENT,
        )
    if not request.current_two_way_trading:
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.INSTRUMENT_NOT_TWO_WAY_TRADABLE,
        )
    if ceiling is None:
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.CAPACITY_UNKNOWN,
        )
    if not request.order_constraints_satisfied:
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ORDER_CONSTRAINTS_UNSATISFIED,
        )
    if request.requested_capital <= ceiling:
        if request.requested_economic_gates_passed:
            return _decision(
                request,
                QualificationState.TRADABLE_NOW,
                QualificationReason.ALL_CURRENT_EVIDENCE_SATISFIED,
            )
        return _decision(
            request,
            QualificationState.RESEARCH_ONLY,
            QualificationReason.ECONOMIC_GATES_FAILED,
        )
    lower = request.lower_tested_capital
    if lower is not None and lower <= ceiling and request.lower_economic_gates_passed:
        return _decision(
            request,
            QualificationState.SMALL_CAPACITY,
            QualificationReason.REQUESTED_CAPITAL_ABOVE_CEILING,
        )
    return _decision(
        request,
        QualificationState.RESEARCH_ONLY,
        QualificationReason.NO_SUPPORTED_LOWER_CAPITAL,
    )


__all__ = [
    "QualificationDecision",
    "QualificationReason",
    "QualificationRequest",
    "QualificationState",
    "qualify_candidate",
]
