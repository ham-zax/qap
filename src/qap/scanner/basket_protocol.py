"""Typed Scanner-V1 basket and asset-momentum protocol."""

import json
from dataclasses import dataclass, replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256
from typing import cast

from qap.market import BarInterval
from qap.product_current_approved_policy import CURRENT_APPROVED_SCANNER_PROTOCOL
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity


@dataclass(frozen=True, slots=True)
class MomentumRule:
    horizon: ScannerHorizon
    resolution: BarInterval
    formation: timedelta


@dataclass(frozen=True, slots=True)
class BasketProtocol:
    protocol_id: str = "scanner-v1-basket-v1"
    source_pair_protocol_id: str = SCANNER_V1_SLICE1.protocol_id
    source_pair_protocol_identity: str = protocol_identity(SCANNER_V1_SLICE1)
    venues: tuple[str, ...] = SCANNER_V1_SLICE1.venues
    execution_bridge: str = "USDT"
    minimum_economic_assets: int = 3
    maximum_economic_assets: int = 6
    neutral_allocation_rule: str = "equal-weight-economic-assets-v1"
    maximum_asset_tilt: Decimal = Decimal("0.10")
    basket_construction_rule: str = "manual-only"
    one_venue_per_basket: bool = True
    one_horizon_per_basket: bool = True
    one_decision_resolution_per_basket: bool = True
    maximum_selected_candidates_per_unordered_pair: int = 1
    pair_edge_weight_rule: str = "equal"
    cross_horizon_combination_allowed: bool = False
    cross_venue_combination_allowed: bool = False
    mechanical_control_reference: str = (
        f"{SCANNER_V1_SLICE1.primary_control.policy_id}:"
        f"{SCANNER_V1_SLICE1.primary_control.control_id}"
    )
    pair_blind_control_reference: str = "scanner-v1-pair-blind-relative-momentum-v1"
    cost_policy_reference: str = SCANNER_V1_SLICE1.cost_policy.policy_id
    momentum_rules: tuple[MomentumRule, ...] = (
        MomentumRule(ScannerHorizon.SHORT, BarInterval("1h"), timedelta(days=2)),
        MomentumRule(ScannerHorizon.MEDIUM, BarInterval("4h"), timedelta(days=10)),
        MomentumRule(ScannerHorizon.SWING, BarInterval("1d"), timedelta(days=28)),
    )

    def momentum_rule(self, horizon: ScannerHorizon) -> MomentumRule:
        if not isinstance(cast(object, horizon), ScannerHorizon):
            raise TypeError("horizon must be a ScannerHorizon")
        for rule in self.momentum_rules:
            if rule.horizon is horizon:
                return rule
        raise KeyError(horizon)

    def allowed_basket_resolutions(
        self,
        horizon: ScannerHorizon,
    ) -> tuple[BarInterval, ...]:
        return SCANNER_V1_SLICE1.horizon(horizon).model_resolutions


def basket_protocol_identity(protocol: BasketProtocol) -> str:
    if not isinstance(cast(object, protocol), BasketProtocol):
        raise TypeError("protocol must be a BasketProtocol")
    payload = {
        "protocol_id": protocol.protocol_id,
        "source_pair_protocol_id": protocol.source_pair_protocol_id,
        "source_pair_protocol_identity": protocol.source_pair_protocol_identity,
        "venues": list(protocol.venues),
        "execution_bridge": protocol.execution_bridge,
        "minimum_economic_assets": protocol.minimum_economic_assets,
        "maximum_economic_assets": protocol.maximum_economic_assets,
        "neutral_allocation_rule": protocol.neutral_allocation_rule,
        "maximum_asset_tilt": str(protocol.maximum_asset_tilt),
        "basket_construction_rule": protocol.basket_construction_rule,
        "one_venue_per_basket": protocol.one_venue_per_basket,
        "one_horizon_per_basket": protocol.one_horizon_per_basket,
        "one_decision_resolution_per_basket": (
            protocol.one_decision_resolution_per_basket
        ),
        "maximum_selected_candidates_per_unordered_pair": (
            protocol.maximum_selected_candidates_per_unordered_pair
        ),
        "pair_edge_weight_rule": protocol.pair_edge_weight_rule,
        "cross_horizon_combination_allowed": (
            protocol.cross_horizon_combination_allowed
        ),
        "cross_venue_combination_allowed": protocol.cross_venue_combination_allowed,
        "mechanical_control_reference": protocol.mechanical_control_reference,
        "pair_blind_control_reference": protocol.pair_blind_control_reference,
        "cost_policy_reference": protocol.cost_policy_reference,
        "momentum_rules": [
            {
                "horizon": rule.horizon.value,
                "resolution": rule.resolution.label,
                "formation_seconds": int(rule.formation.total_seconds()),
            }
            for rule in protocol.momentum_rules
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


SCANNER_V1_BASKET = BasketProtocol()
PRODUCT_CURRENT_APPROVED_BASKET = replace(
    SCANNER_V1_BASKET,
    protocol_id="product-current-approved-basket-v1",
    source_pair_protocol_id=CURRENT_APPROVED_SCANNER_PROTOCOL.protocol_id,
    source_pair_protocol_identity=protocol_identity(CURRENT_APPROVED_SCANNER_PROTOCOL),
)


def basket_protocol(protocol_id: str) -> BasketProtocol:
    normalized = protocol_id.strip()
    for protocol in (SCANNER_V1_BASKET, PRODUCT_CURRENT_APPROVED_BASKET):
        if protocol.protocol_id == normalized:
            return protocol
    raise ValueError("unsupported basket protocol ID")


__all__ = [
    "BasketProtocol",
    "MomentumRule",
    "PRODUCT_CURRENT_APPROVED_BASKET",
    "SCANNER_V1_BASKET",
    "basket_protocol",
    "basket_protocol_identity",
]
