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
    assert len(out["suggestions"]) == 3
    assert [s["rank"] for s in out["suggestions"]] == [1, 2, 3]
    assert out["suggestions"][0]["preset_id"] == "zscore_kalman"
    for s in out["suggestions"]:
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
    assert out["suggestions"][0]["recommended_bar"] == "1h"
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
