"""Frozen Scanner-V1 Slice-1 research protocol."""

import json
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import cast

from qap.market import BarInterval


UNIVERSE_POLICY_VERSION = "scanner-v1-pit-usdt-v1"
CANDIDATE_GENERATOR_VERSION = "scanner-v1-normalized-log-ssd-k8-v1"
TEMPLATE_SET_VERSION = "scanner-v1-mr-template-set-v1"
PROMOTION_POLICY_VERSION = "scanner-v1-promotion-v1"


class ScannerHorizon(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    SWING = "swing"


class TemplateId(StrEnum):
    FAST = "fast"
    BASE = "base"
    SLOW = "slow"


@dataclass(frozen=True, slots=True)
class HistoricalCostPolicy:
    policy_id: str
    fee_bps: Decimal
    slippage_bps: Decimal
    adverse_fee_bps: Decimal
    adverse_slippage_bps: Decimal


@dataclass(frozen=True, slots=True)
class PrimaryControlPolicy:
    policy_id: str
    control_id: str
    band_width: Decimal
    partial_correction_fraction: Decimal


@dataclass(frozen=True, slots=True)
class ResearchNormalization:
    policy_id: str
    total_direct_quote_value: Decimal
    minimum_rebalance_notional: Decimal
    base_step: Decimal | None


@dataclass(frozen=True, slots=True)
class HorizonProtocol:
    horizon: ScannerHorizon
    graph_interval: BarInterval
    graph_window: timedelta
    model_resolutions: tuple[BarInterval, ...]
    evaluation_window: timedelta
    template_windows: tuple[tuple[TemplateId, timedelta], ...]

    def template_window(self, template: TemplateId) -> timedelta:
        if not isinstance(cast(object, template), TemplateId):
            raise TypeError("template must be a TemplateId")
        for candidate, duration in self.template_windows:
            if candidate is template:
                return duration
        raise KeyError(template)

    def window_bars(self, template: TemplateId, resolution: BarInterval) -> int:
        if not isinstance(cast(object, resolution), BarInterval):
            raise TypeError("resolution must be a BarInterval")
        if resolution not in self.model_resolutions:
            raise ValueError("resolution is not admitted for this horizon")
        duration = self.template_window(template)
        if duration % resolution.duration != timedelta(0):
            raise ValueError(
                "template duration must divide exactly into resolution bars"
            )
        return duration // resolution.duration


@dataclass(frozen=True, slots=True)
class ScannerProtocol:
    protocol_id: str
    automatic_history: timedelta
    maximum_discovery_history: timedelta
    venues: tuple[str, ...]
    quote_asset: str
    candidate_generator_version: str
    universe_policy_version: str
    template_set_version: str
    promotion_policy_version: str
    neighbors_per_asset: int
    automatic_replay_cap_per_horizon: int
    max_promotions_per_asset_per_horizon: int
    max_promotions_per_pair_family_per_horizon: int
    minimum_asset_coverage: float
    minimum_pair_coverage: float
    maximum_missing_generator_bars: int
    neutral_threshold: float
    entry_threshold: float
    maximum_tilt: Decimal
    horizons: tuple[HorizonProtocol, ...]
    cost_policy: HistoricalCostPolicy
    primary_control: PrimaryControlPolicy
    normalization: ResearchNormalization

    def horizon(self, horizon: ScannerHorizon) -> HorizonProtocol:
        if not isinstance(cast(object, horizon), ScannerHorizon):
            raise TypeError("horizon must be a ScannerHorizon")
        for candidate in self.horizons:
            if candidate.horizon is horizon:
                return candidate
        raise KeyError(horizon)


def _duration_seconds(value: timedelta) -> int:
    seconds = value.total_seconds()
    if not seconds.is_integer():
        raise ValueError("scanner protocol durations must use whole seconds")
    return int(seconds)


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _protocol_payload(protocol: ScannerProtocol) -> dict[str, object]:
    return {
        "protocol_id": protocol.protocol_id,
        "automatic_history_seconds": _duration_seconds(protocol.automatic_history),
        "maximum_discovery_history_seconds": _duration_seconds(
            protocol.maximum_discovery_history
        ),
        "venues": list(protocol.venues),
        "quote_asset": protocol.quote_asset,
        "candidate_generator_version": protocol.candidate_generator_version,
        "universe_policy_version": protocol.universe_policy_version,
        "template_set_version": protocol.template_set_version,
        "promotion_policy_version": protocol.promotion_policy_version,
        "neighbors_per_asset": protocol.neighbors_per_asset,
        "automatic_replay_cap_per_horizon": (protocol.automatic_replay_cap_per_horizon),
        "max_promotions_per_asset_per_horizon": (
            protocol.max_promotions_per_asset_per_horizon
        ),
        "max_promotions_per_pair_family_per_horizon": (
            protocol.max_promotions_per_pair_family_per_horizon
        ),
        "minimum_asset_coverage": protocol.minimum_asset_coverage.hex(),
        "minimum_pair_coverage": protocol.minimum_pair_coverage.hex(),
        "maximum_missing_generator_bars": protocol.maximum_missing_generator_bars,
        "neutral_threshold": protocol.neutral_threshold.hex(),
        "entry_threshold": protocol.entry_threshold.hex(),
        "maximum_tilt": str(protocol.maximum_tilt),
        "horizons": [
            {
                "horizon": item.horizon.value,
                "graph_interval": item.graph_interval.label,
                "graph_window_seconds": _duration_seconds(item.graph_window),
                "model_resolutions": [
                    resolution.label for resolution in item.model_resolutions
                ],
                "evaluation_window_seconds": _duration_seconds(item.evaluation_window),
                "template_windows": [
                    [template.value, _duration_seconds(duration)]
                    for template, duration in item.template_windows
                ],
            }
            for item in protocol.horizons
        ],
        "cost_policy": {
            "policy_id": protocol.cost_policy.policy_id,
            "fee_bps": str(protocol.cost_policy.fee_bps),
            "slippage_bps": str(protocol.cost_policy.slippage_bps),
            "adverse_fee_bps": str(protocol.cost_policy.adverse_fee_bps),
            "adverse_slippage_bps": str(protocol.cost_policy.adverse_slippage_bps),
        },
        "primary_control": {
            "policy_id": protocol.primary_control.policy_id,
            "control_id": protocol.primary_control.control_id,
            "band_width": str(protocol.primary_control.band_width),
            "partial_correction_fraction": str(
                protocol.primary_control.partial_correction_fraction
            ),
        },
        "normalization": {
            "policy_id": protocol.normalization.policy_id,
            "total_direct_quote_value": str(
                protocol.normalization.total_direct_quote_value
            ),
            "minimum_rebalance_notional": str(
                protocol.normalization.minimum_rebalance_notional
            ),
            "base_step": _decimal(protocol.normalization.base_step),
        },
    }


def protocol_identity(protocol: ScannerProtocol) -> str:
    if not isinstance(cast(object, protocol), ScannerProtocol):
        raise TypeError("protocol must be a ScannerProtocol")
    encoded = json.dumps(
        _protocol_payload(protocol),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


SCANNER_V1_SLICE1 = ScannerProtocol(
    protocol_id="scanner-v1-s1",
    automatic_history=timedelta(days=365),
    maximum_discovery_history=timedelta(days=730),
    venues=("binance", "gate"),
    quote_asset="USDT",
    candidate_generator_version="normalized-log-price-ssd-v1",
    universe_policy_version="scanner-v1-pit-universe-v1",
    template_set_version="scanner-v1-pair-mr-templates-v1",
    promotion_policy_version="scanner-v1-promotion-v1",
    neighbors_per_asset=8,
    automatic_replay_cap_per_horizon=10,
    max_promotions_per_asset_per_horizon=2,
    max_promotions_per_pair_family_per_horizon=1,
    minimum_asset_coverage=0.95,
    minimum_pair_coverage=0.95,
    maximum_missing_generator_bars=2,
    neutral_threshold=0.5,
    entry_threshold=1.5,
    maximum_tilt=Decimal("0.10"),
    horizons=(
        HorizonProtocol(
            horizon=ScannerHorizon.SHORT,
            graph_interval=BarInterval("1h"),
            graph_window=timedelta(days=30),
            model_resolutions=(BarInterval("15m"), BarInterval("1h")),
            evaluation_window=timedelta(days=30),
            template_windows=(
                (TemplateId.FAST, timedelta(days=2)),
                (TemplateId.BASE, timedelta(days=7)),
                (TemplateId.SLOW, timedelta(days=14)),
            ),
        ),
        HorizonProtocol(
            horizon=ScannerHorizon.MEDIUM,
            graph_interval=BarInterval("4h"),
            graph_window=timedelta(days=90),
            model_resolutions=(BarInterval("1h"), BarInterval("4h")),
            evaluation_window=timedelta(days=90),
            template_windows=(
                (TemplateId.FAST, timedelta(days=14)),
                (TemplateId.BASE, timedelta(days=30)),
                (TemplateId.SLOW, timedelta(days=60)),
            ),
        ),
        HorizonProtocol(
            horizon=ScannerHorizon.SWING,
            graph_interval=BarInterval("1d"),
            graph_window=timedelta(days=180),
            model_resolutions=(BarInterval("4h"), BarInterval("1d")),
            evaluation_window=timedelta(days=180),
            template_windows=(
                (TemplateId.FAST, timedelta(days=30)),
                (TemplateId.BASE, timedelta(days=90)),
                (TemplateId.SLOW, timedelta(days=180)),
            ),
        ),
    ),
    cost_policy=HistoricalCostPolicy(
        policy_id="scanner-v1-historical-costs-v1",
        fee_bps=Decimal("10"),
        slippage_bps=Decimal("5"),
        adverse_fee_bps=Decimal("20"),
        adverse_slippage_bps=Decimal("10"),
    ),
    primary_control=PrimaryControlPolicy(
        policy_id="scanner-v1-band-control-v1",
        control_id="band-5pct-half",
        band_width=Decimal("0.05"),
        partial_correction_fraction=Decimal("0.5"),
    ),
    normalization=ResearchNormalization(
        policy_id="scanner-v1-unit-value-normalization-v1",
        total_direct_quote_value=Decimal("1"),
        minimum_rebalance_notional=Decimal("0"),
        base_step=None,
    ),
)


__all__ = [
    "HistoricalCostPolicy",
    "HorizonProtocol",
    "PrimaryControlPolicy",
    "ResearchNormalization",
    "SCANNER_V1_SLICE1",
    "ScannerHorizon",
    "ScannerProtocol",
    "TemplateId",
    "protocol_identity",
]
