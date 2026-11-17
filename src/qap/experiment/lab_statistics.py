"""Statistical resolution preflight and stationary-bootstrap SPA calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from math import isfinite
from typing import Any, cast

import numpy as np
from arch.bootstrap import SPA
from numpy.typing import NDArray

DEFAULT_SPA_REPLICATES = 9_999
DEFAULT_SPA_SEED = 20260930
PROOF_PROTOCOL_VERSION = "qap.lab.proof.v2"
LEGACY_PROOF_PROTOCOL_VERSION = "qap.lab.proof.v1"

type Floats = NDArray[np.float64]


class FamilyResolutionError(ValueError):
    """Declared study family lacks resolution for the first Holm threshold."""


@dataclass(frozen=True, slots=True)
class FamilyResolutionCheck:
    """Numerical resolution capacity check for a declared hypothesis family."""

    outer_family_size: int
    pair_trial_count: int
    replicates: int
    alpha: float
    raw_p_floor: float
    min_attainable_corrected_p: float
    holm_first_threshold: float
    required_replicates: int
    resolvable: bool


def spa_block_size(return_count: int) -> int:
    """Deterministic stationary-bootstrap block length from sample size."""
    return max(2, int(np.sqrt(return_count)))


def check_family_resolution(
    *,
    outer_family_size: int,
    pair_trial_count: int,
    replicates: int = DEFAULT_SPA_REPLICATES,
    alpha: float = 0.05,
) -> FamilyResolutionCheck:
    """Verify that finite bootstrap replicates can reach the first Holm threshold."""
    if outer_family_size < 1:
        raise ValueError("outer_family_size must be at least 1")
    if pair_trial_count < 1:
        raise ValueError("pair_trial_count must be at least 1")
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be strictly between 0 and 1")

    raw_p_floor = 1.0 / (replicates + 1)
    min_attainable_corrected_p = min(1.0, raw_p_floor * pair_trial_count)
    holm_first_threshold = alpha / outer_family_size
    required_replicates = max(
        1, math.ceil((pair_trial_count * outer_family_size) / alpha) - 1
    )
    resolvable = (raw_p_floor * pair_trial_count) <= holm_first_threshold + 1e-15
    return FamilyResolutionCheck(
        outer_family_size=outer_family_size,
        pair_trial_count=pair_trial_count,
        replicates=replicates,
        alpha=alpha,
        raw_p_floor=raw_p_floor,
        min_attainable_corrected_p=min_attainable_corrected_p,
        holm_first_threshold=holm_first_threshold,
        required_replicates=required_replicates,
        resolvable=resolvable,
    )


def require_family_resolution(
    *,
    pair_label: str,
    outer_family_size: int,
    pair_trial_count: int,
    replicates: int = DEFAULT_SPA_REPLICATES,
    alpha: float = 0.05,
) -> FamilyResolutionCheck:
    """Raise FamilyResolutionError when the declared family cannot be resolved."""
    result = check_family_resolution(
        outer_family_size=outer_family_size,
        pair_trial_count=pair_trial_count,
        replicates=replicates,
        alpha=alpha,
    )
    if not result.resolvable:
        raise FamilyResolutionError(
            f"Declared family preflight failed for {pair_label}: "
            f"outer_family_size={result.outer_family_size}, "
            f"pair_trial_count={result.pair_trial_count}, "
            f"replicates={result.replicates}, "
            f"alpha={result.alpha}, "
            f"min_attainable_corrected_p={result.min_attainable_corrected_p:.6g}, "
            f"holm_first_threshold={result.holm_first_threshold:.6g}; "
            f"requires at least {result.required_replicates} replicates or a "
            "smaller declared family/configuration count."
        )
    return result


def corrected_spa(
    strategy: Floats,
    control: Floats,
    trials: int,
    *,
    replicates: int = DEFAULT_SPA_REPLICATES,
    seed: int = DEFAULT_SPA_SEED,
) -> tuple[float, float]:
    """Stationary block bootstrap SPA, then conservative across-family correction."""
    if replicates < 1:
        raise ValueError("replicates must be at least 1")
    if strategy.size < 20 or strategy.shape != control.shape:
        return 1.0, 1.0
    advantage = strategy - control
    if not np.isfinite(advantage).all() or float(np.mean(advantage)) <= 0:
        return 1.0, 1.0
    if float(np.std(advantage)) < 1e-15:
        raw = 0.0
    else:
        test = SPA(
            -control,
            -strategy[:, None],
            block_size=spa_block_size(strategy.size),
            reps=replicates,
            seed=seed,
        )
        test.compute()
        raw = float(cast(Any, test.pvalues)["consistent"])
    # A finite bootstrap cannot establish p=0; derive floor from replicate count.
    floor = 1.0 / (replicates + 1)
    raw = max(floor, raw) if isfinite(raw) else 1.0
    return raw, min(1.0, raw * max(1, trials))


__all__ = [
    "DEFAULT_SPA_REPLICATES",
    "DEFAULT_SPA_SEED",
    "FamilyResolutionCheck",
    "FamilyResolutionError",
    "LEGACY_PROOF_PROTOCOL_VERSION",
    "PROOF_PROTOCOL_VERSION",
    "check_family_resolution",
    "corrected_spa",
    "require_family_resolution",
    "spa_block_size",
]
