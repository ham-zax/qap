"""Compact exact experiment result records."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qap.experiment.manifest import DataRole, PrimaryMetric

_ZERO = Decimal("0")


class ResultStatus(StrEnum):
    """Economic classification against one predeclared threshold."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RoleSummary(_FrozenModel):
    """Terminal exact economics for one replay role."""

    role: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    terminal_value: Decimal
    unitized_terminal_value: Decimal
    terminal_quantities: dict[str, Decimal]
    fill_count: int = Field(ge=0)
    fees_value: Decimal
    slippage_value: Decimal
    turnover_value: Decimal
    external_flow_ids: tuple[str, ...] = ()

    @field_validator(
        "terminal_value",
        "unitized_terminal_value",
        "fees_value",
        "slippage_value",
        "turnover_value",
    )
    @classmethod
    def validate_non_negative_decimal(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value < _ZERO:
            raise ValueError("role financial values must be finite and non-negative")
        return value

    @field_validator("terminal_quantities")
    @classmethod
    def validate_quantities(
        cls,
        value: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        if any(
            not quantity.is_finite() or quantity <= _ZERO for quantity in value.values()
        ):
            raise ValueError("terminal quantities must be finite and strictly positive")
        return dict(sorted(value.items()))

    @field_validator("external_flow_ids")
    @classmethod
    def validate_flow_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not flow_id.strip() for flow_id in value):
            raise ValueError("external flow IDs must not be empty")
        if len(set(value)) != len(value):
            raise ValueError("external flow IDs must be unique")
        return value


class ExperimentResult(_FrozenModel):
    """One durable benchmark-ladder result with no promotion side effect."""

    schema_version: Literal["qap.experiment.result.v1"] = "qap.experiment.result.v1"
    run_id: str = Field(min_length=1)
    research_family_id: str = Field(min_length=1)
    parent_run_id: str | None = None
    data_role: DataRole
    final_oos_consumed: bool
    start_timestamp: datetime
    terminal_timestamp: datetime
    primary_metric: PrimaryMetric
    primary_metric_value: Decimal
    success_threshold: Decimal
    status: ResultStatus
    primary_incremental_benchmark: str | None = None
    strategy_vs_hodl: Decimal
    strategy_vs_matched_contribution: Decimal | None = None
    strategy_vs_primary_control: Decimal | None = None
    strategy_unitized_vs_hodl: Decimal
    maximum_relative_drawdown_vs_hodl: Decimal
    incremental_log_relative_to_hodl: tuple[Decimal, ...] | None = None
    roles: tuple[RoleSummary, ...]
    notes: tuple[str, ...] = ()

    @field_validator(
        "primary_metric_value",
        "success_threshold",
        "strategy_vs_hodl",
        "strategy_vs_matched_contribution",
        "strategy_vs_primary_control",
        "strategy_unitized_vs_hodl",
        mode="before",
    )
    @classmethod
    def validate_finite_optional_decimal(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, Decimal):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = Decimal(value.strip())
            except InvalidOperation as exc:
                raise ValueError(
                    "result financial values must be exact decimal strings"
                ) from exc
        else:
            raise TypeError(
                "result financial values must be Decimal or exact decimal strings"
            )
        if not parsed.is_finite():
            raise ValueError("result financial values must be finite")
        return parsed

    @field_validator("maximum_relative_drawdown_vs_hodl")
    @classmethod
    def validate_drawdown(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value < _ZERO:
            raise ValueError(
                "maximum relative drawdown must be finite and non-negative"
            )
        return value

    @field_validator("incremental_log_relative_to_hodl")
    @classmethod
    def validate_log_increments(
        cls,
        value: tuple[Decimal, ...] | None,
    ) -> tuple[Decimal, ...] | None:
        if value is not None and any(not item.is_finite() for item in value):
            raise ValueError("incremental log-relative values must be finite")
        return value

    @model_validator(mode="after")
    def validate_cross_fields(self) -> Self:
        if self.start_timestamp > self.terminal_timestamp:
            raise ValueError(
                "result start timestamp must not be after terminal timestamp"
            )
        names = tuple(role.role for role in self.roles)
        if len(set(names)) != len(names):
            raise ValueError("result role names must be unique")
        if "strategy" not in names or "hodl" not in names:
            raise ValueError("result must contain strategy and hodl roles")
        if self.data_role is DataRole.FINAL_OOS and not self.final_oos_consumed:
            raise ValueError(
                "completed final_oos result must mark the holdout consumed"
            )
        if self.data_role is not DataRole.FINAL_OOS and self.final_oos_consumed:
            raise ValueError("only final_oos results can consume a holdout")
        if (
            self.primary_metric
            is PrimaryMetric.PRIMARY_CONTROL_RELATIVE_TERMINAL_WEALTH
            and (
                self.primary_incremental_benchmark is None
                or self.strategy_vs_primary_control is None
            )
        ):
            raise ValueError("primary-control result requires its benchmark increment")
        if self.status is ResultStatus.POSITIVE and not (
            self.primary_metric_value > self.success_threshold
        ):
            raise ValueError("positive status requires metric above threshold")
        if self.status is ResultStatus.NEUTRAL and not (
            self.primary_metric_value == self.success_threshold
        ):
            raise ValueError("neutral status requires metric equal to threshold")
        if self.status is ResultStatus.NEGATIVE and not (
            self.primary_metric_value < self.success_threshold
        ):
            raise ValueError("negative status requires metric below threshold")
        return self

    def role(self, name: str) -> RoleSummary:
        for role in self.roles:
            if role.role == name:
                return role
        raise KeyError(name)


__all__ = ["ExperimentResult", "ResultStatus", "RoleSummary"]
