"""Tests for the deterministic Smart Strategy Advisor."""

from typing import Any

from qap.policy.lab_settings import LabSettings
from qap.product_lab_advisor import advise_pair_strategies


def _analysis(
    *,
    bar: str = "1h",
    coint_passes: bool = False,
    hurst_state: str = "mixed",
    hurst_val: float = 0.5,
    half_life_bars: float | None = None,
    anchor_r2: float | None = 0.4,
) -> dict[str, Any]:
    return {
        "bar": bar,
        "coin_a": {"id": "binance:SOL", "code": "SOL"},
        "coin_b": {"id": "binance:ETH", "code": "ETH"},
        "anchor": "binance:BTC",
        "suggested_anchor": (
            None
            if anchor_r2 is None
            else {"coin": {"id": "binance:BTC"}, "joint_r_squared": anchor_r2}
        ),
        "measurements": {
            "cointegration": {
                "passes": coint_passes,
                "p_value": 0.012 if coint_passes else 0.42,
            },
            "half_life": {
                "reverting": half_life_bars is not None,
                "bars": half_life_bars,
            },
            "hurst": {"state": hurst_state, "value": hurst_val},
            "copula": {"family": "t", "lower_tail": 0.18, "upper_tail": 0.16},
        },
    }


def test_advisor_mean_reverting_regime() -> None:
    out = advise_pair_strategies(
        _analysis(
            coint_passes=True,
            hurst_state="reverting",
            hurst_val=0.38,
            half_life_bars=40.0,
        )
    )
    assert out["regime_label"] == "mean_reverting"
    assert out["bar_warning"] is None
    assert out["simple_summary"] and out["pro_summary"]
    assert len(out["suggestions"]) == 4
    assert [s["rank"] for s in out["suggestions"]] == [1, 2, 3, 4]
    assert out["suggestions"][0]["preset_id"] == "zscore_kalman"
    # Fixed fallback lookback (96) must not use ratio half-life (40 * 2 = 80).
    assert out["suggestions"][0]["settings"]["lookback"] == 96
    assert "ratio_half_life_bars=40.0" in out["pro_summary"]
    assert "return_copula=" in out["pro_summary"]
    for s in out["suggestions"]:
        assert "Conservative" not in s["title"]
        assert "above spot fees" not in s["simple_reason"]
        assert "above fees" not in s["simple_reason"]
        LabSettings.model_validate(s["settings"])


def test_advisor_trending_regime() -> None:
    out = advise_pair_strategies(
        _analysis(coint_passes=False, hurst_state="trending", hurst_val=0.63)
    )
    assert out["regime_label"] == "trending"
    assert out["suggestions"][0]["preset_id"] == "ratio_trend"
    for s in out["suggestions"]:
        LabSettings.model_validate(s["settings"])


def test_advisor_15m_noisy_emits_bar_warning() -> None:
    out = advise_pair_strategies(_analysis(bar="15m", hurst_state="mixed"))
    assert out["regime_label"] == "mixed_or_noisy"
    assert out["bar_warning"] is not None
    assert "15m" in out["bar_warning"]
    assert out["suggestions"][0]["recommended_bar"] == "4h"
    for s in out["suggestions"]:
        LabSettings.model_validate(s["settings"])


def test_advisor_handles_real_analysis_dict_anchor_and_anchor_ranking() -> None:
    from qap.api.lab_study_schemas import LabAdvisorDto

    real_shape: dict[str, Any] = {
        "bar": "4h",
        "coin_a": {"id": "binance:ETH", "code": "ETH"},
        "coin_b": {"id": "binance:BTC", "code": "BTC"},
        "anchor": {
            "id": "binance:SOL",
            "code": "SOL",
            "name": "Solana",
            "identity_state": "resolved",
        },
        "anchor_ranking": [
            {
                "anchor": {
                    "id": "binance:SOL",
                    "code": "SOL",
                    "name": "Solana",
                    "identity_state": "resolved",
                },
                "joint_explained": 0.62,
            }
        ],
        "measurements": {
            "cointegration": {"passes": False, "p_value": 0.35},
            "half_life": {"reverting": False, "bars": None},
            "hurst": {"reading": "trending", "exponent": 0.61},
            "copula": {"family": "student", "lower_tail": 0.52, "upper_tail": 0.52},
        },
    }
    dto = LabAdvisorDto.model_validate(advise_pair_strategies(real_shape))
    assert dto.regime_label == "trending"
    assert dto.suggestions[1].recommended_anchor == "binance:SOL"


def test_advisor_no_silent_anchor_fallback_for_btc_eth_or_explicit_none() -> None:
    btc_eth_no_anchor = _analysis(anchor_r2=None)
    btc_eth_no_anchor["coin_a"] = {"id": "binance:BTC", "code": "BTC"}
    btc_eth_no_anchor["coin_b"] = {"id": "binance:ETH", "code": "ETH"}
    btc_eth_no_anchor["anchor"] = None
    btc_eth_no_anchor["anchor_ranking"] = []
    out = advise_pair_strategies(btc_eth_no_anchor)
    copula = next(s for s in out["suggestions"] if s["preset_id"] == "spread_copula")
    assert copula["recommended_anchor"] is None
    assert copula["settings"]["crash_defense_mode"] == "park_usdt"
    assert "USDT" in copula["simple_reason"]

    explicit_none = _analysis(anchor_r2=0.6)
    explicit_none["anchor"] = None
    explicit_none["suggested_anchor"] = None
    explicit_none["anchor_ranking"] = [
        {"anchor": {"id": "binance:SOL", "code": "SOL"}, "joint_explained": 0.6}
    ]
    out_none = advise_pair_strategies(explicit_none)
    copula_none = next(
        s for s in out_none["suggestions"] if s["preset_id"] == "spread_copula"
    )
    assert copula_none["recommended_anchor"] is None
    assert copula_none["settings"]["crash_defense_mode"] == "park_usdt"
