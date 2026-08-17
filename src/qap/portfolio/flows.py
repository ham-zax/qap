"""Explicit exogenous inventory changes admitted by deterministic replay."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType

from qap.portfolio._decimal import canonical_decimal
from qap.portfolio.assets import AssetId

_ZERO = Decimal("0")


def _validated_identifier(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("flow_id must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("flow_id must not be empty")
    return normalized


def _validated_utc(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("effective_time must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("effective_time must be timezone-aware UTC")
    return value.astimezone(UTC)


def _validated_asset(value: object) -> AssetId:
    if not isinstance(value, AssetId):
        raise TypeError("asset must be an AssetId")
    return value


def _validated_delta(value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError("quantity_delta must be Decimal")
    if not value.is_finite() or value == _ZERO:
        raise ValueError("quantity_delta must be finite and non-zero")
    return canonical_decimal(value)


@dataclass(frozen=True, slots=True)
class ExternalInventoryFlow:
    """One audited deposit or withdrawal without invented execution costs."""

    flow_id: str
    effective_time: datetime
    asset: AssetId
    quantity_delta: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "flow_id", _validated_identifier(self.flow_id))
        object.__setattr__(
            self,
            "effective_time",
            _validated_utc(self.effective_time),
        )
        object.__setattr__(self, "asset", _validated_asset(self.asset))
        object.__setattr__(
            self,
            "quantity_delta",
            _validated_delta(self.quantity_delta),
        )

    @property
    def event_id(self) -> str:
        return self.flow_id

    @property
    def balance_deltas(self) -> Mapping[AssetId, Decimal]:
        return MappingProxyType({self.asset: self.quantity_delta})
