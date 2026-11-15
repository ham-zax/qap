"""HTTP DTOs for durable local operations and their bounded commands."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import Field, JsonValue, field_validator

from qap.api.schemas import ApiDto, ErrorDetailDto


class ScannerPinRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    asset_a: str
    asset_b: str
    horizons: tuple[Literal["short", "medium", "swing"], ...] = Field(min_length=1)
    forensic: bool = False


class RunScanRequestDto(ApiDto):
    as_of: datetime
    horizons: tuple[Literal["short", "medium", "swing"], ...] = Field(min_length=1)
    pins: tuple[ScannerPinRequestDto, ...] = ()
    manual_replay_candidate_ids: tuple[str, ...] = ()


class MomentumGenerationRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    horizon: Literal["short", "medium", "swing"]


class FreezeForwardCohortRequestDto(ApiDto):
    scan_id: str
    horizon: Literal["short", "medium", "swing"]
    freeze_at: datetime


class AdvanceForwardCohortRequestDto(ApiDto):
    through: datetime


class CapturePublicEvidenceRequestDto(ApiDto):
    venue: Literal["binance", "gate"]
    venue_symbol: str
    base_asset: str
    quote_asset: str
    kind: Literal["l1", "depth", "metadata"]


class QualificationRequestDto(ApiDto):
    cohort_id: str
    checkpoint_id: str
    as_of: datetime
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


class OperationRefDto(ApiDto):
    schema_version: Literal["qap.api.operation_ref.v1"] = "qap.api.operation_ref.v1"
    operation_id: str
    status: Literal["running"] = "running"


class OperationDto(ApiDto):
    schema_version: Literal["qap.api.operation.v1"] = "qap.api.operation.v1"
    operation_id: str
    kind: str
    status: Literal["running", "completed", "failed", "interrupted"]
    requested_at: datetime
    started_at: datetime
    finished_at: datetime | None
    request_summary: dict[str, JsonValue]
    result: dict[str, JsonValue] | None
    failure: ErrorDetailDto | None
    progress: dict[str, JsonValue] | None = None


class OperationListDto(ApiDto):
    schema_version: Literal["qap.api.operation_list.v1"] = "qap.api.operation_list.v1"
    items: tuple[OperationDto, ...]


__all__ = [
    "AdvanceForwardCohortRequestDto",
    "CapturePublicEvidenceRequestDto",
    "FreezeForwardCohortRequestDto",
    "MomentumGenerationRequestDto",
    "OperationDto",
    "OperationListDto",
    "OperationRefDto",
    "QualificationRequestDto",
    "RunScanRequestDto",
    "ScannerPinRequestDto",
]
