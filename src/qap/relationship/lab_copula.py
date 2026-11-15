"""Small pyvinecopulib adapter with training-only empirical margins."""

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any, cast

import numpy as np
import pyvinecopulib as pv
from scipy import stats  # type: ignore[import-untyped]

from qap.relationship.pair_measurements import Floats, rolling_mean_std


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


def _fit_and_eval_bicop(
    sa_train: Floats,
    sb_train: Floats,
    sa_eval: Floats,
    sb_eval: Floats,
) -> Floats:
    library = cast(Any, pv)
    scipy_stats = cast(Any, stats)
    n = sa_train.size
    train = np.asfortranarray(
        np.column_stack(
            (
                scipy_stats.rankdata(sa_train) / (n + 1),
                scipy_stats.rankdata(sb_train) / (n + 1),
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
    margins_eval = np.column_stack(
        (
            (np.searchsorted(np.sort(sa_train), sa_eval, side="right") + 0.5) / (n + 1),
            (np.searchsorted(np.sort(sb_train), sb_eval, side="right") + 0.5) / (n + 1),
        )
    )
    margins_eval = np.asfortranarray(np.clip(margins_eval, 1e-6, 1 - 1e-6))
    return cast(Floats, np.asarray(model.hfunc2(margins_eval), dtype=np.float64))


def rolling_spread_copula(
    close_a: Floats,
    close_b: Floats,
    *,
    window: int,
    anchor: Floats | None = None,
    refit_step: int | None = None,
) -> Floats | None:
    """Causal, scale-invariant rolling copula over stationary spreads."""
    if (
        close_a.shape != close_b.shape
        or window < 60
        or close_a.size <= window
        or (anchor is not None and anchor.shape != close_a.shape)
    ):
        return None
    step = max(16, window // 4) if refit_step is None else max(1, refit_step)
    da: Floats = cast(Floats, np.log(close_a) - np.log(close_a[0]))
    db: Floats = cast(Floats, np.log(close_b) - np.log(close_b[0]))
    prob_a = np.full(close_a.size, np.nan)

    if anchor is None:
        short_w = max(15, window // 2)
        ma_a, _ = rolling_mean_std(da, short_w)
        ma_b, _ = rolling_mean_std(db, short_w)
        dev_a = da - ma_a
        dev_b = db - ma_b
        for tau in range(window, close_a.size, step):
            formation = slice(tau - window, tau)
            evaluation = slice(tau, min(close_a.size, tau + step))
            raw_a, raw_b = dev_a[formation], dev_b[formation]
            mask = np.isfinite(raw_a) & np.isfinite(raw_b)
            if int(np.count_nonzero(mask)) < 40:
                continue
            sa_train, sb_train = raw_a[mask], raw_b[mask]
            if np.ptp(sa_train) <= 1e-12 or np.ptp(sb_train) <= 1e-12:
                continue
            sa_eval, sb_eval = dev_a[evaluation], dev_b[evaluation]
            eval_mask = np.isfinite(sa_eval) & np.isfinite(sb_eval)
            if not eval_mask.any():
                continue
            block = np.full(sa_eval.size, np.nan)
            block[eval_mask] = _fit_and_eval_bicop(
                sa_train, sb_train, sa_eval[eval_mask], sb_eval[eval_mask]
            )
            prob_a[evaluation] = block
    else:
        dc: Floats = cast(Floats, np.log(anchor) - np.log(anchor[0]))
        for tau in range(window, close_a.size, step):
            formation = slice(tau - window, tau)
            evaluation = slice(tau, min(close_a.size, tau + step))
            dc_train, da_train, db_train = dc[formation], da[formation], db[formation]
            mask = np.isfinite(dc_train) & np.isfinite(da_train) & np.isfinite(db_train)
            if int(np.count_nonzero(mask)) < 40:
                continue
            dc_f, da_f, db_f = dc_train[mask], da_train[mask], db_train[mask]
            var_c = float(np.var(dc_f))
            if var_c <= 1e-18:
                continue
            mean_c = float(np.mean(dc_f))
            beta_a = float(np.cov(da_f, dc_f, ddof=0)[0, 1] / var_c)
            alpha_a = float(np.mean(da_f)) - beta_a * mean_c
            beta_b = float(np.cov(db_f, dc_f, ddof=0)[0, 1] / var_c)
            alpha_b = float(np.mean(db_f)) - beta_b * mean_c
            sa_train = da_f - (alpha_a + beta_a * dc_f)
            sb_train = db_f - (alpha_b + beta_b * dc_f)
            if np.ptp(sa_train) <= 1e-12 or np.ptp(sb_train) <= 1e-12:
                continue
            sa_eval = da[evaluation] - (alpha_a + beta_a * dc[evaluation])
            sb_eval = db[evaluation] - (alpha_b + beta_b * dc[evaluation])
            eval_mask = np.isfinite(sa_eval) & np.isfinite(sb_eval)
            if not eval_mask.any():
                continue
            block = np.full(sa_eval.size, np.nan)
            block[eval_mask] = _fit_and_eval_bicop(
                sa_train, sb_train, sa_eval[eval_mask], sb_eval[eval_mask]
            )
            prob_a[evaluation] = block

    if not np.isfinite(prob_a).any():
        return None
    return prob_a
