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
            object.__setattr__(self, "anchor", None)
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
    step_index: int
    decision_time: datetime
    direction: Literal["into_a", "into_b", "into_usdt"]
    route: str
    fees_usdt: str
    slippage_usdt: str
    rejected_reasons: list[str]
    fills: list[LivePaperFillDto]


class LivePaperLatencyDto(AnalysisModel):
    """Four clocks per decision: exchange (us), receive/decide/fill (ns)."""

    step_index: int
    t_exch_us: int | None
    t_recv_ns: int
    t_decide_ns: int
    t_fill_leg1_ns: int
    t_fill_leg2_ns: int
    order_rtt_ms: float
    recv_to_decide_ms: float
    decide_to_fill_leg1_ms: float
    decide_to_fill_leg2_ms: float
    book_age_leg1_ms: float | None
    book_age_leg2_ms: float | None
    signal_preference: float | None
    action: Literal["swap", "rejected", "hold"]
    rejected_reasons: list[str]


class LivePaperSessionDto(AnalysisModel):
    session_id: str
    actor_id: str
    status: Literal["active", "stopped"]
    created_at: datetime
    updated_at: datetime
    stopped_at: datetime | None
    coin_a: str
    coin_b: str
    anchor: str | None
    bar: PaperBar
    order_rtt_ms: float
    max_staleness_ms: float
    settings: LabSettings
    simple_status: str
    vs_hodl_pct: float
    vs_control_pct: float
    decisions_count: int
    portfolios: LivePaperPortfoliosDto
    trades: list[LivePaperTradeDto]
    latency_audit: list[LivePaperLatencyDto]


class LivePaperSessionRowDto(AnalysisModel):
    session_id: str
    actor_id: str
    status: Literal["active", "stopped"]
    created_at: datetime
    updated_at: datetime
    coin_a: str
    coin_b: str
    anchor: str | None
    bar: PaperBar
    decisions_count: int
    trades_count: int
    vs_hodl_pct: float
    vs_control_pct: float
    simple_status: str


class LivePaperSessionListDto(AnalysisModel):
    sessions: list[LivePaperSessionRowDto]
    next_offset: int | None
