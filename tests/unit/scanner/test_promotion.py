from qap.scanner.promotion import (
    PromotionStatus,
    apply_promotion_policy,
)
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus


def _record(
    candidate_id: str,
    *,
    pair_id: str,
    proxy: float,
    turnover: float = 0.1,
    model_family: str = "residual_mean_reversion",
    orientation: str | None = None,
    automatic: bool = True,
    manual_pinned: bool = False,
    status: ScoutTrialStatus = ScoutTrialStatus.VALID,
) -> ScoutTrialRecord:
    asset_a, asset_b = pair_id.split("/")
    return ScoutTrialRecord(
        candidate_id=candidate_id,
        scan_id="a" * 64,
        venue="binance",
        horizon="short",
        pair_id=pair_id,
        orientation=orientation or f"{asset_a}/{asset_b}",
        resolution="1h",
        model_family=model_family,
        template_id="fast",
        trial_status=status,
        failure_reason=None if status is ScoutTrialStatus.VALID else "invalid",
        scout_relative_wealth_proxy=proxy if status is ScoutTrialStatus.VALID else None,
        scout_turnover_proxy=turnover,
        signal_count=1 if status is ScoutTrialStatus.VALID else 0,
        automatic_neighbor_selected=automatic,
        manual_pinned=manual_pinned,
    )


def test_pair_family_cap_keeps_only_higher_ranked_residual_orientation() -> None:
    records = (
        _record("1" * 64, pair_id="BTC/ETH", proxy=0.04, orientation="BTC/ETH"),
        _record("2" * 64, pair_id="BTC/ETH", proxy=0.03, orientation="ETH/BTC"),
    )

    decisions = apply_promotion_policy(records)

    first = next(item for item in decisions if item.candidate_id == "1" * 64)
    second = next(item for item in decisions if item.candidate_id == "2" * 64)
    assert first.promotion_status is PromotionStatus.AUTOMATIC_PROMOTED
    assert first.automatic_selected is True
    assert second.promotion_status is PromotionStatus.AUTOMATIC_EXCLUDED
    assert second.budget_reason == "pair_family_cap"


def test_per_asset_cap_excludes_third_high_ranked_pair_involving_asset() -> None:
    records = (
        _record("1" * 64, pair_id="A/B", proxy=0.06),
        _record("2" * 64, pair_id="A/C", proxy=0.05),
        _record("3" * 64, pair_id="A/D", proxy=0.04),
    )

    decisions = apply_promotion_policy(records)

    assert sum(item.automatic_selected for item in decisions) == 2
    third = next(item for item in decisions if item.candidate_id == "3" * 64)
    assert third.promotion_status is PromotionStatus.AUTOMATIC_EXCLUDED
    assert third.budget_reason == "asset_cap"


def test_automatic_replay_cap_is_ten_without_filler_trials() -> None:
    records = tuple(
        _record(
            f"{index:064x}",
            pair_id=f"A{index:02d}/B{index:02d}",
            proxy=1.0 - index * 0.01,
        )
        for index in range(12)
    )

    decisions = apply_promotion_policy(records)

    assert sum(item.automatic_selected for item in decisions) == 10
    excluded = [
        item
        for item in decisions
        if item.promotion_status is PromotionStatus.AUTOMATIC_EXCLUDED
    ]
    assert len(excluded) == 2
    assert {item.budget_reason for item in excluded} == {"automatic_replay_cap"}


def test_negative_valid_candidate_is_still_promoted() -> None:
    decisions = apply_promotion_policy(
        (
            _record("1" * 64, pair_id="BTC/ETH", proxy=-0.01),
            _record("2" * 64, pair_id="SOL/XRP", proxy=-0.02),
        )
    )

    promoted = [item for item in decisions if item.automatic_selected]
    assert len(promoted) == 2
    assert promoted[0].candidate_id == "1" * 64
    assert promoted[0].promotion_rank == 1


def test_ranking_uses_proxy_then_turnover_then_canonical_identity() -> None:
    records = (
        _record("3" * 64, pair_id="SOL/XRP", proxy=0.1, turnover=0.2),
        _record("2" * 64, pair_id="BTC/ETH", proxy=0.1, turnover=0.1),
        _record("1" * 64, pair_id="ADA/DOT", proxy=0.1, turnover=0.1),
    )

    decisions = apply_promotion_policy(records)
    ranked = sorted(
        (item for item in decisions if item.promotion_rank is not None),
        key=lambda item: item.promotion_rank or 0,
    )

    assert [item.candidate_id for item in ranked] == ["1" * 64, "2" * 64, "3" * 64]


def test_manual_replays_are_outside_automatic_budget_without_duplicate_candidate() -> (
    None
):
    automatic = tuple(
        _record(
            f"{index + 1:064x}",
            pair_id=f"A{index:02d}/B{index:02d}",
            proxy=1.0 - index * 0.01,
        )
        for index in range(11)
    )
    manual_only = _record(
        "f" * 64,
        pair_id="MAN/UAL",
        proxy=-0.5,
        automatic=False,
        manual_pinned=True,
    )
    overlap_id = automatic[0].candidate_id

    decisions = apply_promotion_policy(
        (*automatic, manual_only),
        manual_candidate_ids=(manual_only.candidate_id, overlap_id),
    )

    assert sum(item.automatic_selected for item in decisions) == 10
    assert sum(item.manual_selected for item in decisions) == 2
    assert sum(item.selected_for_replay for item in decisions) == 11
    assert len({item.candidate_id for item in decisions}) == len(decisions)
    overlap = next(item for item in decisions if item.candidate_id == overlap_id)
    assert overlap.automatic_selected is True
    assert overlap.manual_selected is True
    manual = next(
        item for item in decisions if item.candidate_id == manual_only.candidate_id
    )
    assert manual.promotion_status is PromotionStatus.MANUAL_PROMOTED
    assert manual.promotion_rank is None


def test_invalid_trial_is_not_automatic_but_can_be_explicitly_manual() -> None:
    invalid = _record(
        "9" * 64,
        pair_id="BTC/ETH",
        proxy=0.0,
        status=ScoutTrialStatus.INVALID,
    )

    automatic_only = apply_promotion_policy((invalid,))
    manual = apply_promotion_policy(
        (invalid,), manual_candidate_ids=(invalid.candidate_id,)
    )

    assert automatic_only == ()
    assert len(manual) == 1
    assert manual[0].manual_selected is True
    assert manual[0].automatic_selected is False
