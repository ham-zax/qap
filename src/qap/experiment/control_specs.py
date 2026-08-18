"""Frozen benchmark control manifest specifications."""

from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

_ZERO = Decimal("0")
_ONE = Decimal("1")


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("control financial values must be exact decimal strings")
    try:
        result = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(
            "control financial values must be exact decimal strings"
        ) from exc
    if not result.is_finite():
        raise ValueError("control financial values must be finite")
    return result


class _ControlSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    @field_validator("control_id", check_fields=False)
    @classmethod
    def validate_control_id(cls, value: str) -> str:
        if not value:
            raise ValueError("control_id must not be empty")
        return value


class PeriodicFixedWeightControlSpec(_ControlSpec):
    kind: Literal["periodic_fixed_weight"]
    control_id: str
    cadence_bars: PositiveInt


class BandPartialControlSpec(_ControlSpec):
    kind: Literal["band_partial"]
    control_id: str
    band_width: Decimal
    partial_correction_fraction: Decimal

    @field_validator("band_width", "partial_correction_fraction", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal:
        return _decimal(value)

    @model_validator(mode="after")
    def validate_parameters(self) -> Self:
        if not (_ZERO <= self.band_width < _ONE):
            raise ValueError("band_width must be in [0, 1)")
        if not (_ZERO < self.partial_correction_fraction <= _ONE):
            raise ValueError("partial_correction_fraction must be in (0, 1]")
        return self


class ContributionAwareBandControlSpec(_ControlSpec):
    kind: Literal["contribution_aware_band"]
    control_id: str
    band_width: Decimal
    partial_correction_fraction: Decimal

    @field_validator("band_width", "partial_correction_fraction", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal:
        return _decimal(value)

    @model_validator(mode="after")
    def validate_parameters(self) -> Self:
        if not (_ZERO <= self.band_width < _ONE):
            raise ValueError("band_width must be in [0, 1)")
        if not (_ZERO < self.partial_correction_fraction <= _ONE):
            raise ValueError("partial_correction_fraction must be in (0, 1]")
        return self


class PairBlindRelativeMomentumControlSpec(_ControlSpec):
    kind: Literal["pair_blind_relative_momentum"]
    control_id: str


ControlSpec = Annotated[
    PeriodicFixedWeightControlSpec
    | BandPartialControlSpec
    | ContributionAwareBandControlSpec
    | PairBlindRelativeMomentumControlSpec,
    Field(discriminator="kind"),
]


__all__ = [
    "BandPartialControlSpec",
    "ContributionAwareBandControlSpec",
    "ControlSpec",
    "PairBlindRelativeMomentumControlSpec",
    "PeriodicFixedWeightControlSpec",
]
