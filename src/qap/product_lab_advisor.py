"""Pure deterministic Smart Strategy Advisor for Simple and Pro Lab users."""

from collections.abc import Mapping
from math import isfinite
from typing import Any, cast

from qap.policy.lab_settings import LabSettings


def _suggestion(
    rank: int,
    preset_id: str,
    title: str,
    simple_reason: str,
    pro_reason: str,
    recommended_bar: str,
    recommended_anchor: str | None,
    settings_dict: dict[str, Any],
) -> dict[str, Any]:
    validated = LabSettings(**settings_dict).model_dump(mode="json")
    return {
        "rank": rank,
        "preset_id": preset_id,
        "title": title,
        "simple_reason": simple_reason,
        "pro_reason": pro_reason,
        "recommended_bar": recommended_bar,
        "recommended_anchor": recommended_anchor,
        "settings": validated,
    }


def advise_pair_strategies(analysis: Mapping[str, Any]) -> dict[str, Any]:
    m = analysis["measurements"]
    bar = str(analysis["bar"])
    suggested_anchor = analysis.get("suggested_anchor")
    coin_a = str(analysis["coin_a"]["code"])
    coin_b = str(analysis["coin_b"]["code"])

    coint = m.get("cointegration")
    coint_passes = bool(coint and coint["passes"])
    coint_p = coint["p_value"] if coint else None
    half_life_info = m.get("half_life")
    half_life_bars = (
        half_life_info["bars"]
        if (half_life_info and half_life_info["reverting"])
        else None
    )
    hurst_info = m.get("hurst")
    hurst_state = hurst_info["state"] if hurst_info else None
    hurst_val = hurst_info["value"] if hurst_info else None
    copula_info = m.get("copula")
    anchor_id = (
        suggested_anchor["coin"]["id"] if suggested_anchor else analysis.get("anchor")
    )
    anchor_r2 = suggested_anchor["joint_r_squared"] if suggested_anchor else None

    if coint_passes or hurst_state == "reverting":
        regime_label = "mean_reverting"
        simple_summary = (
            f"{coin_a} and {coin_b} tend to snap back together after short-term "
            "divergences, so mean-reversion rotation presets are favored."
        )
    elif hurst_state == "trending":
        regime_label = "trending"
        simple_summary = (
            f"{coin_a} and {coin_b} are currently drifting in sustained trends, "
            "so trend-following presets are favored over counter-trend swaps."
        )
    else:
        regime_label = "mixed_or_noisy"
        simple_summary = (
            f"{coin_a} and {coin_b} show mixed or noisy behavior right now; "
            "tail-only copula or wider thresholds help avoid over-trading."
        )

    if isinstance(copula_info, Mapping):
        cop = cast(Mapping[str, Any], copula_info)
        copula_desc = (
            f"{cop.get('family', 'none')} "
            f"(lower={cop.get('lower_tail')}, "
            f"upper={cop.get('upper_tail')})"
        )
    else:
        copula_desc = "unavailable"
    pro_summary = (
        f"Regime={regime_label}; coint_p={coint_p}; "
        f"half_life_bars={half_life_bars}; hurst={hurst_val}; "
        f"copula={copula_desc}; anchor_r2={anchor_r2}."
    )

    bar_warning = (
        "15m candles generate high swap counts where 20 bps round-trip fees "
        "often exceed gross spread; compare 1h or 4h as well."
        if bar == "15m"
        else None
    )
    rec_bar = "1h" if bar == "15m" else bar
    rec_lookback = (
        int(min(500, max(60, round(2.0 * float(half_life_bars)))))
        if (half_life_bars is not None and isfinite(float(half_life_bars)))
        else 96
    )
    copula_anchor = (
        anchor_id if (anchor_r2 is not None and float(anchor_r2) >= 0.25) else None
    )

    if regime_label == "mean_reverting":
        suggestions = [
            _suggestion(
                1,
                "zscore_kalman",
                "Kalman Z-Score Mean Reversion",
                "Adapts smoothly to gradual shifts in the pair ratio.",
                f"Kalman hedge with lookback={rec_lookback}, entry=2.0, exit=0.4.",
                rec_bar,
                None,
                {
                    "method": "zscore",
                    "hedge_method": "kalman",
                    "lookback": rec_lookback,
                    "entry": 2.0,
                    "exit": 0.4,
                },
            ),
            _suggestion(
                2,
                "spread_copula",
                "Spread Copula Tail Rotation",
                "Waits for rare tail divergences before rotating.",
                f"Rolling spread copula lookback={max(80, rec_lookback)}, p=0.05.",
                rec_bar,
                copula_anchor,
                {
                    "method": "copula",
                    "lookback": max(80, rec_lookback),
                    "copula_probability": 0.05,
                },
            ),
            _suggestion(
                3,
                "ratio_trend_guard",
                "Ratio Trend Falsifier",
                "Checks whether following momentum beats mean reversion.",
                "Trend 12/48 crossover falsifier.",
                rec_bar,
                None,
                {"method": "trend", "fast_window": 12, "slow_window": 48},
            ),
        ]
    elif regime_label == "trending":
        suggestions = [
            _suggestion(
                1,
                "ratio_trend",
                "Ratio Trend Following",
                "Rides sustained relative strength between the two coins.",
                "Trend 12/48 crossover aligned with Hurst > 0.5.",
                rec_bar,
                None,
                {"method": "trend", "fast_window": 12, "slow_window": 48},
            ),
            _suggestion(
                2,
                "spread_copula_anchor",
                "Anchor-Mediated Spread Copula",
                "Uses a shared market anchor to filter noisy swings.",
                "Rolling spread copula lookback=96, p=0.05 with anchor.",
                rec_bar,
                anchor_id,
                {"method": "copula", "lookback": 96, "copula_probability": 0.05},
            ),
            _suggestion(
                3,
                "zscore_ols_wide",
                "Wide OLS Z-Score",
                "Only fades extreme moves to avoid fighting the trend.",
                "OLS z-score lookback=120, entry=2.5, exit=0.5.",
                rec_bar,
                None,
                {
                    "method": "zscore",
                    "hedge_method": "ols",
                    "lookback": 120,
                    "entry": 2.5,
                    "exit": 0.5,
                },
            ),
        ]
    else:
        suggestions = [
            _suggestion(
                1,
                "spread_copula",
                "Spread Copula Tail Filter",
                "Targets only extreme tail dislocations in noisy markets.",
                "Rolling spread copula lookback=96, p=0.05.",
                rec_bar,
                anchor_id,
                {"method": "copula", "lookback": 96, "copula_probability": 0.05},
            ),
            _suggestion(
                2,
                "zscore_ols",
                "OLS Z-Score",
                "Uses a slightly higher entry bar to cut down churn.",
                "OLS z-score lookback=96, entry=2.2, exit=0.4.",
                rec_bar,
                None,
                {
                    "method": "zscore",
                    "hedge_method": "ols",
                    "lookback": 96,
                    "entry": 2.2,
                    "exit": 0.4,
                },
            ),
            _suggestion(
                3,
                "ratio_trend",
                "Slow Ratio Trend",
                "Tests whether slower trend shifts capture cleaner moves.",
                "Trend 16/64 crossover.",
                rec_bar,
                None,
                {"method": "trend", "fast_window": 16, "slow_window": 64},
            ),
        ]

    return {
        "regime_label": regime_label,
        "simple_summary": simple_summary,
        "pro_summary": pro_summary,
        "bar_warning": bar_warning,
        "suggestions": suggestions,
    }
