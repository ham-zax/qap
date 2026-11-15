"""Small pyvinecopulib adapter with training-only empirical margins."""

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any, cast

import numpy as np
import pyvinecopulib as pv
from scipy import stats  # type: ignore[import-untyped]

from qap.relationship.pair_measurements import Floats


@dataclass(frozen=True, slots=True)
class CopulaFeatures:
    probability_a: Floats
    probability_b: Floats
    family: str
    lower_tail: float
    upper_tail: float
    training_observations: int


def copula_features(
    close_a: Floats, close_b: Floats, training: int
) -> CopulaFeatures | None:
    a, b = np.diff(np.log(close_a)), np.diff(np.log(close_b))
    if min(a.size, b.size) <= training or training < 60:
        return None
    if np.ptp(a[:training]) == 0 or np.ptp(b[:training]) == 0:
        return None
    library = cast(Any, pv)
    train = np.asfortranarray(
        np.column_stack(
            (
                cast(Any, stats).rankdata(a[:training]) / (training + 1),
                cast(Any, stats).rankdata(b[:training]) / (training + 1),
            )
        )
    )
    model = library.Bicop.from_data(
        train,
        controls=library.FitControlsBicop(
            family_set=[
                library.BicopFamily.indep,
                library.BicopFamily.gaussian,
                library.BicopFamily.student,
                library.BicopFamily.clayton,
                library.BicopFamily.gumbel,
            ],
            num_threads=1,
        ),
    )
    margins = np.column_stack(
        (
            (np.searchsorted(np.sort(a[:training]), a, side="right") + 0.5)
            / (training + 1),
            (np.searchsorted(np.sort(b[:training]), b, side="right") + 0.5)
            / (training + 1),
        )
    )
    margins = np.asfortranarray(np.clip(margins, 1e-6, 1 - 1e-6))
    probability_a = np.r_[np.nan, model.hfunc2(margins)]
    probability_b = np.r_[np.nan, model.hfunc1(margins)]
    probability_a[: training + 1] = np.nan
    probability_b[: training + 1] = np.nan
    lower = upper = 0.0
    parameters = np.asarray(model.parameters).ravel()
    family = str(model.family).split(".")[-1]
    if family == "student":
        rho, degrees = float(parameters[0]), float(parameters[1])
        if 1 + rho > 0:
            lower = upper = float(
                2
                * cast(Any, stats).t.cdf(
                    -sqrt((degrees + 1) * (1 - rho) / (1 + rho)), degrees + 1
                )
            )
    elif family == "clayton":
        theta = float(parameters[0])
        if theta != 0:
            lower = 2 ** (-1 / theta)
    elif family == "gumbel":
        theta = float(parameters[0])
        if theta != 0:
            upper = 2 - 2 ** (1 / theta)
    if int(model.rotation) == 180:
        lower, upper = upper, lower
    elif int(model.rotation) in (90, 270):
        lower = upper = 0.0
    if not all(isfinite(item) for item in (lower, upper)):
        return None
    return CopulaFeatures(probability_a, probability_b, family, lower, upper, training)
