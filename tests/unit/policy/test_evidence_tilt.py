from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qap.policy import DecisionReason
from qap.portfolio import AllocationTarget, AssetId, PairOrientation, PortfolioState

D = Decimal
BTC = AssetId("BTC")
ETH = AssetId("ETH")
SOL = AssetId("SOL")
USDT = AssetId("USDT")
ORIENTATION = PairOrientation(base=ETH, quote=BTC)
AS_OF = datetime(2024, 1, 1, 12, tzinfo=UTC)
STATE = PortfolioState.from_holdings({BTC: D("1"), ETH: D("1")})
NEUTRAL = AllocationTarget.for_basket(
    {BTC: D("0.5"), ETH: D("0.5")},
    basket={BTC, ETH},
)
CROSS_SECTIONAL_NEUTRAL = AllocationTarget.for_basket(
    {BTC: D("0.4"), ETH: D("0.3"), SOL: D("0.3")},
    basket={BTC, ETH, SOL},
)


def _policy(*, neutral_mode: str = "neutral_target"):
    from qap.policy.evidence_tilt import EvidenceTiltPolicy, NeutralBandMode

    return EvidenceTiltPolicy(
        policy_id="rolling-z-tilt-v1",
        orientation=ORIENTATION,
        neutral_target=NEUTRAL,
        neutral_threshold=0.25,
        enter_threshold=1.0,
        maximum_tilt=D("0.2"),
        neutral_mode=NeutralBandMode(neutral_mode),
    )


def test_positive_and_negative_scores_tilt_symmetrically_between_pair_legs() -> None:
    positive = _policy().decide(
        as_of=AS_OF,
        current_state=STATE,
        score=1.25,
        evidence_id="evidence-positive",
    )
    negative = _policy().decide(
        as_of=AS_OF,
        current_state=STATE,
        score=-1.25,
        evidence_id="evidence-negative",
    )

    assert positive.reason is DecisionReason.EVIDENCE_TARGET
    assert positive.target is not None
    assert dict(positive.target.weights) == {BTC: D("0.3"), ETH: D("0.7")}
    assert positive.evidence_ids == ("evidence-positive",)
    assert negative.target is not None
    assert dict(negative.target.weights) == {BTC: D("0.7"), ETH: D("0.3")}
    assert negative.evidence_ids == ("evidence-negative",)


def test_neutral_band_can_emit_the_declared_neutral_target() -> None:
    decision = _policy().decide(
        as_of=AS_OF,
        current_state=STATE,
        score=0.1,
        evidence_id="evidence-neutral",
    )

    assert decision.reason is DecisionReason.EVIDENCE_TARGET
    assert decision.target == NEUTRAL


def test_neutral_band_can_be_declared_as_no_action() -> None:
    decision = _policy(neutral_mode="no_action").decide(
        as_of=AS_OF,
        current_state=STATE,
        score=0.1,
        evidence_id="evidence-neutral",
    )

    assert decision.no_action is True
    assert decision.reason is DecisionReason.BELOW_THRESHOLD


def test_score_between_neutral_and_enter_thresholds_is_no_action() -> None:
    decision = _policy().decide(
        as_of=AS_OF,
        current_state=STATE,
        score=0.5,
        evidence_id="evidence-hysteresis",
    )

    assert decision.no_action is True
    assert decision.reason is DecisionReason.BELOW_THRESHOLD


def test_missing_or_non_finite_score_is_not_fabricated_into_a_target() -> None:
    missing = _policy().decide(
        as_of=AS_OF,
        current_state=STATE,
        score=None,
        evidence_id="evidence-missing",
    )
    assert missing.no_action is True
    assert missing.reason is DecisionReason.INSUFFICIENT_EVIDENCE

    with pytest.raises(ValueError, match="score must be finite"):
        _policy().decide(
            as_of=AS_OF,
            current_state=STATE,
            score=float("nan"),
            evidence_id="evidence-invalid",
        )


def test_policy_rejects_threshold_or_tilt_configuration_that_breaks_bounds() -> None:
    from qap.policy.evidence_tilt import EvidenceTiltPolicy, NeutralBandMode

    with pytest.raises(ValueError, match="neutral_threshold"):
        EvidenceTiltPolicy(
            policy_id="bad-thresholds",
            orientation=ORIENTATION,
            neutral_target=NEUTRAL,
            neutral_threshold=1.1,
            enter_threshold=1.0,
            maximum_tilt=D("0.2"),
            neutral_mode=NeutralBandMode.NEUTRAL_TARGET,
        )
    with pytest.raises(ValueError, match="maximum_tilt"):
        EvidenceTiltPolicy(
            policy_id="bad-tilt",
            orientation=ORIENTATION,
            neutral_target=NEUTRAL,
            neutral_threshold=0.25,
            enter_threshold=1.0,
            maximum_tilt=D("0.6"),
            neutral_mode=NeutralBandMode.NEUTRAL_TARGET,
        )


def test_cross_sectional_policy_transfers_weight_from_lowest_to_highest_score() -> None:
    from qap.policy.evidence_tilt import CrossSectionalTiltPolicy

    policy = CrossSectionalTiltPolicy(
        policy_id="common-mode-tilt-v1",
        neutral_target=CROSS_SECTIONAL_NEUTRAL,
        maximum_tilt=D("0.1"),
    )
    decision = policy.decide(
        as_of=AS_OF,
        current_state=STATE,
        scores={BTC: 0.2, ETH: -0.15, SOL: -0.05},
        evidence_id="cross-sectional-evidence",
    )

    assert decision.reason is DecisionReason.EVIDENCE_TARGET
    assert decision.target is not None
    assert dict(decision.target.weights) == {
        BTC: D("0.5"),
        ETH: D("0.2"),
        SOL: D("0.3"),
    }


def test_cross_sectional_policy_no_actions_without_score_dispersion() -> None:
    from qap.policy.evidence_tilt import CrossSectionalTiltPolicy

    policy = CrossSectionalTiltPolicy(
        policy_id="common-mode-tilt-v1",
        neutral_target=CROSS_SECTIONAL_NEUTRAL,
        maximum_tilt=D("0.1"),
    )
    decision = policy.decide(
        as_of=AS_OF,
        current_state=STATE,
        scores={BTC: 0.0, ETH: 0.0, SOL: 0.0},
        evidence_id="cross-sectional-flat",
    )

    assert decision.no_action is True
    assert decision.reason is DecisionReason.BELOW_THRESHOLD
