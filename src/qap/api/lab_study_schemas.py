"""Complete Lab study contract, independent of presentation-derived decisions."""

from datetime import datetime
from typing import Literal, Self

from pydantic import Field, JsonValue, model_validator

from qap.api.pair_rotation_analysis_schemas import (
    AnalysisDays,
    AnalysisModel,
    LabAnalysisDto,
    LabCoinDto,
)
from qap.api.pair_rotation_schemas import PairRotationRequestDto
from qap.policy.lab_settings import LabSettings


class LabStudyRequestDto(AnalysisModel):
    coin_a: str
    coin_b: str
    anchor: str | None = None
    bar: Literal["1m", "15m", "1h", "4h", "1d"] = "15m"
    days: AnalysisDays = AnalysisDays.half_year
    band_lookback: int = Field(default=672, ge=2, le=10000)
    settings: LabSettings = Field(default_factory=LabSettings)

    @model_validator(mode="after")
    def pair_valid(self) -> Self:
        pair = PairRotationRequestDto(coin_a=self.coin_a, coin_b=self.coin_b)
        object.__setattr__(self, "coin_a", pair.coin_a)
        object.__setattr__(self, "coin_b", pair.coin_b)
        if self.anchor is not None and self.anchor != "none":
            venue, separator, code = self.anchor.partition(":")
            if venue != "binance" or not separator or not code:
                raise ValueError("Choose a Binance anchor listing.")
        if self.settings.method == "lead_lag" and self.bar != "1m":
            raise ValueError("Lead-lag proof requires one-minute bars.")
        return self


class LabCallDto(AnalysisModel):
    status: Literal[
        "insufficient_history",
        "identity_unresolved",
        "execution_data_missing",
        "cost_data_missing",
        "cost_budget_failed",
        "no_edge",
        "hold",
        "into_a",
        "into_b",
    ]
    headline: str
    reason: str
    target_weight_a: str | None
    rotation_fraction: str | None


class LabProofDto(AnalysisModel):
    passes: bool
    data_role: Literal["validation"]
    final_oos_used: bool
    validation_reused: bool
    settings_tried: int
    control: str | None
    raw_p_value: float | None
    corrected_p_value: float | None
    significance: float
    folds_passing: int
    folds_total: int
    minimum_passing_folds: int
    validation_trades: int
    minimum_trades: int
    vs_hodl_pct: float | None
    vs_control_pct: float | None
    cost_paid_pct: float | None
    gross_vs_hodl_pct: float | None
    cost_gate_passed: bool | None
    tuning_cost_pct: float | None
    tuning_gross_vs_hodl_pct: float | None
    tuning_start: datetime
    tuning_end: datetime
    proof_start: datetime
    proof_end: datetime
    correction: str
    limitations: list[str]


class LabWealthDto(AnalysisModel):
    time: list[int]
    value: dict[str, list[float]]
    coins_a: dict[str, list[float]]
    coins_b: dict[str, list[float]]
    terminal_values: dict[str, str]
    window_kind: Literal["validation", "context_only"]


class LabSignalDto(AnalysisModel):
    time: list[int]
    values: list[float | None]
    upper: float
    lower: float
    unit: str


class LabTradeDto(AnalysisModel):
    decision_index: int
    fill_index: int
    time: datetime
    direction: Literal["into_a", "into_b", "into_usdt", "into_anchor"]
    route: str
    fees_usdt: str
    slippage_usdt: str
    fills: list[dict[str, str]]


class LabStudyResultDto(AnalysisModel):
    schema_version: Literal["qap.lab.study.v1"]
    analysis: LabAnalysisDto
    requested_settings: LabSettings
    applied_settings: LabSettings
    call: LabCallDto
    proof: LabProofDto
    signal: LabSignalDto
    wealth: LabWealthDto | None
    trades: list[LabTradeDto]
    folds: list[dict[str, JsonValue]]
    statistics: dict[str, dict[str, JsonValue]]
    code_fingerprint: str
    execution_route: str
    execution_metadata: list[dict[str, str]]


class LabStudyDto(AnalysisModel):
    study_id: str
    created_at: datetime
    pinned: bool
    result: LabStudyResultDto


class LabSavedSummaryDto(AnalysisModel):
    study_id: str
    created_at: datetime
    pinned: bool
    coin_a: LabCoinDto
    coin_b: LabCoinDto
    method: str
    data_through: datetime
    headline: str


class LabSavedListDto(AnalysisModel):
    studies: list[LabSavedSummaryDto]
    next_offset: int | None


class LabPinDto(AnalysisModel):
    pinned: bool


class LabAdvisorSuggestionDto(AnalysisModel):
    rank: int
    preset_id: str
    title: str
    simple_reason: str
    pro_reason: str
    recommended_bar: str
    recommended_anchor: str | None
    settings: LabSettings


class LabAdvisorDto(AnalysisModel):
    regime_label: str
    simple_summary: str
    pro_summary: str
    bar_warning: str | None
    suggestions: list[LabAdvisorSuggestionDto]


class LabCompareRequestDto(AnalysisModel):
    coin_a: str
    coin_b: str
    anchor: str | None = None
    bar: Literal["1m", "15m", "1h", "4h", "1d"] = "15m"
    days: AnalysisDays = AnalysisDays.half_year
    band_lookback: int = Field(default=672, ge=2, le=10000)
    candidates: list[LabSettings] = Field(
        default_factory=list[LabSettings], max_length=8
    )

    @model_validator(mode="after")
    def pair_valid(self) -> Self:
        pair = PairRotationRequestDto(coin_a=self.coin_a, coin_b=self.coin_b)
        object.__setattr__(self, "coin_a", pair.coin_a)
        object.__setattr__(self, "coin_b", pair.coin_b)
        if self.anchor is not None and self.anchor != "none":
            venue, separator, code = self.anchor.partition(":")
            if venue != "binance" or not separator or not code:
                raise ValueError("Choose a Binance anchor listing.")
        for candidate in self.candidates:
            if candidate.method == "lead_lag" and self.bar != "1m":
                raise ValueError("Lead-lag proof requires one-minute bars.")
        return self


class LabCompareResultDto(AnalysisModel):
    advisor: LabAdvisorDto
    studies: list[LabStudyDto]
    best_study_id: str | None
