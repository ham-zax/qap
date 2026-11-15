"""Finite, descriptive analysis contract. No strategy call or proof authority."""

from datetime import datetime
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AnalysisDays(IntEnum):
    month = 30
    quarter = 90
    half_year = 180
    year = 365


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class LabCoinDto(AnalysisModel):
    id: str
    code: str
    name: str
    identity_state: Literal["resolved", "review", "unresolved"]


class LabSeriesDto(AnalysisModel):
    time: list[int]
    close_a: list[float]
    close_b: list[float]
    ratio: list[float]
    mean: list[float | None]
    std: list[float | None]
    anchor_close: list[float] | None


class CorrelationDto(AnalysisModel):
    pearson: float
    spearman: float
    kendall: float
    observations: int


class CointegrationDto(AnalysisModel):
    statistic: float
    p_value: float
    level: float
    passes: bool


class HedgeRatioDto(AnalysisModel):
    ols: float
    tls: float
    first_half_ols: float
    second_half_ols: float
    stable: bool


class HalfLifeDto(AnalysisModel):
    bars: float | None
    reverting: bool


class HurstDto(AnalysisModel):
    exponent: float
    reading: Literal["reverting", "random", "trending"]


class RegimeDto(AnalysisModel):
    volatility: Literal["calm", "normal", "stressed"]
    volatility_percentile: float
    trend: Literal["trending", "ranging"]
    efficiency: float


class LeadLagDto(AnalysisModel):
    lag_bars: int
    correlation: float
    stable: bool


class AnchorLinkDto(AnalysisModel):
    beta: float
    r_squared: float
    lead_lag: LeadLagDto | None


class KalmanDto(AnalysisModel):
    beta: float
    standard_error: float
    beta_change: float


class GrangerDirectionDto(AnalysisModel):
    lag_bars: int
    p_value: float
    passes: bool


class GrangerDto(AnalysisModel):
    a_to_b: GrangerDirectionDto
    b_to_a: GrangerDirectionDto
    max_lag: int
    observations: int


class CopulaTailsDto(AnalysisModel):
    family: str
    lower_tail: float
    upper_tail: float
    observations: int


class RollingDependenceDto(AnalysisModel):
    window_bars: int
    latest: float
    low: float
    high: float


class LabMeasurementsDto(AnalysisModel):
    correlation: CorrelationDto | None
    cointegration: CointegrationDto | None
    hedge_ratio: HedgeRatioDto | None
    half_life: HalfLifeDto | None
    hurst: HurstDto | None
    ratio_percentile: float | None
    regime: RegimeDto | None
    anchor_a: AnchorLinkDto | None
    anchor_b: AnchorLinkDto | None
    kalman: KalmanDto | None
    granger: GrangerDto | None
    copula: CopulaTailsDto | None
    rolling_dependence: RollingDependenceDto | None


class AnchorFitDto(AnalysisModel):
    anchor: LabCoinDto
    beta_a: float
    beta_b: float
    joint_explained: float


class LabDatasetDto(AnalysisModel):
    dataset_id: str
    interval: str
    venue_symbol: str
    semantic_fingerprint: str
    coverage_start: datetime | None
    cutoff: datetime | None


class LabAnalysisDto(AnalysisModel):
    schema_version: Literal["qap.api.pair-rotation-analysis.v1"]
    coin_a: LabCoinDto
    coin_b: LabCoinDto
    bar: Literal["1m", "15m", "1h", "4h", "1d"]
    window_days: int
    band_lookback: int
    data_through: datetime
    bars_used: int
    identity_confirmed: bool
    series: LabSeriesDto
    anchor: LabCoinDto | None
    anchor_ranking: list[AnchorFitDto]
    measurements: LabMeasurementsDto
    datasets: list[LabDatasetDto]
