"""Explicit deterministic fee and slippage calculations."""

from dataclasses import dataclass
from decimal import Decimal

from qap.portfolio._decimal import (
    canonical_decimal,
    divide,
    exact_add,
    exact_multiply,
    exact_subtract,
)

_BASIS_POINT_DENOMINATOR = Decimal("10000")
_ONE = Decimal("1")
_ZERO = Decimal("0")


def _validated_bps(value: object, *, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite() or value < _ZERO:
        raise ValueError(f"{field} must be finite and non-negative")
    return canonical_decimal(value)


def _validated_reference_price(value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError("reference_price must be Decimal")
    if not value.is_finite() or value <= _ZERO:
        raise ValueError("reference_price must be positive finite")
    return canonical_decimal(value)


@dataclass(frozen=True, slots=True)
class CostModel:
    """Pure quote-fee and adverse-price slippage configuration."""

    fee_bps: Decimal
    slippage_bps: Decimal

    def __post_init__(self) -> None:
        fee_bps = _validated_bps(self.fee_bps, field="fee_bps")
        slippage_bps = _validated_bps(
            self.slippage_bps,
            field="slippage_bps",
        )
        if slippage_bps >= _BASIS_POINT_DENOMINATOR:
            raise ValueError("slippage_bps must be below 10000")
        object.__setattr__(self, "fee_bps", fee_bps)
        object.__setattr__(self, "slippage_bps", slippage_bps)

    @classmethod
    def zero(cls) -> "CostModel":
        """Return a model with no fee and no modeled slippage."""

        return cls(fee_bps=_ZERO, slippage_bps=_ZERO)

    @property
    def fee_rate(self) -> Decimal:
        return divide(self.fee_bps, _BASIS_POINT_DENOMINATOR)

    @property
    def slippage_rate(self) -> Decimal:
        return divide(self.slippage_bps, _BASIS_POINT_DENOMINATOR)

    def buy_execution_price(self, reference_price: Decimal) -> Decimal:
        """Apply adverse upward slippage to a buy reference price."""

        reference = _validated_reference_price(reference_price)
        return exact_multiply(reference, exact_add(_ONE, self.slippage_rate))

    def sell_execution_price(self, reference_price: Decimal) -> Decimal:
        """Apply adverse downward slippage to a sell reference price."""

        reference = _validated_reference_price(reference_price)
        return exact_multiply(reference, exact_subtract(_ONE, self.slippage_rate))
