from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.qualification import (
    QualificationReason,
    QualificationRequest,
    QualificationState,
    qualify_candidate,
)

AS_OF = datetime(2026, 8, 18, tzinfo=UTC)


def _request(**overrides: object) -> QualificationRequest:
    payload: dict[str, object] = {
        "candidate_id": "a" * 64,
        "freeze_id": "b" * 64,
        "as_of": AS_OF,
        "requested_capital": Decimal("400"),
        "prospective_protocol_version": PROSPECTIVE_V1.protocol_id,
        "prospective_protocol_identity": prospective_protocol_identity(PROSPECTIVE_V1),
        "current_state_qap_run_id": "qap-current-state",
        "capture_snapshot_ids": ("c" * 64, "d" * 64),
        "market_metadata_fingerprint": "e" * 64,
        "eligibility_resolved": True,
        "capture_contract_satisfied": True,
        "current_two_way_trading": True,
        "order_constraints_satisfied": True,
        "candidate_capital_ceiling": Decimal("500"),
        "requested_capital_qap_run_id": "qap-requested",
        "requested_baseline_gate_passed": True,
        "requested_adverse_gate_passed": True,
        "lower_tested_capital": None,
        "lower_capital_qap_run_id": None,
        "lower_baseline_gate_passed": False,
        "lower_adverse_gate_passed": False,
    }
    payload.update(overrides)
    return QualificationRequest(**payload)  # type: ignore[arg-type]


def test_tradable_now_requires_requested_capital_qap_evidence() -> None:
    decision = qualify_candidate(_request())
    assert decision.state is QualificationState.TRADABLE_NOW
    assert decision.reason is QualificationReason.ALL_CURRENT_EVIDENCE_SATISFIED
    assert decision.request.requested_capital_qap_run_id == "qap-requested"


def test_small_capacity_requires_lower_capital_qap_evidence() -> None:
    decision = qualify_candidate(
        _request(
            requested_capital=Decimal("600"),
            requested_capital_qap_run_id=None,
            requested_baseline_gate_passed=False,
            requested_adverse_gate_passed=False,
            lower_tested_capital=Decimal("400"),
            lower_capital_qap_run_id="qap-lower",
            lower_baseline_gate_passed=True,
            lower_adverse_gate_passed=True,
        )
    )
    assert decision.state is QualificationState.SMALL_CAPACITY
    assert decision.reason is QualificationReason.REQUESTED_CAPITAL_ABOVE_CEILING
    assert decision.request.lower_capital_qap_run_id == "qap-lower"


def test_missing_capture_contract_is_research_only_even_with_positive_economics() -> (
    None
):
    decision = qualify_candidate(_request(capture_contract_satisfied=False))
    assert decision.state is QualificationState.RESEARCH_ONLY
    assert decision.reason is QualificationReason.MICROSTRUCTURE_COVERAGE_INSUFFICIENT


def test_positive_economic_gate_requires_qap_run_reference() -> None:
    with pytest.raises(ValueError, match="QAP run reference"):
        _request(requested_capital_qap_run_id=None)
