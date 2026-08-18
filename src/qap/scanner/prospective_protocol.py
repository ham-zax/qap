"""Typed semantic protocol for scanner prospective evidence and liquidity policy."""

import json
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256
from typing import cast

from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon


@dataclass(frozen=True, slots=True)
class ProspectiveProtocol:
    protocol_id: str = "scanner-v1-prospective-v1"
    checkpoint_policy_version: str = "scanner-v1-prospective-checkpoints-v2"
    microstructure_policy_version: str = "scanner-v1-public-microstructure-v1"
    liquidity_policy_version: str = "liquidity-policy-v1"
    capacity_policy_version: str = "scanner-v1-conservative-capacity-v1"
    qualification_policy_version: str = "scanner-v1-qualification-v1"
    adverse_cost_reference: str = SCANNER_V1_SLICE1.cost_policy.policy_id
    primary_control_reference: str = (
        f"{SCANNER_V1_SLICE1.primary_control.policy_id}:"
        f"{SCANNER_V1_SLICE1.primary_control.control_id}"
    )
    short_forward_window: timedelta = timedelta(hours=48)
    medium_forward_window: timedelta = timedelta(days=10)
    swing_forward_window: timedelta = timedelta(days=28)
    l1_cadence: timedelta = timedelta(seconds=60)
    depth_cadence: timedelta = timedelta(minutes=5)
    minimum_qualification_window: timedelta = timedelta(days=14)
    overall_coverage_minimum: Decimal = Decimal("0.95")
    daily_coverage_minimum: Decimal = Decimal("0.90")
    c95_quantile: Decimal = Decimal("0.95")
    safe_capacity_haircut: Decimal = Decimal("0.5")
    structural_rebalance_fraction: Decimal = Decimal("0.20")
    target_base_weights: tuple[Decimal, ...] = (
        Decimal("0.40"),
        Decimal("0.50"),
        Decimal("0.60"),
    )

    def forward_window(self, horizon: ScannerHorizon) -> timedelta:
        if horizon is ScannerHorizon.SHORT:
            return self.short_forward_window
        if horizon is ScannerHorizon.MEDIUM:
            return self.medium_forward_window
        if horizon is ScannerHorizon.SWING:
            return self.swing_forward_window
        raise ValueError(f"unsupported scanner horizon: {horizon}")


def _payload(protocol: ProspectiveProtocol) -> dict[str, object]:
    return {
        "protocol_id": protocol.protocol_id,
        "checkpoint_policy_version": protocol.checkpoint_policy_version,
        "microstructure_policy_version": protocol.microstructure_policy_version,
        "liquidity_policy_version": protocol.liquidity_policy_version,
        "capacity_policy_version": protocol.capacity_policy_version,
        "qualification_policy_version": protocol.qualification_policy_version,
        "adverse_cost_reference": protocol.adverse_cost_reference,
        "primary_control_reference": protocol.primary_control_reference,
        "forward_windows_seconds": {
            "short": int(protocol.short_forward_window.total_seconds()),
            "medium": int(protocol.medium_forward_window.total_seconds()),
            "swing": int(protocol.swing_forward_window.total_seconds()),
        },
        "capture": {
            "l1_cadence_seconds": int(protocol.l1_cadence.total_seconds()),
            "depth_cadence_seconds": int(protocol.depth_cadence.total_seconds()),
            "minimum_qualification_window_seconds": int(
                protocol.minimum_qualification_window.total_seconds()
            ),
            "overall_coverage_minimum": str(protocol.overall_coverage_minimum),
            "daily_coverage_minimum": str(protocol.daily_coverage_minimum),
        },
        "liquidity": {
            "c95_quantile": str(protocol.c95_quantile),
            "safe_capacity_haircut": str(protocol.safe_capacity_haircut),
            "structural_rebalance_fraction": str(
                protocol.structural_rebalance_fraction
            ),
            "target_base_weights": [
                str(value) for value in protocol.target_base_weights
            ],
        },
    }


def prospective_protocol_identity(protocol: ProspectiveProtocol) -> str:
    if not isinstance(cast(object, protocol), ProspectiveProtocol):
        raise TypeError("protocol must be a ProspectiveProtocol")
    encoded = json.dumps(
        _payload(protocol),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


PROSPECTIVE_V1 = ProspectiveProtocol()

L1_CADENCE = PROSPECTIVE_V1.l1_cadence
DEPTH_CADENCE = PROSPECTIVE_V1.depth_cadence
MINIMUM_QUALIFICATION_WINDOW = PROSPECTIVE_V1.minimum_qualification_window
OVERALL_COVERAGE_MINIMUM = PROSPECTIVE_V1.overall_coverage_minimum
DAILY_COVERAGE_MINIMUM = PROSPECTIVE_V1.daily_coverage_minimum
C95_QUANTILE = PROSPECTIVE_V1.c95_quantile
SAFE_CAPACITY_HAIRCUT = PROSPECTIVE_V1.safe_capacity_haircut
STRUCTURAL_REBALANCE_FRACTION = PROSPECTIVE_V1.structural_rebalance_fraction
TARGET_BASE_WEIGHTS = PROSPECTIVE_V1.target_base_weights
LIQUIDITY_POLICY_VERSION = PROSPECTIVE_V1.liquidity_policy_version

__all__ = [
    "C95_QUANTILE",
    "DAILY_COVERAGE_MINIMUM",
    "DEPTH_CADENCE",
    "L1_CADENCE",
    "LIQUIDITY_POLICY_VERSION",
    "MINIMUM_QUALIFICATION_WINDOW",
    "OVERALL_COVERAGE_MINIMUM",
    "PROSPECTIVE_V1",
    "ProspectiveProtocol",
    "SAFE_CAPACITY_HAIRCUT",
    "STRUCTURAL_REBALANCE_FRACTION",
    "TARGET_BASE_WEIGHTS",
    "prospective_protocol_identity",
]
