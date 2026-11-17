"""Typed contract for forward Binance L2 paper-trading sessions."""

from datetime import datetime
from typing import Literal, Self

from pydantic import Field, model_validator

from qap.api.pair_rotation_analysis_schemas import AnalysisModel
from qap.api.pair_rotation_schemas import PairRotationRequestDto
from qap.policy.lab_settings import LabSettings

PaperBar = Literal["1m", "15m", "1h", "4h", "1d"]


class LivePaperCreateDto(AnalysisModel):
    coin_a: str
    coin_b: str
    anchor: str | None = None
    bar: PaperBar = "1h"
    settings: LabSettings = Field(default_factory=LabSettings)
    order_rtt_ms: float = Field(default=75.0, gt=0.0, le=5000.0)
    max_staleness_ms: float = Field(default=500.0, gt=0.0, le=10000.0)

    @model_validator(mode="after")
    def pair_valid(self) -> Self:
        pair = PairRotationRequestDto(coin_a=self.coin_a, coin_b=self.coin_b)
        object.__setattr__(self, "coin_a", pair.coin_a)
        object.__setattr__(self, "coin_b", pair.coin_b)
        if self.anchor == "none":
            object.__setattr__(self, "anchor", "none")
        elif self.anchor is not None:
            venue, separator, code = self.anchor.partition(":")
            if venue != "binance" or not separator or not code:
                raise ValueError("Choose a Binance anchor listing.")
        return self


class LivePaperStepDto(AnalysisModel):
    duration_seconds: float = Field(default=3.0, gt=0.0, le=30.0)


class LivePaperPortfolioDto(AnalysisModel):
    value_usdt: str
    return_pct: float
    holdings: dict[str, str]
    fees_usdt: str
    slippage_usdt: str
    rotations: int


class LivePaperPortfoliosDto(AnalysisModel):
    strategy: LivePaperPortfolioDto
    hodl: LivePaperPortfolioDto
    drift_control: LivePaperPortfolioDto


class LivePaperFillDto(AnalysisModel):
    fill_id: str
    market: str
    side: Literal["buy", "sell"]
    base_asset: str
    quote_asset: str
    base_quantity: str
    execution_price: str
    reference_price: str
    vwap_price: str
    gross_quote_notional: str
    fee: str
    fee_asset: str
    slippage_usdt: str
    levels_consumed: int


class LivePaperTradeDto(AnalysisModel):
    target_id: str | None = None
    step_index: int
    decision_time: datetime
    direction: Literal["into_a", "into_b", "into_usdt", "into_anchor"]
    status: Literal["complete", "partial"] = "complete"
    route: str
    fees_usdt: str
    slippage_usdt: str
    rejected_reasons: list[str]
    fills: list[LivePaperFillDto]


class LivePaperLatencyDto(AnalysisModel):
    """Declared delay vs actual supporting clocks per attempt."""

    step_index: int
    attempt_index: int = 1
    candle_time: int | None = None
    observation_type: str = "legacy_step"
    execution_status: str = "hold"
    legacy_clock: bool = False
    t_exch_us: int | None
    t_recv_ns: int
    t_decide_ns: int
    t_fill_leg1_ns: int
    t_fill_leg2_ns: int
    requested_fill_leg1_ns: int | None = None
    requested_fill_leg2_ns: int | None = None
    actual_fill_leg1_ns: int | None = None
    actual_fill_leg2_ns: int | None = None
    order_rtt_ms: float
    recv_to_decide_ms: float
    decide_to_fill_leg1_ms: float
    decide_to_fill_leg2_ms: float
    actual_decide_to_fill_leg1_ms: float | None = None
    actual_decide_to_fill_leg2_ms: float | None = None
    book_age_leg1_ms: float | None
    book_age_leg2_ms: float | None
    signal_preference: float | None
    action: Literal["swap", "rejected", "hold"]
    rejected_reasons: list[str]


class LivePaperPendingTargetDto(AnalysisModel):
    target_id: str
    status: str
    reason: str
    target_weights: dict[str, str]
    attempts: int
    fills_count: int


class LivePaperMetadataProvenanceDto(AnalysisModel):
    observed_at: str
    source_id: str
    payload_sha256: str


class LivePaperSessionDto(AnalysisModel):
    schema_version: str = "qap.lab.paper_session.v2"
    session_id: str
    actor_id: str
    status: Literal["active", "stopped"]
    can_step: bool = True
    step_block_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    stopped_at: datetime | None
    coin_a: str
    coin_b: str
    anchor: str | None
    anchor_mode: str = "auto"
    bar: PaperBar
    order_rtt_ms: float
    max_staleness_ms: float
    settings: LabSettings
    simple_status: str
    vs_hodl_pct: float
    vs_control_pct: float
    decisions_count: int
    book_observations_count: int = 0
    track_record_mode: str = "continuous_forward"
    candle_origin_time: int | None = None
    last_candle_time: int | None = None
    pending_target: LivePaperPendingTargetDto | None = None
    market_metadata_provenance: dict[str, LivePaperMetadataProvenanceDto] = Field(
        default_factory=dict
    )
    portfolios: LivePaperPortfoliosDto
    trades: list[LivePaperTradeDto]
    latency_audit: list[LivePaperLatencyDto]


class LivePaperSessionRowDto(AnalysisModel):
    schema_version: str = "qap.lab.paper_session.v2"
    session_id: str
    actor_id: str
    status: Literal["active", "stopped"]
    can_step: bool = True
    step_block_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    coin_a: str
    coin_b: str
    anchor: str | None
    bar: PaperBar
    decisions_count: int
    book_observations_count: int = 0
    track_record_mode: str = "continuous_forward"
    trades_count: int
    vs_hodl_pct: float
    vs_control_pct: float
    simple_status: str


class LivePaperSessionListDto(AnalysisModel):
    sessions: list[LivePaperSessionRowDto]
    next_offset: int | None
