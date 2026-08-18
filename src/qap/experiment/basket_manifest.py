"""Frozen Scanner-V1 basket manifest rules shared by experiment composition."""

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal

from qap.experiment.control_specs import (
    BandPartialControlSpec,
    ControlSpec,
    PairBlindRelativeMomentumControlSpec,
)
from qap.market import BarInterval

BASKET_MAXIMUM_TILT = Decimal("0.10")
_TEMPLATE_DAYS = {
    "short": {"fast": 2, "base": 7, "slow": 14},
    "medium": {"fast": 14, "base": 30, "slow": 60},
    "swing": {"fast": 30, "base": 90, "slow": 180},
}
_MOMENTUM_DAYS = {"short": 2, "medium": 10, "swing": 28}
_ALLOWED_INTERVALS = {
    "short": frozenset(("15m", "1h")),
    "medium": frozenset(("1h", "4h")),
    "swing": frozenset(("4h", "1d")),
}
_MINIMUM_PAIR_COVERAGE = 0.95


def basket_horizon(policy_config: Mapping[str, object], interval: str) -> str:
    horizon = policy_config.get("horizon")
    if not isinstance(horizon, str) or horizon not in _TEMPLATE_DAYS:
        raise ValueError("basket_graph horizon is invalid")
    if interval not in _ALLOWED_INTERVALS[horizon]:
        raise ValueError("basket_graph interval is not admitted for horizon")
    return horizon


def basket_edge_rule(
    policy_config: Mapping[str, object],
    interval: str,
    template_id: str,
) -> tuple[int, int]:
    horizon = basket_horizon(policy_config, interval)
    try:
        formation_days = _TEMPLATE_DAYS[horizon][template_id]
    except KeyError as exc:
        raise ValueError("basket edge template_id is invalid") from exc
    formation_seconds = formation_days * 24 * 60 * 60
    interval_seconds = int(BarInterval(interval).duration.total_seconds())
    if formation_seconds % interval_seconds != 0:
        raise ValueError("basket edge formation is not integral in decision bars")
    window_bars = formation_seconds // interval_seconds
    minimum_observations = max(
        3,
        math.ceil(window_bars * _MINIMUM_PAIR_COVERAGE),
    )
    return window_bars, minimum_observations


def pair_blind_window_returns(
    policy_config: Mapping[str, object],
    interval: str,
) -> int:
    horizon = basket_horizon(policy_config, interval)
    formation_seconds = _MOMENTUM_DAYS[horizon] * 24 * 60 * 60
    interval_seconds = int(BarInterval(interval).duration.total_seconds())
    if formation_seconds % interval_seconds != 0:
        raise ValueError("basket momentum formation is not integral in decision bars")
    return formation_seconds // interval_seconds


def validate_basket_manifest_contract(
    *,
    policy_component_id: str,
    policy_config: Mapping[str, object],
    interval: str,
    relationship_component_id: str,
    relationship_config: Mapping[str, object],
    execution_mode: str,
    data_role: str,
    has_adverse_cost: bool,
    relationship_alpha_claim: bool,
    primary_incremental_benchmark: str | None,
    controls: Sequence[ControlSpec],
) -> None:
    pair_blind_controls = tuple(
        control
        for control in controls
        if isinstance(control, PairBlindRelativeMomentumControlSpec)
    )
    if policy_component_id != "basket_graph":
        if pair_blind_controls:
            raise ValueError("pair-blind momentum control requires basket_graph")
        return
    basket_horizon(policy_config, interval)
    if data_role != "development":
        raise ValueError("basket_graph requires development data_role")
    if relationship_component_id != "none" or relationship_config:
        raise ValueError("basket_graph requires relationship 'none'")
    if execution_mode != "multi_asset_bridge":
        raise ValueError("basket_graph requires multi_asset_bridge execution")
    if not has_adverse_cost:
        raise ValueError("basket_graph requires an adverse cost scenario")
    if not relationship_alpha_claim:
        raise ValueError("basket_graph requires relationship_alpha_claim")

    band_controls = tuple(
        control
        for control in controls
        if isinstance(control, BandPartialControlSpec)
        and control.control_id == "band-5pct-half"
    )
    if len(band_controls) != 1 or (
        band_controls[0].band_width != Decimal("0.05")
        or band_controls[0].partial_correction_fraction != Decimal("0.5")
    ):
        raise ValueError("basket_graph requires the frozen band-5pct-half control")

    if len(pair_blind_controls) != 1:
        raise ValueError(
            "basket_graph requires exactly one pair-blind momentum control"
        )
    if primary_incremental_benchmark != pair_blind_controls[0].control_id:
        raise ValueError("basket_graph primary benchmark must be pair-blind momentum")


__all__ = [
    "BASKET_MAXIMUM_TILT",
    "basket_edge_rule",
    "basket_horizon",
    "pair_blind_window_returns",
    "validate_basket_manifest_contract",
]
