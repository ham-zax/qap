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
    hurst_map = (
        cast(Mapping[str, Any], hurst_info) if isinstance(hurst_info, Mapping) else None
    )
    hurst_state = (
        (hurst_map.get("reading") or hurst_map.get("state"))
        if hurst_map is not None
        else None
    )
    hurst_val = (
        (
            hurst_map.get("exponent")
            if "exponent" in hurst_map
            else hurst_map.get("value")
        )
        if hurst_map is not None
        else None
    )
    copula_info = m.get("copula")
    ranking = analysis.get("anchor_ranking")
    ranking_list = cast(list[object], ranking) if isinstance(ranking, list) else []
    top_ranked: Mapping[str, Any] | None = (
        cast(Mapping[str, Any], ranking_list[0])
        if ranking_list and isinstance(ranking_list[0], Mapping)
        else None
    )
    anchor_source: object = (
        suggested_anchor if suggested_anchor is not None else top_ranked
    )
    anchor_map = (
        cast(Mapping[str, Any], anchor_source)
        if isinstance(anchor_source, Mapping)
        else None
    )
    anchor_coin_raw = (
        (anchor_map.get("anchor") or anchor_map.get("coin"))
        if anchor_map is not None
        else None
    )
    anchor_coin = (
        cast(Mapping[str, Any], anchor_coin_raw)
        if isinstance(anchor_coin_raw, Mapping)
        else None
    )
    fallback_anchor = analysis.get("anchor")
    fallback_anchor_id = (
        str(cast(Mapping[str, Any], fallback_anchor)["id"])
        if isinstance(fallback_anchor, Mapping) and "id" in fallback_anchor
        else (str(fallback_anchor) if isinstance(fallback_anchor, str) else None)
    )
    explicit_no_anchor = (
        "anchor" in analysis and analysis["anchor"] is None and bool(ranking_list)
    )
    anchor_id: str | None = (
        None
        if explicit_no_anchor
        else str(anchor_coin["id"])
        if anchor_coin is not None and "id" in anchor_coin
        else fallback_anchor_id
    )
    anchor_r2 = (
        (
            anchor_map.get("joint_explained")
            if "joint_explained" in anchor_map
            else anchor_map.get("joint_r_squared")
        )
        if anchor_map is not None
        else None
    )

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
        "often exceed gross spread; 4h presets are recommended to cut fee drag."
        if bar == "15m"
        else None
    )
    rec_bar = "4h" if bar in ("1m", "15m", "1h") else bar
    rec_lookback = (
        int(min(500, max(60, round(2.0 * float(half_life_bars)))))
        if (half_life_bars is not None and isfinite(float(half_life_bars)))
        else 96
    )
    copula_anchor = (
        anchor_id if (anchor_r2 is not None and float(anchor_r2) >= 0.25) else None
    )
    copula_defense = "park_anchor" if copula_anchor is not None else "park_usdt"

    kalman_shielded = (
        "zscore_kalman",
        "Drawdown-Shielded Kalman Reversion",
        "Adapts to ratio drift and parks in USDT if drawdown exceeds 12%.",
        f"Kalman hedge lookback={rec_lookback}, entry=2.2, exit=0.4, min_hold=8, park_usdt@12%.",
        rec_bar,
        None,
        {
            "method": "zscore",
            "hedge_method": "kalman",
            "lookback": rec_lookback,
            "entry": 2.2,
            "exit": 0.4,
            "minimum_hold": 8,
            "cooldown": 6,
            "crash_defense_mode": "park_usdt",
            "regime_break_drawdown": 0.12,
        },
    )
    tail_copula = (
        "spread_copula",
        "4h Tail Copula + Benchmark Defense",
        "Waits for rare 2% tail divergences and parks in the benchmark on breaks.",
        f"4h tail copula lookback=96, p=0.02, exit_band=0.15, min_hold=12, {copula_defense}@15%.",
        rec_bar,
        copula_anchor,
        {
            "method": "copula",
            "lookback": 96,
            "copula_probability": 0.02,
            "copula_exit_band": 0.15,
            "minimum_hold": 12,
            "cooldown": 8,
            "crash_defense_mode": copula_defense,
            "regime_break_drawdown": 0.15,
        },
    )
    wide_ols = (
        "zscore_ols_wide",
        "Conservative Wide-Band OLS (2.5σ)",
        "Only enters on 2.5σ extremes to keep gross spread well above spot fees.",
        "OLS z-score lookback=120, entry=2.5, exit=0.3, min_hold=10, cooldown=8.",
        rec_bar,
        None,
        {
            "method": "zscore",
            "hedge_method": "ols",
            "lookback": 120,
            "entry": 2.5,
            "exit": 0.3,
            "minimum_hold": 10,
            "cooldown": 8,
            "crash_defense_mode": "coins_only",
        },
    )
    slow_trend = (
        "ratio_trend",
        "Slow Macro Ratio Trend (24/96)",
        "Rides sustained multi-day relative strength with a 0.5% deadband.",
        "Trend 24/96 crossover, deadband=0.005, min_hold=12, cooldown=8.",
        rec_bar,
        None,
        {
            "method": "trend",
            "fast_window": 24,
            "slow_window": 96,
            "trend_deadband": 0.005,
            "minimum_hold": 12,
            "cooldown": 8,
        },
    )

    if regime_label == "mean_reverting":
        ordered = [kalman_shielded, tail_copula, wide_ols, slow_trend]
    elif regime_label == "trending":
        ordered = [
            slow_trend,
            ("spread_copula_anchor", *tail_copula[1:4], rec_bar, anchor_id, {
                **tail_copula[6],
                "crash_defense_mode": "park_anchor" if anchor_id else "park_usdt",
            }),
            wide_ols,
            kalman_shielded,
        ]
    else:
        ordered = [tail_copula, kalman_shielded, wide_ols, slow_trend]

    suggestions = [
        _suggestion(rank, *spec) for rank, spec in enumerate(ordered, start=1)
    ]

    return {
        "regime_label": regime_label,
        "simple_summary": simple_summary,
        "pro_summary": pro_summary,
        "bar_warning": bar_warning,
        "suggestions": suggestions,
    }
