"""Declared, bounded Pair Rotation Lab research settings."""

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SignalMethod = Literal["zscore", "lead_lag", "copula", "trend"]


class LabSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    method: SignalMethod = "zscore"
    auto_tune: bool = True
    lookback: int = Field(default=96, ge=20, le=10000)
    entry: float = Field(default=2.0, gt=0, le=10)
    exit: float = Field(default=0.5, ge=0, le=5)
    hedge_method: Literal["ratio", "ols", "tls", "kalman"] = "ratio"
    starting_value: Decimal = Field(default=Decimal("10000"), gt=0, le=100000000)
    initial_weight: Decimal = Field(default=Decimal("0.5"), gt=0, lt=1)
    rotation_size: Decimal = Field(default=Decimal("0.5"), gt=0, le=Decimal("0.5"))
    minimum_hold: int = Field(default=4, ge=0, le=10000)
    cooldown: int = Field(default=4, ge=0, le=10000)
    fee_bps: Decimal = Field(default=Decimal("10"), gt=0, le=100)
    slippage_bps: Decimal = Field(default=Decimal("5"), gt=0, le=1000)
    volume_impact_bps: Decimal = Field(default=Decimal("10"), ge=0, le=1000)
    minimum_notional: Decimal = Field(default=Decimal("1"), ge=0, le=100000)
    cost_budget_multiple: Decimal = Field(default=Decimal("2"), ge=0, le=100)
    anchor_threshold: float = Field(default=0.002, gt=0, le=0.5)
    copula_probability: float = Field(default=0.05, gt=0, lt=0.5)
    copula_exit_band: float = Field(default=0.15, gt=0.0, lt=0.45)
    trend_deadband: float = Field(default=0.002, ge=0.0, le=0.5)
    crash_defense_mode: Literal["coins_only", "park_anchor", "park_usdt"] = "coins_only"
    regime_break_drawdown: float = Field(default=0.15, ge=0.02, le=0.80)
    fast_window: int = Field(default=12, ge=2, le=1000)
    slow_window: int = Field(default=48, ge=3, le=10000)
    proof_fraction: float = Field(default=0.3, ge=0.2, le=0.5)
    folds: int = Field(default=8, ge=3, le=12)
    minimum_passing_folds: int = Field(default=5, ge=1, le=12)
    minimum_trades: int = Field(default=10, ge=1, le=1000)
    significance: float = Field(default=0.05, gt=0, le=0.1)

    @model_validator(mode="after")
    def validate_relationships(self) -> Self:
        if self.exit >= self.entry:
            raise ValueError("Exit threshold must be smaller than entry threshold.")
        if self.fast_window >= self.slow_window:
            raise ValueError("Fast window must be shorter than slow window.")
        if self.minimum_passing_folds > self.folds:
            raise ValueError("Passing folds cannot exceed total folds.")
        if self.copula_probability >= 0.5 - self.copula_exit_band:
            raise ValueError(
                "Copula entry probability must sit outside the exit neutral band."
            )
        if (
            self.initial_weight - self.rotation_size < 0
            or self.initial_weight + self.rotation_size > 1
        ):
            raise ValueError(
                "Rotation size cannot move a target outside owned spot weights."
            )
        return self
