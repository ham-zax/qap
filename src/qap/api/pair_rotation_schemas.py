"""Typed backend discovery and data-open requests for the Pair Rotation Lab."""

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qap.product_coin_search import ResearchCoin


class PairRotationRequestDto(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)
    coin_a: str = Field(min_length=1, max_length=100)
    coin_b: str = Field(min_length=1, max_length=100)
    lookback_days: int = Field(default=365, ge=1, le=3650)
    base_interval: Literal["15m", "1m"] = "15m"
    include_execution: bool = False

    @model_validator(mode="after")
    def distinct_same_venue(self) -> Self:
        if self.base_interval == "15m" and self.lookback_days < 365:
            raise ValueError("15m preparation retains at least one year.")
        ids: list[str] = []
        for value in (self.coin_a, self.coin_b):
            venue, separator, code = value.partition(":")
            if not separator or not code.strip() or venue != "binance":
                raise ValueError("Choose Binance spot listings as binance:CODE.")
            ids.append(f"{venue}:{code.upper()}")
        if ids[0] == ids[1]:
            raise ValueError("Choose two distinct coins.")
        object.__setattr__(self, "coin_a", ids[0])
        object.__setattr__(self, "coin_b", ids[1])
        return self


class CoinSearchDto(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["qap.api.coin-search.v1"] = "qap.api.coin-search.v1"
    directory_status: Literal["not_refreshed", "observed"]
    registry_status: Literal["unavailable", "cached"]
    directory_observed_at: datetime | None
    registry_observed_at: datetime | None
    registry_attribution: str | None
    coins: tuple[ResearchCoin, ...]
