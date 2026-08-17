"""Deterministic direct-spot execution contracts."""

from qap.execution.costs import CostModel
from qap.execution.direct import (
    DirectExecutionReason,
    DirectExecutionResult,
    execute_direct_rebalance_leg,
)
from qap.execution.fills import (
    ExecutionQuantization,
    Fill,
    FillSide,
    build_buy_fill,
    build_sell_fill,
)
from qap.execution.multi_asset import (
    MultiAssetOrderOutcome,
    MultiAssetPreflightError,
    MultiAssetRebalanceResult,
    RebalancePhase,
    execute_multi_asset_rebalance,
)
from qap.execution.precision import (
    MarketPrecision,
    MarketPrecisionError,
    MarketPrecisionReason,
)
from qap.execution.replay import (
    ReplayNoFillReason,
    ReplayPolicy,
    ReplayStep,
    ReplayTrace,
    run_deterministic_replay,
)
from qap.execution.routing import (
    ExecutionRoute,
    ExecutionRouteLeg,
    RoutedExecutionReason,
    RoutedExecutionResult,
    RoutePlanningError,
    RoutingReason,
    execute_routed_conversion,
    plan_execution_route,
)

__all__ = [
    "CostModel",
    "DirectExecutionReason",
    "DirectExecutionResult",
    "ExecutionQuantization",
    "Fill",
    "FillSide",
    "ExecutionRoute",
    "ExecutionRouteLeg",
    "MarketPrecision",
    "MarketPrecisionError",
    "MarketPrecisionReason",
    "MultiAssetOrderOutcome",
    "MultiAssetPreflightError",
    "MultiAssetRebalanceResult",
    "RebalancePhase",
    "ReplayNoFillReason",
    "RoutedExecutionReason",
    "RoutedExecutionResult",
    "RoutePlanningError",
    "RoutingReason",
    "ReplayPolicy",
    "ReplayStep",
    "ReplayTrace",
    "build_buy_fill",
    "build_sell_fill",
    "execute_direct_rebalance_leg",
    "execute_multi_asset_rebalance",
    "execute_routed_conversion",
    "plan_execution_route",
    "run_deterministic_replay",
]
