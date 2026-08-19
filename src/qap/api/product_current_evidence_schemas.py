"""HTTP contracts for Product current public-evidence collection."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import field_validator

from qap.api.scanner_schemas import CaptureReadinessDto, QualificationRequestDto
from qap.api.schemas import ApiDto


class CurrentEvidenceSlotCountsDto(ApiDto):
    scheduled: int
    captured: int
    missed: int


class ResearchIdeaCurrentEvidenceDto(ApiDto):
    schema_version: Literal["qap.api.product_current_evidence.v1"] = (
        "qap.api.product_current_evidence.v1"
    )
    state: Literal[
        "not_collecting",
        "collecting",
        "coverage_incomplete",
        "contract_ready",
        "evidence_unavailable",
    ]
    collector_status: Literal["not_running", "running", "failed"]
    collector_failure_reason: str | None
    plan_id: str | None
    collecting_since: datetime | None
    active_cohort_id: str | None
    active_freeze_id: str | None
    venue: Literal["binance", "gate"] | None
    venue_symbol: str | None
    latest_observation: datetime | None
    l1_slots: CurrentEvidenceSlotCountsDto
    depth_slots: CurrentEvidenceSlotCountsDto
    readiness_as_of: datetime | None
    readiness: CaptureReadinessDto | None
    assessment_blocker: str | None


class ProductAmountAssessmentRequestDto(ApiDto):
    requested_capital: str

    @field_validator("requested_capital")
    @classmethod
    def validate_capital(cls, value: str) -> str:
        try:
            parsed = Decimal(value.strip())
        except InvalidOperation as exc:
            raise ValueError(
                "requested_capital must be an exact decimal string"
            ) from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ValueError("requested_capital must be positive finite")
        return format(parsed, "f")


class ProductQualificationWorkerRequestDto(QualificationRequestDto):
    evidence_source: Literal["product_collector"]
    active_freeze_id: str


__all__ = [
    "CurrentEvidenceSlotCountsDto",
    "ProductAmountAssessmentRequestDto",
    "ProductQualificationWorkerRequestDto",
    "ResearchIdeaCurrentEvidenceDto",
]
