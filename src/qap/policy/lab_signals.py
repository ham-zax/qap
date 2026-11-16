"""Pure causal Lab preferences, separate from all owned inventory and fills."""

from qap.policy.lab_settings import LabSettings
from qap.policy.lab_strategy_registry import STRATEGY_REGISTRY, LabSignal, StrategySpec
from qap.relationship.pair_measurements import Floats

__all__ = ["LabSignal", "STRATEGY_REGISTRY", "StrategySpec", "signal_path"]


def signal_path(
    a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None = None
) -> LabSignal:
    return STRATEGY_REGISTRY[settings.method].build(a, b, settings, anchor)
