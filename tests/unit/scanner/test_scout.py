from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from qap.market import BarInterval
from qap.portfolio import AllocationTarget, AssetId, PairOrientation, PortfolioState
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, TemplateId
from qap.scanner.scout import ScoutTrialStatus, run_scout_trial, scout_target_weights
from qap.scanner.trials import ScannerModelFamily, ScannerTrial, preference_score

BTC = AssetId("BTC")
ETH = AssetId("ETH")
START = datetime(2026, 1, 1, tzinfo=UTC)
ORIENTATION = PairOrientation(base=ETH, quote=BTC)


def _trial() -> ScannerTrial:
    return ScannerTrial(
        candidate_id="c" * 64,
        scan_id="a" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        pair_id="BTC/ETH",
        asset_a=BTC,
        asset_b=ETH,
        orientation=ORIENTATION,
        resolution=BarInterval("1h"),
        model_family=ScannerModelFamily.RESIDUAL_MEAN_REVERSION,
        template_id=TemplateId.FAST,
        window_bars=48,
        minimum_observations=46,
        source_artifact_fingerprints=("b" * 64, "e" * 64),
        selection_slice_fingerprints=("1" * 64, "2" * 64),
        evidence_dataset_ids=("btc-1h", "eth-1h"),
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )


def _times(count: int) -> tuple[datetime, ...]:
    return tuple(START + position * timedelta(hours=1) for position in range(count))


def test_scout_state_mapping_matches_evidence_tilt_policy_semantics() -> None:
    from qap.policy.evidence_tilt import EvidenceTiltPolicy, NeutralBandMode

    neutral = AllocationTarget.for_basket(
        {BTC: Decimal("0.5"), ETH: Decimal("0.5")}, basket={BTC, ETH}
    )
    policy = EvidenceTiltPolicy(
        policy_id="scout-parity",
        orientation=ORIENTATION,
        neutral_target=neutral,
        neutral_threshold=0.5,
        enter_threshold=1.5,
        maximum_tilt=Decimal("0.10"),
        neutral_mode=NeutralBandMode.NEUTRAL_TARGET,
    )
    state = PortfolioState.from_holdings({BTC: Decimal("1"), ETH: Decimal("1")})

    for z_score in (0.0, 0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0):
        scout = scout_target_weights(z_score)
        decision = policy.decide(
            as_of=START,
            current_state=state,
            score=preference_score(z_score),
            evidence_id=f"z-{z_score}",
        )
        if scout is None:
            assert decision.no_action is True
        else:
            assert decision.target is not None
            assert scout == pytest.approx(
                (
                    float(decision.target.weights[ORIENTATION.base]),
                    float(decision.target.weights[ORIENTATION.quote]),
                )
            )


def test_scout_signal_acts_only_on_next_observation() -> None:
    record = run_scout_trial(
        _trial(),
        timestamps=_times(3),
        z_scores=(-2.0, 1.0, 1.0),
        prices_by_asset={
            ETH: (1.0, 2.0, 2.0),
            BTC: (1.0, 1.0, 1.0),
        },
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=2),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )

    assert record.trial_status is ScoutTrialStatus.VALID
    assert record.signal_count == 1
    # The 60/40 target is applied only after ETH has already doubled. With flat
    # prices thereafter, the only relative effect is the declared friction proxy.
    assert record.scout_relative_wealth_proxy is not None
    assert record.scout_relative_wealth_proxy < 0.0


def test_no_action_preserves_quantities_and_weight_drift_between_targets() -> None:
    record = run_scout_trial(
        _trial(),
        timestamps=_times(4),
        z_scores=(-2.0, 1.0, 0.0, 1.0),
        prices_by_asset={
            ETH: (1.0, 1.0, 2.0, 2.0),
            BTC: (1.0, 1.0, 1.0, 1.0),
        },
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=3),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )

    assert record.trial_status is ScoutTrialStatus.VALID
    # First rebalance is 50/50 -> 60/40, turnover 0.1. NO_ACTION then preserves
    # quantities while ETH doubles, drifting weights to 75/25. The later neutral
    # rebalance therefore adds 0.25 one-way turnover. Total = 0.35.
    assert record.scout_turnover_proxy == pytest.approx(0.35)


def test_scout_subtracts_one_way_friction_once_per_rebalance() -> None:
    record = run_scout_trial(
        _trial(),
        timestamps=_times(3),
        z_scores=(-2.0, 1.0, 1.0),
        prices_by_asset={ETH: (1.0, 1.0, 1.0), BTC: (1.0, 1.0, 1.0)},
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=2),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )

    assert record.trial_status is ScoutTrialStatus.VALID
    assert record.scout_turnover_proxy == pytest.approx(0.1)
    assert record.scout_relative_wealth_proxy == pytest.approx(-0.00015)


def test_finite_negative_proxy_is_valid_but_no_active_signal_is_invalid() -> None:
    negative = run_scout_trial(
        _trial(),
        timestamps=_times(3),
        z_scores=(-2.0, 1.0, 1.0),
        prices_by_asset={ETH: (1.0, 1.0, 1.0), BTC: (1.0, 1.0, 1.0)},
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=2),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )
    no_signal = run_scout_trial(
        _trial(),
        timestamps=_times(3),
        z_scores=(0.0, 1.0, 0.0),
        prices_by_asset={ETH: (1.0, 1.0, 1.0), BTC: (1.0, 1.0, 1.0)},
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=2),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )

    assert negative.trial_status is ScoutTrialStatus.VALID
    assert negative.scout_relative_wealth_proxy is not None
    assert negative.scout_relative_wealth_proxy < 0.0
    assert no_signal.trial_status is ScoutTrialStatus.INVALID
    assert no_signal.failure_reason == "no_active_signal"
    assert no_signal.scout_relative_wealth_proxy is None


def test_scout_rejects_non_finite_evidence_as_unrankable() -> None:
    record = run_scout_trial(
        _trial(),
        timestamps=_times(3),
        z_scores=(-2.0, float("nan"), 1.0),
        prices_by_asset={ETH: (1.0, 1.0, 1.0), BTC: (1.0, 1.0, 1.0)},
        evaluation_start=START,
        evaluation_end=START + timedelta(hours=2),
        cost_policy=SCANNER_V1_SLICE1.cost_policy,
    )

    assert record.trial_status is ScoutTrialStatus.INVALID
    assert record.failure_reason == "non_finite_evidence"
    assert record.scout_relative_wealth_proxy is None
