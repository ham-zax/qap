"""Frozen Scanner-V1 Slice-2 liquidity/capture constants from the approved design."""

from datetime import timedelta
from decimal import Decimal

SLICE2_DESIGN_SHA256 = (
    "0817427b8d4950136ea3b5c3bb5fd51f08753ba6449574bb38c8911d2a334ac4"
)
LIQUIDITY_POLICY_VERSION = "liquidity-policy-v1"
L1_CADENCE = timedelta(seconds=60)
DEPTH_CADENCE = timedelta(minutes=5)
MINIMUM_QUALIFICATION_WINDOW = timedelta(days=14)
OVERALL_COVERAGE_MINIMUM = Decimal("0.95")
DAILY_COVERAGE_MINIMUM = Decimal("0.90")
C95_QUANTILE = Decimal("0.95")
SAFE_CAPACITY_HAIRCUT = Decimal("0.5")
STRUCTURAL_REBALANCE_FRACTION = Decimal("0.20")
TARGET_BASE_WEIGHTS = (Decimal("0.40"), Decimal("0.50"), Decimal("0.60"))

__all__ = [
    "C95_QUANTILE",
    "DAILY_COVERAGE_MINIMUM",
    "DEPTH_CADENCE",
    "L1_CADENCE",
    "LIQUIDITY_POLICY_VERSION",
    "MINIMUM_QUALIFICATION_WINDOW",
    "OVERALL_COVERAGE_MINIMUM",
    "SAFE_CAPACITY_HAIRCUT",
    "SLICE2_DESIGN_SHA256",
    "STRUCTURAL_REBALANCE_FRACTION",
    "TARGET_BASE_WEIGHTS",
]
